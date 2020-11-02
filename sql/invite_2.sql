ALTER TABLE invite_active ADD allowed_by INT NOT NULL DEFAULT 0;
UPDATE invite_active SET allowed_by = user WHERE allowed_by = 0;

CREATE TABLE invite_requests
(
    message   INT NOT NULL UNIQUE,
    user      INT  NOT NULL,
    reason    TEXT
);

PRAGMA user_version = 2;
