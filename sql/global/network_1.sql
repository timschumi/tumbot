CREATE TABLE network
(
    name   TEXT NOT NULL,
    owner  INTEGER NOT NULL
);

CREATE TABLE network_member
(
    nid INTEGER NOT NULL REFERENCES network ON DELETE CASCADE,
    gid INTEGER NOT NULL,
    admin INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (nid, gid)
) WITHOUT ROWID;

PRAGMA user_version = 1;
