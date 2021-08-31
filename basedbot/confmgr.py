from enum import Enum
from typing import Optional
from .converter import converter_from_def


class UnregisteredVariableException(Exception):
    """ Thrown when a non-existing configuration variable is queried """


class ConflictingVariableException(Exception):
    """ Thrown when two different configuration variables are defined using the same name """


class ConfigAccessLevel(Enum):
    """ Constants for configuration variable access levels """

    ADMIN = 1
    OWNER = 2
    INTERNAL = 3


class ConfigVar:
    """ A single configuration variable and its properties """

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
        """ Gets the raw configuration value for a given context """

        with self._db.get(ctx, self.scope) as db:
            result = db.execute("SELECT value FROM config WHERE name = ?",
                                (self.name,)).fetchall()

        if len(result) < 1:
            return self.default

        return str(result[0][0])

    async def cget(self, ctx):
        """ Gets the converted configuration value for a given context """

        value = self.get(ctx)
        return await self.conv.load(ctx, value)

    def set(self, ctx, value):
        """ Sets the raw configuration value for a given context """

        with self._db.get(ctx, self.scope) as db:
            db.execute("REPLACE INTO config (name, value) VALUES (?, ?)", (self.name, value))

    async def cset(self, ctx, value):
        """ Converts the given value and sets it for a given context """

        value = await self.conv.store(ctx, value)
        self.set(ctx, value)

    def unset(self, ctx):
        """ Resets the configuration variable to the default value """

        with self._db.get(ctx, self.scope) as db:
            db.execute("DELETE FROM config WHERE name = ?", (self.name,))

    async def show(self, ctx):
        """ Converts the stored value to a human-readable representation """

        return await self.conv.show(ctx, self.get(ctx))


class ConfigManager:
    """ Manages a collection of configuration variables """

    def __init__(self, db):
        self.db = db
        self._vars = {}

    def register(self, name, **kwargs):
        """ Adds a new configuration variable with the given name and properties """

        if name not in self._vars:
            self._vars[name] = ConfigVar(self.db, name, **kwargs)
            return self._vars[name]

        existing = self._vars[name]

        for key, value in kwargs.items():
            if not hasattr(existing, key):
                continue

            if getattr(existing, key) != value:
                raise ConflictingVariableException(f"Attribute `{key}` conflicts with "
                                                   f"existing variable definition.")

        return self._vars[name]

    @property
    def registered_variables(self):
        """ Returns the list of registered variables """
        return self._vars.keys()

    def var(self, name):
        """ Gets the stored variable object for a given name """
        if name not in self._vars:
            raise UnregisteredVariableException(f"Variable `{name}` is not registered.")

        return self._vars[name]

    def get(self, ctx, name, **kwargs):
        """ Legacy interface for getting raw configuration variable values """

        existing = self.var(name)
        return existing.get(ctx, **kwargs)

    def set(self, ctx, name, **kwargs):
        """ Legacy interface for setting raw configuration variable values """

        existing = self.var(name)
        existing.set(ctx, **kwargs)
