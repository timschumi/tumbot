class ConfigManager:
    def __init__(self, db):
        self.db = db

    def get(self, dbid, name, default=None):
        result = self.db.get(dbid).execute("SELECT value FROM config WHERE name = ?", (name,)).fetchall()

        if len(result) < 1:
            return default

        return str(result[0][0])

    def set(self, dbid, name, value):
        with self.db.get(dbid) as db:
            db.execute("REPLACE INTO config (name, value) VALUES (?, ?)", (name, value))
