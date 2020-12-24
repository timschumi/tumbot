CREATE TABLE permissions (
  name TEXT NOT NULL,
  id INTEGER NOT NULL,
  state INTEGER NOT NULL,
  PRIMARY KEY (name, id)
) WITHOUT ROWID;

PRAGMA user_version = 2;
