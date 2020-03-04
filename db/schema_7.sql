CREATE TABLE birthdays
(
    userId TEXT NOT NULL UNIQUE,
    date   INT  NOT NULL,
    month  INT  NOT NULL
);

PRAGMA user_version = 7;
