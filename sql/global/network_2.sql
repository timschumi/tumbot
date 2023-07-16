ALTER TABLE network_member ADD propagate_ban INT NOT NULL DEFAULT FALSE;

PRAGMA user_version = 2;
