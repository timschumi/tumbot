CREATE TABLE birtdays(
  userId INT NOT NULL UNIQUE,
  day INT NOT NULL,
  month INT NOT NULL
);

PRAGMA user_version = 7;
