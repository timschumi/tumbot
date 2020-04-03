CREATE TABLE temp AS
SELECT CAST(userId AS INTEGER) AS newuser, day, month FROM birthdays;

DROP TABLE birthdays;

CREATE TABLE birthdays
(
    userId INT  NOT NULL UNIQUE,
    day    INT  NOT NULL,
    month  INT  NOT NULL
);

INSERT INTO birthdays(userId, day, month)
SELECT newuser, day, month FROM temp;

DROP TABLE temp;

PRAGMA user_version = 8;
