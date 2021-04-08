CREATE TABLE network_invites
(
    network INTEGER NOT NULL UNIQUE,
    message INTEGER NOT NULL,
    inviter INTEGER NOT NULL
);

PRAGMA user_version = 1;