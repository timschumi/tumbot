from enum import Enum
from typing import Optional
from .converter import converter_from_def


class UnregisteredVariableException(Exception):
    pass


class ConflictingVariableException(Exception):
    pass


class ConfigAccessLevel(Enum):
    ADMIN = 1
    OWNER = 2
    INTERNAL = 3


class ConfigVar:
    def __init__(self, db, name, default=None, access=ConfigAccessLevel.ADMIN,
                 description=None, scope='guild', conv=Optional[str]):
        self._db = db

        self.name = name
        self.default = default
        self.access = access
        self.description = description
        self.scope = scope
        self.conv = converter_from_def(conv)

    def get(self, ctx):
        with self._db.get(ctx, self.scope) as db:
            result = db.execute("SELECT value FROM config WHERE name = ?",
                                (self.name,)).fetchall()

        if len(result) < 1:
            return self.default

        return str(result[0][0])

    async def cget(self, ctx):
        value = self.get(ctx)
        return await self.conv.load(ctx, value)

    def set(self, ctx, value):
        with self._db.get(ctx, self.scope) as db:
            db.execute("REPLACE INTO config (name, value) VALUES (?, ?)", (self.name, value))

    async def cset(self, ctx, value):
        value = await self.conv.store(ctx, value)
        self.set(ctx, value)

    def unset(self, ctx):
        with self._db.get(ctx, self.scope) as db:
            db.execute("DELETE FROM config WHERE name = ?", (self.name,))

    async def show(self, ctx):
        return await self.conv.show(ctx, self.get(ctx))


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
                raise ConflictingVariableException(f"Attribute `{key}` conflicts with "
                                                   f"existing variable definition.")

        return self._vars[name]

    @property
    def registered_variables(self):
        return self._vars.keys()

    def var(self, name):
        if name not in self._vars:
            raise UnregisteredVariableException(f"Variable `{name}` is not registered.")

        return self._vars[name]

    def get(self, ctx, name, **kwargs):
        existing = self.var(name)
        return existing.get(ctx, **kwargs)

    def set(self, ctx, name, **kwargs):
        existing = self.var(name)
        existing.set(ctx, **kwargs)
