import functools
import discord

__all__ = [
    "raw_reaction_filter",
]


def raw_reaction_filter(
    guild_only=False, not_self=None, emoji_names=None, client_func=None
):
    """Filters events that are received by raw_reaction handlers

    Parameters
    ----------
    guild_only: :class:`bool`
        If True, removes events that are not from a guild. False by default.
    not_self: :class:`bool`
        If True, removes events that are caused by ourselves. False by default.
    emoji_names: Optional[List[:class:`str`]]
        If set, removes events with emoji names that are not in the list. None by default.
    client_func: Optional[:class:`function`]
        A helper function that retrieves an instance of :class:`discord.Client`. None by default.
        It receives the same arguments that the wrapped function receives.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Use the first RawReactionActionEvent argument as payload
            payload = next(
                filter(lambda e: isinstance(e, discord.RawReactionActionEvent), args)
            )

            if guild_only and payload.guild_id is None:
                return

            if not_self and client_func is None:
                raise ValueError("`client_func` must not be None when using `not_self`")

            if not_self and payload.user_id == client_func(*args, **kwargs).user.id:
                return

            if emoji_names and payload.emoji.name not in emoji_names:
                return

            return await func(*args, **kwargs)

        return wrapper

    return decorator
