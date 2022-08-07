CREATE TABLE unarchive (
    id CHAR(20) PRIMARY KEY,
    available BOOLEAN NOT NULL,
    FOREIGN KEY(id)
    REFERENCES thread(id)
    ON DELETE CASCADE
);