class UnregisteredVariableException(Exception):
    pass


class ConflictingVariableException(Exception):
    pass


class ConfigVar:
    def __init__(self, db, name, default=None):
        self._db = db

        self.name = name
        self.default = default

    def get(self, dbid, default=None):
        if default is None:
            default = self.default

        return self._get(dbid, default=default)

    def set(self, dbid, value):
        self._set(dbid, value)

    def _get(self, dbid, default=None):
        result = self._db.get(dbid).execute("SELECT value FROM config WHERE name = ?", (self.name,)).fetchall()

        if len(result) < 1:
            return default

        return str(result[0][0])

    def _set(self, dbid, value):
        with self._db.get(dbid) as db:
            db.execute("REPLACE INTO config (name, value) VALUES (?, ?)", (self.name, value))


class ConfigManager:
    def __init__(self, db):
        self.db = db
        self._vars = {}

    def register(self, name, **kwargs):
        if name not in self._vars:
            self._vars[name] = ConfigVar(self.db, name, **kwargs)
            return self._vars[name]

        existing = self._vars[name]

        for key, value in kwargs.items():
            if not hasattr(existing, key):
                continue

            if getattr(existing, key) != kwargs[key]:
                raise ConflictingVariableException(f"Attribute `{key}` conflicts with existing variable definition.")

        return self._vars[name]

    def var(self, name):
        if name not in self._vars:
            raise UnregisteredVariableException(f"Variable `{name}` is not registered.")

        return self._vars[name]

    def get(self, dbid, name, **kwargs):
        existing = self.var(name)
        return existing.get(dbid, **kwargs)

    def set(self, dbid, name, **kwargs):
        existing = self.var(name)
        existing.set(dbid, **kwargs)
