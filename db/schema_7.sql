CREATE TABLE birthdays
(
    userId INT  NOT NULL UNIQUE,
    day    INT  NOT NULL,
    month  INT  NOT NULL
);

-- Skip ahead to version 8, since schema 8 is just a fixup/data conversion.
PRAGMA user_version = 8;
