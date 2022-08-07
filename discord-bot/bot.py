#!python3.9
import os
import asyncio
import pymysql
from typing import (
    Any,
    Union
)
from discord import (
    Client,
    Intents,
    Thread,
    http
)

if not __debug__:
    from dotenv import load_dotenv
    load_dotenv('.env')

RDS_HOST = os.getenv('RDS_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

snowflake = Union[str, int]

class Bot(Client):
    def __init__(self, *, intents: Intents = Intents.default(), **options: Any) -> None:
        super().__init__(intents=intents, **options)

        # connect database
        try:
            self.conn = pymysql.connect(host=RDS_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, connect_timeout=5)
        except pymysql.MySQLError as e:
            print("ERROR: Unexpected error: Could not connect to MySQL instance.")
            print(e)
            import sys
            sys.exit(1)
    
    def get_status(self, thread_id: snowflake) -> bool:
        sql = "SELECT available FROM  unarchive WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, (str(thread_id), ))

            results = cur.fetchall()
            for r in results:
                return bool(r[0])
            
        return False


    async def on_ready(self):
        print("bot start")

    async def on_thread_update(self, before: Thread, after: Thread) -> None:

        if after.locked or not after.archived or before.archived:
            return
        
        thread_id: snowflake = after.id
        if not bool(thread_id):
            return
            
        status: bool = self.get_status(thread_id)


        if not status:
            return
        
        await asyncio.sleep(5)
        await after.edit(archived=False, reason="Auto Unarchive Thread.")
