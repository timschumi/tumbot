import discord

from discord.ext import commands


class UnregisteredPermissionException(Exception):
    """Thrown when a non-existent permission is queried"""


class ConflictingPermissionException(Exception):
    """Thrown when two different permissions are defined using the same name"""


def has_permissions(*perms):
    """Command decorator that requires the user to have all listed permissions"""

    def predicate(ctx):
        # Translate all permissions to their objects
        full_perms = [ctx.bot.perm.get(perm) for perm in perms]

        missing = [
            perm.pretty_name for perm in full_perms if not perm.allowed(ctx.author)
        ]

        if not missing:
            return True

        raise commands.MissingPermissions(missing)

    return commands.check(predicate)


def _build_id_list(member: discord.Member):
    ids = [member.id]
    ids += [role.id for role in reversed(member.roles)]

    return ids


class Permission:
    """A single permission and its properties"""

    def __init__(self, db, name, base=False, pretty_name=None):
        self._db = db

        self.name = name
        self.base = base
        self.pretty_name = pretty_name if pretty_name is not None else name

    def definitions(self, guild: discord.Guild):
        """Returns a list of all existing permission rules for a guild"""

        with self._db.get(guild.id) as db:
            res = db.execute(
                "SELECT * FROM permissions WHERE name = ?", (self.name,)
            ).fetchall()
        return {row["id"]: (row["state"] == 1) for row in res}

    def allowed(self, member: discord.Member):
        """Checks if a permission is granted for a given guild member"""

        if not isinstance(member, discord.Member):
            return False

        ids = _build_id_list(member)
        perms = self.definitions(member.guild)

        # Search for permission from the top
        for i in ids:
            # If no rule saved, go to next
            if i not in perms:
                continue

            return perms[i]

        # If we are here, no rule matched. Fall back to builtin permission.
        if isinstance(self.base, str):
            return getattr(member.guild_permissions, self.base, False)

        return self.base is True

    def grant(self, guild, discord_id):
        """Grants the permission to a given ID"""

        with self._db.get(guild.id) as db:
            db.execute(
                "REPLACE INTO permissions (name, id, state) VALUES (?, ?, ?)",
                (self.name, discord_id, 1),
            )

    def deny(self, guild, discord_id):
        """Denies the permission for a given ID"""

        with self._db.get(guild.id) as db:
            db.execute(
                "REPLACE INTO permissions (name, id, state) VALUES (?, ?, ?)",
                (self.name, discord_id, 0),
            )

    def default(self, guild, discord_id):
        """Removes existing rules for a given ID"""

        with self._db.get(guild.id) as db:
            db.execute(
                "DELETE FROM permissions WHERE name = ? AND id = ?",
                (self.name, discord_id),
            )


class PermissionManager:
    """Manages a collection of permissions"""

    def __init__(self, db):
        self.db = db
        self._perms = {}

    def register(self, name, **kwargs):
        """Adds a new permission with the given name and properties"""

        if name not in self._perms:
            self._perms[name] = Permission(self.db, name, **kwargs)
            return self._perms[name]

        existing = self._perms[name]

        for key, value in kwargs.items():
            if not hasattr(existing, key):
                continue

            if getattr(existing, key) != value:
                raise ConflictingPermissionException(
                    f"Attribute `{key}` conflicts with "
                    f"existing permission definition."
                )

        return self._perms[name]

    @property
    def registered_permissions(self):
        """Returns the list of registered permissions"""

        return self._perms.values()

    @property
    def registered_permission_names(self):
        """Returns the list of names of all registered permissions"""

        return self._perms.keys()

    def get(self, name):
        """Gets the stored permission object for a given name"""

        if name not in self._perms:
            raise UnregisteredPermissionException(
                f"Permission `{name}` is not registered."
            )

        return self._perms[name]
