CREATE TABLE invite_active
(
    code   TEXT NOT NULL UNIQUE,
    user   INT  NOT NULL,
    reason TEXT
);

PRAGMA user_version = 1;
