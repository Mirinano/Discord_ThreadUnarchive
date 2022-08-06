#!python3.9
import os
import json
import pymysql
from typing import (
    Optional,
    Union
)

from enums import (
    InteractionType,
    InteractionResponseType,
    MessageFlags
)
import commands

if not __debug__:
    from dotenv import load_dotenv
    load_dotenv('.env')

# init
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
APPLICATION_PUBLIC_KEY = os.getenv('APPLICATION_PUBLIC_KEY')

RDS_HOST = os.getenv('RDS_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def connect_db():
    try:
        conn = pymysql.connect(host=RDS_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, connect_timeout=5)
        return conn
    except pymysql.MySQLError as e:
        print("ERROR: Unexpected error: Could not connect to MySQL instance.")
        print(e)
        return None


def insert_thread(cursor, thread: dict):
    sql = """INSERT INTO thread (
        id,
        channel,
        thread_name,
        locked,
        archive,
        archive_timestamp,
        auto_archive_duration,
        invitable,
        create_timestamp
    ) VALUES (
        '{id}',
        '{channel}',
        '{thread_name}',
        {locked},
        {archive},
        '{archive_timestamp}',
        {auto_archive_duration},
        {invitable},
        '{create_timestamp}'
    ) ON DUPLICATE KEY UPDATE
        channel='{channel}',
        thread_name='{thread_name}',
        locked={locked},
        archive={archive},
        archive_timestamp='{archive_timestamp}',
        auto_archive_duration={auto_archive_duration},
        invitable={invitable},
        create_timestamp='{create_timestamp}'
    ;"""
    query = {
        "id" : thread['id'],
        "channel" : thread['parent_id'],
        "thread_name" : thread['name'],
        "locked" : "b'1'" if thread["thread_metadata"]['locked'] else "b'0'",
        "archive" : "b'1'" if thread["thread_metadata"]['archived'] else "b'0'",
        "archive_timestamp" : convert_timestamp(thread["thread_metadata"]['archive_timestamp']),
        "auto_archive_duration" : thread["thread_metadata"]['auto_archive_duration'],
        "invitable" : "b'1'" if thread["thread_metadata"].get('invitable') else "b'0'",
        "create_timestamp" : convert_timestamp(thread["thread_metadata"].get('create_timestamp', "2000-01-01T00:00:00.000000+00:00")),
    }
    sql_content = sql.format(**query)
    # print(sql_content)
    cursor.execute(sql_content)

def insert_unarchive(cursor, _id: str, enable: bool):
    sql = """INSERT INTO unarchive (
        id,
        available
    ) VALUES (
        '{id}',
        {available}
    ) ON DUPLICATE KEY UPDATE
        available={available}
    ;"""
    query = {
        "id" : _id,
        "available" : "b'1'" if enable else "b'0'",
    }
    sql_content = sql.format(**query)
    # print(sql_content)
    cursor.execute(sql_content)

def select_unarchive(conn, _id: str) -> bool:
    sql = "SELECT available FROM  unarchive WHERE id = %s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (str(_id), ))

        results = cursor.fetchall()
        b = b'\x01'
        for r in results:
            bit = r[0]
            return bit == b
    
    return False

def convert_timestamp(text: str) -> str:
    return text.split('.')[0].replace('T', ' ')

def verify(signature: str, timestamp: str, body: str) -> bool:
    from nacl.signing import VerifyKey
    verify_key = VerifyKey(bytes.fromhex(APPLICATION_PUBLIC_KEY))
    try:
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
    except Exception as e:
        print(f"failed to verify request: {e}")
        return False

    return True

def callback(event: dict, context: dict):
    """AWS Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # print("event:")
    # print(event)

    headers: dict = { k.lower(): v for k, v in event['headers'].items() }
    # print("headers:")
    # print(headers)

    # path: str = p if (p := event.get("rawPath")) is not None else event.get("path")
    
    """Discord Interations"""
    rawBody: str  = event['body']
    # print("rawBody:")
    # print(rawBody)

    # validate request
    signature = headers.get('x-signature-ed25519')
    timestamp = headers.get('x-signature-timestamp')
    if not verify(signature, timestamp, rawBody):
        print("not verfy.")
        return {
            "cookies": [],
            "isBase64Encoded": False,
            "statusCode": 401,
            "headers": {},
            "body": ""
        }
    # print("verfy!!")

    req: dict = json.loads(rawBody)

    if not __debug__:
        print(json.dumps(req, ensure_ascii=False, indent=4))


    interact_type = InteractionType(req['type'])
    # ping pong
    if interact_type == InteractionType.ping:
        return {
            "type" : InteractionResponseType.pong.value
        }
    elif interact_type == InteractionType.application_command:
        data: dict = req['data']
        if data['id'] == commands.unarchive: #/unarchive
            # unarchive

            # connect database
            conn = connect_db()
            if conn is None:
                # connection error
                return {
                    "type" : InteractionResponseType.channel_message.value,
                    "data" : {
                        "content" : "```console\nERROR: Unexpected error: Could not connect to MySQL instance.\n```",
                        "flags" : MessageFlags.ephemeral.value,
                    }
                }

            options: list[dict] = data['options']
            thread_id: str = get_options(options, name="thread")[0]["value"]
            enable: bool = get_options(options, name="enable")[0]["value"]
            thread = data['resolved']['channels'][thread_id]

            with conn.cursor() as cur:
                insert_thread(cur, thread)
                insert_unarchive(cur, thread_id, enable)
            conn.commit()

            return {
                "type" : InteractionResponseType.channel_message.value,
                "data" : {
                    "content" : "スレッドの自動アンアーカイブ設定を更新しました。\n対象: {thread}\nステータス: {status}".format(
                        thread = f"{thread['name']} ( <#{thread_id}> )",
                        status = "有効化" if enable else "無効化"
                    )
                }
            }
        elif data['id'] == commands.status: #/status
            # check status
            # connect database
            conn = connect_db()
            if conn is None:
                # connection error
                return {
                    "type" : InteractionResponseType.channel_message.value,
                    "data" : {
                        "content" : "```console\nERROR: Unexpected error: Could not connect to MySQL instance.\n```",
                        "flags" : MessageFlags.ephemeral.value,
                    }
                }

            options: list[dict] = data['options']
            thread_id: str = get_options(options, name="thread")[0]["value"]
            thread = data['resolved']['channels'][thread_id]

            enable: bool = select_unarchive(conn, thread_id)

            return {
                "type" : InteractionResponseType.channel_message.value,
                "data" : {
                    "content" : "{thread}の自動アンアーカイブは、 {status} です。".format(
                        thread = f"{thread['name']} ( <#{thread_id}> )",
                        status = "有効" if enable else "無効"
                    )
                }
            }
                
    return {
        "type" : InteractionResponseType.channel_message.value,
        "data" : {
            "content" : "This is a test command or the behavior of the command is undefined.",
            "flags" : MessageFlags.ephemeral.value,
        }
    }



def get_options(
    options: list[dict],
    *,
    name:  Optional[str] = None,
    type:  Optional[int] = None,
    value: Optional[Union[str, int, bool, float]] = None
) -> list[dict]:
    match: list[dict] = list()
    for opt in options:
        if (type is not None) and (opt.get('type') != type):
            continue
        if (name is not None) and (opt.get('name') != name):
            continue
        if (value is not None) and (opt.get('value') != value):
            continue
        match.append(opt)
    return match



if __name__ == '__main__':
    print("start")