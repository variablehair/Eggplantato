.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    discord.py.

Version Related Info
---------------------

There are two main ways to query version information about the library.

.. data:: version_info

    A named tuple that is similar to `sys.version_info`_.

    Just like `sys.version_info`_ the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

    .. _sys.version_info: https://docs.python.org/3.5/library/sys.html#sys.version_info

.. data:: __version__

    A string representation of the version. e.g. ``'0.10.0-alpha0'``.

Client
-------

.. autoclass:: Client
    :members:

.. autoclass:: AutoShardedClient
    :members:

Opus Library
~~~~~~~~~~~~~

.. autofunction:: discord.opus.load_opus

.. autofunction:: discord.opus.is_loaded

.. _discord-api-events:

Event Reference
---------------

This page outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import discord

    class MyClient(discord.Client):

        @asyncio.coroutine
        def on_message(self, message):
            yield from self.send_message(message.channel, 'Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignore the exception.

.. warning::

    All the events must be a |corourl|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must either be decorated
    with ``@asyncio.coroutine`` or in Python 3.5+ be defined using the ``async def``
    declaration.

    The following two functions are examples of coroutine functions: ::

        async def on_ready():
            pass

        @asyncio.coroutine
        def on_ready():
            pass

    Since this can be a potentially common mistake, there is a helper
    decorator, :meth:`Client.async_event` to convert a basic function
    into a coroutine and an event at the same time. Note that it is
    not necessary if you use ``async def``.

.. versionadded:: 0.7.0
    Subclassing to listen to events.

.. function:: on_connect()

    Called when the client has successfully connected to Discord. This is not
    the same as the client being fully prepared, see :func:`on_ready` for that.

    The warnings on :func:`on_ready` also apply.

.. function:: on_ready()

    Called when the client is done preparing the data received from Discord. Usually after login is successful
    and the :attr:`Client.guilds` and co. are filled up.

    .. warning::

        This function is not guaranteed to be the first event called.
        Likewise, this function is **not** guaranteed to only be called
        once. This library implements reconnection logic and thus will
        end up calling this event whenever a RESUME request fails.

.. function:: on_shard_ready(shard_id)

    Similar to :func:`on_ready` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has become ready.

    :param shard_id: The shard ID that is ready.

.. function:: on_resumed()

    Called when the client has resumed a session.

.. function:: on_error(event, \*args, \*\*kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    supress the default action of printing the traceback.

    The information of the exception rasied and the exception itself can
    be retreived with a standard call to ``sys.exc_info()``.

    If you want exception to propogate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    ``raise`` statement.  Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    :param event: The name of the event that raised the exception.
    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        execption.

.. function:: on_message(message)

    Called when a message is created and sent to a guild.

    :param message: A :class:`Message` of the current message.

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is received from the websocket, before
    it's processed.This event is always dispatched when a message is
    received and the passed data is not processed in any way.

    This is only really useful for grabbing the websocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
        websocket. The voice websocket will not trigger this event.

    :param msg: The message passed in from the websocket library.
                Could be ``bytes`` for a binary message or ``str``
                for a regular message.

.. function:: on_socket_raw_send(payload)

    Called whenever a send operation is done on the websocket before the
    message is sent. The passed parameter is the message that is to
    sent to the websocket.

    This is only really useful for grabbing the websocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
        websocket. The voice websocket will not trigger this event.

    :param payload: The message that is about to be passed on to the
                    websocket library. It can be ``bytes`` to denote a binary
                    message or ``str`` to denote a regular text message.

.. function:: on_message_delete(message)

    Called when a message is deleted. If the message is not found in the
    :attr:`Client.messages` cache, then these events will not be called. This
    happens if the message is too old or the client is participating in high
    traffic guilds. To fix this, increase the ``max_messages`` option of
    :class:`Client`.

    :param message: A :class:`Message` of the deleted message.

.. function:: on_message_edit(before, after)

    Called when a message receives an update event. If the message is not found
    in the :attr:`Client.messages` cache, then these events will not be called.
    This happens if the message is too old or the client is participating in high
    traffic guilds. To fix this, increase the ``max_messages`` option of :class:`Client`.

    The following non-exhaustive cases trigger this event:

    - A message has been pinned or unpinned.
    - The message content has been changed.
    - The message has received an embed.
        - For performance reasons, the embed guild does not do this in a "consistent" manner.
    - A call message has received an update to its participants or ending time.

    :param before: A :class:`Message` of the previous version of the message.
    :param after: A :class:`Message` of the current version of the message.

.. function:: on_reaction_add(reaction, user)

    Called when a message has a reaction added to it. Similar to on_message_edit,
    if the message is not found in the :attr:`Client.messages` cache, then this
    event will not be called.

    .. note::

        To get the message being reacted, access it via :attr:`Reaction.message`.

    :param reaction: A :class:`Reaction` showing the current state of the reaction.
    :param user: A :class:`User` or :class:`Member` of the user who added the reaction.

.. function:: on_reaction_remove(reaction, user)

    Called when a message has a reaction removed from it. Similar to on_message_edit,
    if the message is not found in the :attr:`Client.messages` cache, then this event
    will not be called.

    .. note::

        To get the message being reacted, access it via :attr:`Reaction.message`.

    :param reaction: A :class:`Reaction` showing the current state of the reaction.
    :param user: A :class:`User` or :class:`Member` of the user who removed the reaction.

.. function:: on_reaction_clear(message, reactions)

    Called when a message has all its reactions removed from it. Similar to on_message_edit,
    if the message is not found in the :attr:`Client.messages` cache, then this event
    will not be called.

    :param message: The :class:`Message` that had its reactions cleared.
    :param reactions: A list of :class:`Reaction`\s that were removed.

.. function:: on_channel_delete(channel)
              on_channel_create(channel)

    Called whenever a channel is removed or added from a guild.

    Note that you can get the guild from :attr:`Channel.guild`.
    :func:`on_channel_create` could also pass in a :class:`PrivateChannel` depending
    on the value of :attr:`Channel.is_private`.

    :param channel: The :class:`Channel` that got added or deleted.

.. function:: on_channel_update(before, after)

    Called whenever a channel is updated. e.g. changed name, topic, permissions.

    :param before: The :class:`Channel` that got updated with the old info.
    :param after: The :class:`Channel` that got updated with the updated info.

.. function:: on_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a channel.

    :param channel: The :class:`Channel` that had it's pins updated.
    :param last_pin: A ``datetime.datetime`` object representing when the latest message
    was pinned or ``None`` if there are no pins.

.. function:: on_member_join(member)
              on_member_remove(member)

    Called when a :class:`Member` leaves or joins a :class:`Guild`.

    :param member: The :class:`Member` that joined or left.

.. function:: on_member_update(before, after)

    Called when a :class:`Member` updates their profile.

    This is called when one or more of the following things change:

    - status
    - game playing
    - avatar
    - nickname
    - roles

    :param before: The :class:`Member` that updated their profile with the old info.
    :param after: The :class:`Member` that updated their profile with the updated info.

.. function:: on_guild_join(guild)

    Called when a :class:`Guild` is either created by the :class:`Client` or when the
    :class:`Client` joins a guild.

    :param guild: The class:`Guild` that was joined.

.. function:: on_guild_remove(guild)

    Called when a :class:`Guild` is removed from the :class:`Client`.

    This happens through, but not limited to, these circumstances:

    - The client got banned.
    - The client got kicked.
    - The client left the guild.
    - The client or the guild owner deleted the guild.

    In order for this event to be invoked then the :class:`Client` must have
    been part of the guild to begin with. (i.e. it is part of :attr:`Client.guilds`)

    :param guild: The :class:`Guild` that got removed.

.. function:: on_guild_update(before, after)

    Called when a :class:`Guild` updates, for example:

    - Changed name
    - Changed AFK channel
    - Changed AFK timeout
    - etc

    :param before: The :class:`Guild` prior to being updated.
    :param after: The :class:`Guild` after being updated.

.. function:: on_guild_role_create(role)
              on_guild_role_delete(role)

    Called when a :class:`Guild` creates or deletes a new :class:`Role`.

    To get the guild it belongs to, use :attr:`Role.guild`.

    :param role: The :class:`Role` that was created or deleted.

.. function:: on_guild_role_update(before, after)

    Called when a :class:`Role` is changed guild-wide.

    :param before: The :class:`Role` that updated with the old info.
    :param after: The :class:`Role` that updated with the updated info.

.. function:: on_guild_emojis_update(before, after)

    Called when a :class:`Guild` adds or removes :class:`Emoji`.

    :param before: A list of :class:`Emoji` before the update.
    :param after: A list of :class:`Emoji` after the update.

.. function:: on_guild_available(guild)
              on_guild_unavailable(guild)

    Called when a guild becomes available or unavailable. The guild must have
    existed in the :attr:`Client.guilds` cache.

    :param guild: The :class:`Guild` that has changed availability.

.. function:: on_voice_state_update(before, after)

    Called when a :class:`Member` changes their voice state.

    The following, but not limited to, examples illustrate when this event is called:

    - A member joins a voice room.
    - A member leaves a voice room.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a guild administrator.

    :param before: The :class:`Member` whose voice state changed prior to the changes.
    :param after: The :class:`Member` whose voice state changed after the changes.

.. function:: on_member_ban(member)

    Called when a :class:`Member` gets banned from a :class:`Guild`.

    You can access the guild that the member got banned from via :attr:`Member.guild`.

    :param member: The member that got banned.

.. function:: on_member_unban(guild, user)

    Called when a :class:`User` gets unbanned from a :class:`Guild`.

    :param guild: The guild the user got unbanned from.
    :param user: The user that got unbanned.

.. function:: on_typing(channel, user, when)

    Called when someone begins typing a message.

    The ``channel`` parameter could either be a :class:`PrivateChannel` or a
    :class:`Channel`. If ``channel`` is a :class:`PrivateChannel` then the
    ``user`` parameter is a :class:`User`, otherwise it is a :class:`Member`.

    :param channel: The location where the typing originated from.
    :param user: The user that started typing.
    :param when: A ``datetime.datetime`` object representing when typing started.

.. function:: on_group_join(channel, user)
              on_group_remove(channel, user)

    Called when someone joins or leaves a group, i.e. a :class:`PrivateChannel`
    with a :attr:`PrivateChannel.type` of :attr:`ChannelType.group`.

    :param channel: The group that the user joined or left.
    :param user: The user that joined or left.

.. function:: on_relationship_add(relationship)
              on_relationship_remove(relationship)

    Called when a :class:`Relationship` is added or removed from the
    :class:`ClientUser`.

    :param relationship: The relationship that was added or removed.

.. function:: on_relationship_update(before, after)

    Called when a :class:`Relationship` is updated, e.g. when you
    block a friend or a friendship is accepted.

    :param before: The previous relationship status.
    :param after: The updated relationship status.

.. _discord-api-utils:

Utility Functions
-----------------

.. autofunction:: discord.utils.find

.. autofunction:: discord.utils.get

.. autofunction:: discord.utils.snowflake_time

.. autofunction:: discord.utils.oauth_url

Application Info
------------------

.. class:: AppInfo

    A namedtuple representing the bot's application info.

    .. attribute:: id

        The application's ``client_id``.
    .. attribute:: name

        The application's name.
    .. attribute:: description

        The application's description
    .. attribute:: icon

        The application's icon hash if it exists, ``None`` otherwise.
    .. attribute:: icon_url

        A property that retrieves the application's icon URL if it exists.

        If it doesn't exist an empty string is returned.
    .. attribute:: owner

        The owner of the application. This is a :class:`User` instance
        with the owner's information at the time of the call.

Profile
---------

.. class:: Profile

    A namedtuple representing a user's Discord public profile.

    .. attribute:: user

        The :class:`User` the profile belongs to.
    .. attribute:: premium

        A boolean indicating if the user has premium (i.e. Discord Nitro).
    .. attribute:: premium_since

        A naive UTC datetime indicating how long the user has been premium since.
        This could be ``None`` if not applicable.
    .. attribute:: mutual_guilds

        A list of :class:`Guild` that the :class:`ClientUser` shares with this
        user.
    .. attribute:: connected_accounts

        A list of dict objects indicating the accounts the user has connected.

        An example entry can be seen below: ::

            {type: "twitch", id: "92473777", name: "discordapp"}

.. _discord-api-enums:

Enumerations
-------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of `enum`_.

.. _enum: https://docs.python.org/3/library/enum.html

.. class:: ChannelType

    Specifies the type of :class:`Channel`.

    .. attribute:: text

        A text channel.
    .. attribute:: voice

        A voice channel.
    .. attribute:: private

        A private text channel. Also called a direct message.
    .. attribute:: group

        A private group text channel.

.. class:: MessageType

    Specifies the type of :class:`Message`. This is used to denote if a message
    is to be interpreted as a system message or a regular message.

    .. attribute:: default

        The default message type. This is the same as regular messages.
    .. attribute:: recipient_add

        The system message when a recipient is added to a group private
        message, i.e. a private channel of type :attr:`ChannelType.group`.
    .. attribute:: recipient_remove

        The system message when a recipient is removed from a group private
        message, i.e. a private channel of type :attr:`ChannelType.group`.
    .. attribute:: call

        The system message denoting call state, e.g. missed call, started call,
        etc.
    .. attribute:: channel_name_change

        The system message denoting that a channel's name has been changed.
    .. attribute:: channel_icon_change

        The system message denoting that a channel's icon has been changed.
    .. attribute:: pins_add

        The system message denoting that a pinned message has been added to a channel.

.. class:: GuildRegion

    Specifies the region a :class:`Guild`'s voice server belongs to.

    .. attribute:: us_west

        The US West region.
    .. attribute:: us_east

        The US East region.
    .. attribute:: us_central

        The US Central region.
    .. attribute:: eu_west

        The EU West region.
    .. attribute:: eu_central

        The EU Central region.
    .. attribute:: singapore

        The Singapore region.
    .. attribute:: london

        The London region.
    .. attribute:: sydney

        The Sydney region.
    .. attribute:: amsterdam

        The Amsterdam region.
    .. attribute:: frankfurt

        The Frankfurt region.

    .. attribute:: brazil

        The Brazil region.
    .. attribute:: vip_us_east

        The US East region for VIP guilds.
    .. attribute:: vip_us_west

        The US West region for VIP guilds.
    .. attribute:: vip_amsterdam

        The Amsterdam region for VIP guilds.

.. class:: VerificationLevel

    Specifies a :class:`Guild`\'s verification level, which is the criteria in
    which a member must meet before being able to send messages to the guild.

    .. attribute:: none

        No criteria set.
    .. attribute:: low

        Member must have a verified email on their Discord account.
    .. attribute:: medium

        Member must have a verified email and be registered on Discord for more
        than five minutes.
    .. attribute:: high

        Member must have a verified email, be registered on Discord for more
        than five minutes, and be a member of the guild itself for more than
        ten minutes.
    .. attribute:: table_flip

        An alias for :attr:`high`.

.. class:: Status

    Specifies a :class:`Member` 's status.

    .. attribute:: online

        The member is online.
    .. attribute:: offline

        The member is offline.
    .. attribute:: idle

        The member is idle.
    .. attribute:: dnd

        The member is "Do Not Disturb".
    .. attribute:: do_not_disturb

        An alias for :attr:`dnd`.
    .. attribute:: invisible

        The member is "invisible". In reality, this is only used in sending
        a presence a la :meth:`Client.change_presence`. When you receive a
        user's presence this will be :attr:`offline` instead.

.. class:: RelationshipType

    Specifies the type of :class:`Relationship`

    .. attribute:: friend

        You are friends with this user.
    .. attribute:: blocked

        You have blocked this user.
    .. attribute:: incoming_request

        The user has sent you a friend request.
    .. attribute:: outgoing_request

        You have sent a friend request to this user.

Async Iterator
----------------

Some API functions return an "async iterator". An async iterator is something that is
capable of being used in an `async for <https://docs.python.org/3/reference/compound_stmts.html#the-async-for-statement>`_
statement.

These async iterators can be used as follows in 3.5 or higher: ::

    async for elem in channel.history():
        # do stuff with elem here

If you are using 3.4 however, you will have to use the more verbose way: ::

    iterator = channel.history() # or whatever returns an async iterator
    while True:
        try:
            item = yield from iterator.get()
        except discord.NoMoreItems:
            break

        # do stuff with item here

Certain utilities make working with async iterators easier, detailed below.

.. class:: AsyncIterator

    Represents the "AsyncIterator" concept. Note that no such class exists,
    it is purely abstract.

    .. method:: get(**attrs)

        |coro|

        Similar to :func:`utils.get` except run over the async iterator.

    .. method:: find(predicate)

        |coro|

        Similar to :func:`utils.find` except run over the async iterator.

        Unlike :func:`utils.find`\, the predicate provided can be a
        coroutine.

        :param predicate: The predicate to use. Can be a coroutine.
        :return: The first element that returns ``True`` for the predicate or ``None``.

    .. method:: flatten()

        |coro|

        Flattens the async iterator into a ``list`` with all the elements.

        :return: A list of every element in the async iterator.
        :rtype: list

    .. method:: map(func)

        This is similar to the built-in ``map`` function. Another
        :class:`AsyncIterator` is returned that executes the function on
        every element it is iterating over. This function can either be a
        regular function or a coroutine.

        :param func: The function to call on every element. Could be a coroutine.
        :return: An async iterator.

    .. method:: filter(predicate)

        This is similar to the built-in ``filter`` function. Another
        :class:`AsyncIterator` is returned that filters over the original
        async iterator. This predicate can be a regular function or a coroutine.

        :param predicate: The predicate to call on every element. Could be a coroutine.
        :return: An async iterator.

.. _discord_api_data:

Data Classes
--------------

Some classes are just there to be data containers, this lists them.

.. note::

    With the exception of :class:`Object`, :class:`Colour`, and :class:`Permissions` the
    data classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.

    If you want to get one of these data classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of data classes that you receive from the events specified in the
    :ref:`discord-api-events`.


.. warning::

    Nearly all data classes here have ``__slots__`` defined which means that it is
    impossible to have dynamic attributes to the data classes. The only exception
    to this rule is :class:`Object` which was designed with dynamic attributes in
    mind.

    More information about ``__slots__`` can be found
    `in the official python documentation <https://docs.python.org/3/reference/datamodel.html#slots>`_.

Object
~~~~~~~

.. autoclass:: Object
    :members:

ClientUser
~~~~~~~~~~~~

.. autoclass:: ClientUser
    :members:
    :inherited-members:

Relationship
~~~~~~~~~~~~~~

.. autoclass:: Relationship
    :members:

User
~~~~~

.. autoclass:: User
    :members:
    :inherited-members:

Message
~~~~~~~

.. autoclass:: Message
    :members:

Reaction
~~~~~~~~~

.. autoclass:: Reaction
    :members:

Embed
~~~~~~

.. autoclass:: Embed
    :members:

CallMessage
~~~~~~~~~~~~

.. autoclass:: CallMessage
    :members:

GroupCall
~~~~~~~~~~

.. autoclass:: GroupCall
    :members:

Guild
~~~~~~

.. autoclass:: Guild
    :members:

Member
~~~~~~

.. autoclass:: Member
    :members:
    :inherited-members:

VoiceState
~~~~~~~~~~~

.. autoclass:: VoiceState
    :members:

Colour
~~~~~~

.. autoclass:: Colour
    :members:

Game
~~~~

.. autoclass:: Game
    :members:

Emoji
~~~~~

.. autoclass:: Emoji
    :members:

Role
~~~~~

.. autoclass:: Role
    :members:

Permissions
~~~~~~~~~~~~

.. autoclass:: Permissions
    :members:

PermissionOverwrite
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PermissionOverwrite
    :members:


TextChannel
~~~~~~~~~~~~

.. autoclass:: TextChannel
    :members:
    :inherited-members:

VoiceChannel
~~~~~~~~~~~~~

.. autoclass:: VoiceChannel
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. autoclass:: DMChannel
    :members:
    :inherited-members:

GroupChannel
~~~~~~~~~~~~

.. autoclass:: GroupChannel
    :members:
    :inherited-members:


Invite
~~~~~~~

.. autoclass:: Invite
    :members:

Exceptions
------------

The following exceptions are thrown by the library.

.. autoexception:: DiscordException

.. autoexception:: ClientException

.. autoexception:: LoginFailure

.. autoexception:: NoMoreItems

.. autoexception:: HTTPException
    :members:

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: ConnectionClosed

.. autoexception:: discord.opus.OpusError

.. autoexception:: discord.opus.OpusNotLoaded
