CREATE TABLE version (
  name TEXT PRIMARY KEY,
  version INTEGER
) WITHOUT ROWID;

CREATE TABLE config (
  name TEXT PRIMARY KEY,
  value TEXT
) WITHOUT ROWID;

PRAGMA user_version = 1;
