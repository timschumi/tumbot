import typing
import inspect

import discord
from discord.ext import commands


class InvalidConversionException(Exception):
    """Thrown when a value can't be converted using a converter"""


def converter_from_def(conv):
    """Builds a converter object from a type definition"""

    # If this already is an instance of a converter, return it
    if isinstance(conv, Converter):
        return conv

    # If this is a converter class, create a converter
    if inspect.isclass(conv) and issubclass(conv, Converter):
        return conv()

    # Is this one of the advanced python typing definitions?
    if hasattr(conv, "__origin__"):
        if conv.__origin__ is typing.Union:
            types = conv.__args__

            # Normal Union
            if type(None) not in types:
                return UnionConverter([converter_from_def(e) for e in types])

            types = [e for e in types if not isinstance(None, e)]

            if len(types) == 1:
                return OptionalConverter(converter_from_def(types[0]))

            return OptionalConverter(
                UnionConverter([converter_from_def(e) for e in types])
            )

    # Convert from standard typing definitions
    if isinstance(conv, type):
        if conv.__name__ == "bool":
            return BoolConverter()

        if conv.__name__ == "str":
            return StringConverter()

        if conv.__name__ == "int":
            return IntConverter()

        return globals()[conv.__name__ + "Converter"]()

    return None


class Converter:
    """The common interface for a converter"""

    async def store(self, ctx, value):
        """Converts a value into the internal string representation"""

        raise NotImplementedError("store has not been implemented")

    async def load(self, ctx, value):
        """Converts an internal string representation into the actual value"""

        raise NotImplementedError("load has not been implemented")

    def name(self):
        """Returns a human-readable name for the given type"""

        raise NotImplementedError("name has not been implemented")

    async def _tostr(self, ctx, value):
        """Converts an actual object into a human-readable output"""

        del ctx
        return str(value)

    async def show(self, ctx, value):
        """Converts an object (actual object or internal string) into a human-readable output"""

        if isinstance(value, str):
            value = await self.load(ctx, value)

        return await self._tostr(ctx, value)


class OptionalConverter(Converter):
    """Converts a value to None or passes to the enclosed converter"""

    def __init__(self, conv):
        self._conv = converter_from_def(conv)

    async def store(self, ctx, value):
        if value is None:
            raise InvalidConversionException("Can't convert None to String")

        return await self._conv.store(ctx, value)

    async def load(self, ctx, value):
        if value is None:
            return None

        return await self._conv.load(ctx, value)

    def name(self):
        return f"Optional[{self._conv.name()}]"

    async def show(self, ctx, value):
        if value is None:
            return "None"

        return await self._conv.show(ctx, value)


class UnionConverter(Converter):
    """Converts the value by trying all the enclosed converters in order"""

    def __init__(self, *args):
        self._conv = [converter_from_def(conv) for conv in args]

    async def _try_for_all(self, ctx, value, func):
        for conv in self._conv:
            try:
                return await getattr(conv, func)(ctx, value)
            except InvalidConversionException:
                pass

        # If we are here, none of the Converters worked
        raise InvalidConversionException(
            f"Could not convert {value} using type {self.name()}"
        )

    async def store(self, ctx, value):
        return await self._try_for_all(ctx, value, "store")

    async def load(self, ctx, value):
        return await self._try_for_all(ctx, value, "load")

    def name(self):
        return f"Union[{', '.join([conv.name() for conv in self._conv])}]"

    async def show(self, ctx, value):
        return await self._try_for_all(ctx, value, "show")


class BoolConverter(Converter):
    """Converts boolean-like values and strings"""

    async def store(self, ctx, value):
        if value in (True, "yes", "y", "true", "True", "t", "1", "enable", "on"):
            return "1"

        if value in (False, "no", "n", "false", "False", "f", "0", "disable", "off"):
            return "0"

        raise InvalidConversionException(
            f"'{value}' is not recognized as a boolean value"
        )

    async def load(self, ctx, value):
        if value == "0":
            return False

        if value == "1":
            return True

        raise InvalidConversionException(
            f"'{value}' could not be converted to a boolean type"
        )

    def name(self):
        return "Boolean"


class StringConverter(Converter):
    """Converts internal string representations into themselves. Essentially a no-op."""

    async def store(self, ctx, value):
        return value

    async def load(self, ctx, value):
        return value

    def name(self):
        return "String"

    async def show(self, ctx, value):
        return f'"{value}"'


class IntConverter(Converter):
    """Converts integers"""

    async def store(self, ctx, value):
        if isinstance(value, int):
            return str(value)

        if isinstance(value, str) and value.isnumeric():
            return value

        raise InvalidConversionException(
            f"{value} is nether a number nor a numeric string"
        )

    async def load(self, ctx, value):
        try:
            return int(value)
        except ValueError as e:
            raise InvalidConversionException(e) from e

    def name(self):
        return "Int"

    async def _tostr(self, ctx, value):
        return f"{value}"


class MemberConverter(Converter):
    """Converts guild members"""

    async def store(self, ctx, value):
        if isinstance(value, discord.Member):
            return str(value.id)

        try:
            value = await commands.converter.MemberConverter().convert(ctx, value)
        except commands.MemberNotFound as e:
            raise InvalidConversionException(e) from e

        return str(value.id)

    async def load(self, ctx, value):
        member = ctx.guild.get_member(int(value))

        if member is None:
            raise InvalidConversionException(f"Member with ID '{value}' not found")

        return member

    def name(self):
        return "Member"

    async def _tostr(self, ctx, value):
        return f"@{value}"


class UserConverter(Converter):
    """Converts users"""

    async def store(self, ctx, value):
        if isinstance(value, discord.User):
            return str(value.id)

        try:
            value = await commands.converter.UserConverter().convert(ctx, value)
        except commands.UserNotFound as e:
            raise InvalidConversionException(e) from e

        return str(value.id)

    async def load(self, ctx, value):
        user = ctx.bot.get_user(int(value))

        if user is None:
            raise InvalidConversionException(f"User with ID '{value}' not found")

        return user

    def name(self):
        return "User"

    async def _tostr(self, ctx, value):
        return f"@{value}"


class TextChannelConverter(Converter):
    """Converts text channels"""

    async def store(self, ctx, value):
        if isinstance(value, discord.TextChannel):
            return str(value.id)

        try:
            value = await commands.converter.TextChannelConverter().convert(ctx, value)
        except commands.ChannelNotFound as e:
            raise InvalidConversionException(e) from e

        return str(value.id)

    async def load(self, ctx, value):
        channel = ctx.guild.get_channel(int(value))

        if channel is None:
            raise InvalidConversionException(f"TextChannel with ID '{value}' not found")

        return channel

    def name(self):
        return "TextChannel"

    async def _tostr(self, ctx, value):
        return f"#{value}"


class RoleConverter(Converter):
    """Converts roles"""

    async def store(self, ctx, value):
        if isinstance(value, discord.Role):
            return str(value.id)

        if value == "everyone":
            return str(ctx.guild.id)

        try:
            value = await commands.converter.RoleConverter().convert(ctx, value)
        except commands.RoleNotFound as e:
            raise InvalidConversionException(e) from e

        return str(value.id)

    async def load(self, ctx, value):
        role = ctx.guild.get_role(int(value))

        if role is None:
            raise InvalidConversionException(f"Role with ID '{value}' not found")

        return role

    def name(self):
        return "Role"

    async def _tostr(self, ctx, value):
        return f"@{value.name}"
