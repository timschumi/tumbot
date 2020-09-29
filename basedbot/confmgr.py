class ConfigManager:
    def __init__(self, db):
        self.db = db

    def get(self, guild_id, name, default=None):
        result = self.db.get(guild_id).execute("SELECT value FROM config WHERE name = ?", (name,)).fetchall()

        if len(result) < 1:
            return default

        return str(result[0][0])

    def set(self, guild_id, name, value):
        with self.db.get(guild_id) as db:
            db.execute("REPLACE INTO config (name, value) VALUES (?, ?)", (name, value))