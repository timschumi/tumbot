from enum import Enum


class UnregisteredVariableException(Exception):
    pass


class ConflictingVariableException(Exception):
    pass


class ConfigAccessLevel(Enum):
    ADMIN = 1
    OWNER = 2
    INTERNAL = 3


class ConfigVar:
    def __init__(self, db, name, default=None, access=ConfigAccessLevel.ADMIN, description=None):
        self._db = db

        self.name = name
        self.default = default
        self.access = access
        self.description = description

    def get(self, dbid, default=None):
        if default is None:
            default = self.default

        result = self._db.get(dbid).execute("SELECT value FROM config WHERE name = ?", (self.name,)).fetchall()

        if len(result) < 1:
            return default

        return str(result[0][0])

    def set(self, dbid, value):
        with self._db.get(dbid) as db:
            db.execute("REPLACE INTO config (name, value) VALUES (?, ?)", (self.name, value))

    def unset(self, dbid):
        with self._db.get(dbid) as db:
            db.execute("DELETE FROM config WHERE name = ?", (self.name,))


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

    @property
    def registered_variables(self):
        return self._vars.keys()

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
