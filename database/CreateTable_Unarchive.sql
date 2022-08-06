CREATE TABLE unarchive (
    id CHAR(20) PRIMARY KEY,
    available BIT(1) NOT NULL,
    FOREIGN KEY(id)
    REFERENCES thread(id)
    ON DELETE CASCADE
);