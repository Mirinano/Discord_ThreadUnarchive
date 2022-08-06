CREATE TABLE thread (
    id CHAR(20) PRIMARY KEY,
    channel CHAR(20),
    thread_name TEXT,
    locked BIT(1),
    archive BIT(1),
    archive_timestamp TIMESTAMP,
    auto_archive_duration INT,
    invitable BIT(1),
    create_timestamp TIMESTAMP
);