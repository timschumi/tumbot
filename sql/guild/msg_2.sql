ALTER TABLE msg ADD allow_memegen BOOLEAN NOT NULL DEFAULT FALSE;

PRAGMA user_version = 2;
