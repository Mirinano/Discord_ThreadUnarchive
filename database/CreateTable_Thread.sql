CREATE TABLE thread (
    id CHAR(20) PRIMARY KEY,
    channel CHAR(20),
    thread_name TEXT,
    locked BOOLEAN,
    archive BOOLEAN,
    archive_timestamp TIMESTAMP,
    auto_archive_duration INT,
    invitable BOOLEAN,
    create_timestamp TIMESTAMP
);