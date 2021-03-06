# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from .user import User, Profile
from .invite import Invite
from .object import Object
from .errors import *
from .permissions import Permissions, PermissionOverwrite
from .enums import ChannelType, Status
from .gateway import *
from .emoji import Emoji
from .http import HTTPClient
from .state import ConnectionState
from . import utils, compat
from .backoff import ExponentialBackoff

import asyncio
import aiohttp
import websockets

import logging, traceback
import sys, re, io
import itertools
import datetime
from collections import namedtuple
from os.path import split as path_split

PY35 = sys.version_info >= (3, 5)
log = logging.getLogger(__name__)

AppInfo = namedtuple('AppInfo', 'id name description icon owner')

def app_info_icon_url(self):
    """Retrieves the application's icon_url if it exists. Empty string otherwise."""
    if not self.icon:
        return ''

    return 'https://cdn.discordapp.com/app-icons/{0.id}/{0.icon}.jpg'.format(self)

AppInfo.icon_url = property(app_info_icon_url)

class Client:
    """Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client`.

    .. _deque: https://docs.python.org/3.4/library/collections.html#collections.deque
    .. _event loop: https://docs.python.org/3/library/asyncio-eventloops.html
    .. _connector: http://aiohttp.readthedocs.org/en/stable/client_reference.html#connectors
    .. _ProxyConnector: http://aiohttp.readthedocs.org/en/stable/client_reference.html#proxyconnector

    Parameters
    ----------
    max_messages : Optional[int]
        The maximum number of messages to store in :attr:`messages`.
        This defaults to 5000. Passing in `None` or a value less than 100
        will use the default instead of the passed in value.
    loop : Optional[event loop]
        The `event loop`_ to use for asynchronous operations. Defaults to ``None``,
        in which case the default event loop is used via ``asyncio.get_event_loop()``.
    connector : aiohttp.BaseConnector
        The `connector`_ to use for connection pooling. Useful for proxies, e.g.
        with a `ProxyConnector`_.
    shard_id : Optional[int]
        Integer starting at 0 and less than shard_count.
    shard_count : Optional[int]
        The total number of shards.
    fetch_offline_members: bool
        Indicates if :func:`on_ready` should be delayed to fetch all offline
        members from the guilds the bot belongs to. If this is ``False``\, then
        no offline members are received and :meth:`request_offline_members`
        must be used to fetch the offline members of the guild.

    Attributes
    -----------
    ws
        The websocket gateway the client is currently connected to. Could be None.
    loop
        The `event loop`_ that the client uses for HTTP requests and websocket operations.
    """
    def __init__(self, *, loop=None, **options):
        self.ws = None
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._listeners = {}
        self.shard_id = options.get('shard_id')
        self.shard_count = options.get('shard_count')

        connector = options.pop('connector', None)
        self.http = HTTPClient(connector, loop=self.loop)

        self.connection = ConnectionState(dispatch=self.dispatch, chunker=self._chunker,
                                          syncer=self._syncer, http=self.http, loop=self.loop, **options)

        self.connection.shard_count = self.shard_count
        self._closed = asyncio.Event(loop=self.loop)
        self._ready = asyncio.Event(loop=self.loop)

        # if VoiceClient.warn_nacl:
        #     VoiceClient.warn_nacl = False
        #     log.warning("PyNaCl is not installed, voice will NOT be supported")

    # internals

    @asyncio.coroutine
    def _syncer(self, guilds):
        yield from self.ws.request_sync(guilds)

    @asyncio.coroutine
    def _chunker(self, guild):
        if hasattr(guild, 'id'):
            guild_id = guild.id
        else:
            guild_id = [s.id for s in guild]

        payload = {
            'op': 8,
            'd': {
                'guild_id': guild_id,
                'query': '',
                'limit': 0
            }
        }

        yield from self.ws.send_as_json(payload)

    def handle_ready(self):
        self._ready.set()

    def _resolve_invite(self, invite):
        if isinstance(invite, Invite) or isinstance(invite, Object):
            return invite.id
        else:
            rx = r'(?:https?\:\/\/)?discord\.gg\/(.+)'
            m = re.match(rx, invite)
            if m:
                return m.group(1)
        return invite

    @property
    def user(self):
        """Optional[:class:`ClientUser`]: Represents the connected client. None if not logged in."""
        return self.connection.user

    @property
    def guilds(self):
        """List[:class:`Guild`]: The guilds that the connected client is a member of."""
        return self.connection.guilds

    @property
    def emojis(self):
        """List[:class:`Emoji`]: The emojis that the connected client has."""
        return self.connection.emojis

    @property
    def private_channels(self):
        """List[:class:`abc.PrivateChannel`]: The private channels that the connected client is participating on."""
        return self.connection.private_channels

    @property
    def messages(self):
        """A deque_ of :class:`Message` that the client has received from all
        guilds and private messages.

        The number of messages stored in this deque is controlled by the
        ``max_messages`` parameter.
        """
        return self.connection.messages

    @property
    def voice_clients(self):
        """List[:class:`VoiceClient`]: Represents a list of voice connections."""
        return self.connection.voice_clients

    def is_ready(self):
        """bool: Specifies if the client's internal cache is ready for use."""
        return self._ready.is_set()

    @asyncio.coroutine
    def _run_event(self, coro, event_name, *args, **kwargs):
        try:
            yield from coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                yield from self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def dispatch(self, event, *args, **kwargs):
        log.debug('Dispatching event {}'.format(event))
        method = 'on_' + event
        handler = 'handle_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as e:
                    future.set_exception(e)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            actual_handler = getattr(self, handler)
        except AttributeError:
            pass
        else:
            actual_handler(*args, **kwargs)

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            compat.create_task(self._run_event(coro, method, *args, **kwargs), loop=self.loop)

    @asyncio.coroutine
    def on_error(self, event_method, *args, **kwargs):
        """|coro|

        The default error handler provided by the client.

        By default this prints to ``sys.stderr`` however it could be
        overridden to have a different implementation.
        Check :func:`discord.on_error` for more details.
        """
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

    @asyncio.coroutine
    def request_offline_members(self, *guilds):
        """|coro|

        Requests previously offline members from the guild to be filled up
        into the :attr:`Guild.members` cache. This function is usually not
        called. It should only be used if you have the ``fetch_offline_members``
        parameter set to ``False``.

        When the client logs on and connects to the websocket, Discord does
        not provide the library with offline members if the number of members
        in the guild is larger than 250. You can check if a guild is large
        if :attr:`Guild.large` is ``True``.

        Parameters
        -----------
        \*guilds
            An argument list of guilds to request offline members for.

        Raises
        -------
        InvalidArgument
            If any guild is unavailable or not large in the collection.
        """
        if any(not g.large or g.unavailable for g in guilds):
            raise InvalidArgument('An unavailable or non-large guild was passed.')

        yield from self.connection.request_offline_members(guilds)

    # login state management

    @asyncio.coroutine
    def login(self, token, *, bot=True):
        """|coro|

        Logs in the client with the specified credentials.

        This function can be used in two different ways.

        Parameters
        -----------
        token: str
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.
        bot: bool
            Keyword argument that specifies if the account logging on is a bot
            token or not.

        Raises
        ------
        LoginFailure
            The wrong credentials are passed.
        HTTPException
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """

        log.info('logging in using static token')
        data = yield from self.http.static_login(token, bot=bot)
        self.connection.is_bot = bot

    @asyncio.coroutine
    def logout(self):
        """|coro|

        Logs out of Discord and closes all connections.
        """
        yield from self.close()

    @asyncio.coroutine
    def _connect(self):
        self.ws = yield from DiscordWebSocket.from_client(self)

        while True:
            try:
                yield from self.ws.poll_event()
            except ResumeWebSocket as e:
                log.info('Got a request to RESUME the websocket.')
                self.ws = yield from DiscordWebSocket.from_client(self, shard_id=self.shard_id,
                                                                        session=self.ws.session_id,
                                                                        sequence=self.ws.sequence,
                                                                        resume=True)

    @asyncio.coroutine
    def connect(self, *, reconnect=True):
        """|coro|

        Creates a websocket connection and lets the websocket listen
        to messages from discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        -----------
        reconnect: bool
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).

        Raises
        -------
        GatewayNotFound
            If the gateway to connect to discord is not found. Usually if this
            is thrown then there is a discord API outage.
        ConnectionClosed
            The websocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        while not self.is_closed():
            try:
                yield from self._connect()
            except (TimeoutError,
                    HTTPException,
                    GatewayNotFound,
                    BlockingIOError,
                    ConnectionError,
                    ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError) as e:

                if not reconnect:
                    yield from self.close()
                    raise

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, no sharding, etc)
                # sometimes, discord sends us 1000 for unknown reasons so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(e, ConnectionClosed):
                    if e.code != 1000:
                        yield from self.close()
                        raise

                retry = backoff.delay()
                log.exception("Attempting a reconnect in {:.2f}s".format(retry))
                yield from asyncio.sleep(retry, loop=self.loop)

    @asyncio.coroutine
    def close(self):
        """|coro|

        Closes the connection to discord.
        """
        if self.is_closed():
            return

        for voice in list(self.voice_clients):
            try:
                yield from voice.disconnect()
            except:
                # if an error happens during disconnects, disregard it.
                pass

            self.connection._remove_voice_client(voice.guild.id)

        if self.ws is not None and self.ws.open:
            yield from self.ws.close()


        yield from self.http.close()
        self._closed.set()
        self._ready.clear()

    @asyncio.coroutine
    def start(self, *args, **kwargs):
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        """

        bot = kwargs.pop('bot', True)
        reconnect = kwargs.pop('reconnect', True)
        yield from self.login(*args, bot=bot)
        yield from self.connect(reconnect=reconnect)

    def run(self, *args, **kwargs):
        """A blocking call that abstracts away the `event loop`_
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(logout())
                # cancel all tasks lingering
            finally:
                loop.close()

        Warning
        --------
        This function must be the last function to call due to the fact that it
        is blocking. That means that registration of events or anything being
        called after this function call will not execute until it returns.
        """

        try:
            self.loop.run_until_complete(self.start(*args, **kwargs))
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.logout())
            pending = asyncio.Task.all_tasks(loop=self.loop)
            gathered = asyncio.gather(*pending, loop=self.loop)
            try:
                gathered.cancel()
                self.loop.run_until_complete(gathered)

                # we want to retrieve any exceptions to make sure that
                # they don't nag us about it being un-retrieved.
                gathered.exception()
            except:
                pass
        finally:
            self.loop.close()

    # properties

    def is_closed(self):
        """bool: Indicates if the websocket connection is closed."""
        return self._closed.is_set()

    # helpers/getters

    @property
    def users(self):
        """Returns a list of all the :class:`User` the bot can see."""
        return list(self.connection._users.values())

    def get_channel(self, id):
        """Returns a :class:`abc.GuildChannel` or :class:`abc.PrivateChannel` with the following ID.

        If not found, returns None.
        """
        return self.connection.get_channel(id)

    def get_guild(self, id):
        """Returns a :class:`Guild` with the given ID. If not found, returns None."""
        return self.connection._get_guild(id)

    def get_user(self, id):
        """Returns a :class:`User` with the given ID. If not found, returns None."""
        return self.connection.get_user(id)

    def get_all_channels(self):
        """A generator that retrieves every :class:`Channel` the client can 'access'.

        This is equivalent to: ::

            for guild in client.guilds:
                for channel in guild.channels:
                    yield channel

        Note
        -----
        Just because you receive a :class:`Channel` does not mean that
        you can communicate in said channel. :meth:`Channel.permissions_for` should
        be used for that.
        """

        for guild in self.guilds:
            for channel in guild.channels:
                yield channel

    def get_all_members(self):
        """Returns a generator with every :class:`Member` the client can see.

        This is equivalent to: ::

            for guild in client.guilds:
                for member in guild.members:
                    yield member

        """
        for guild in self.guilds:
            for member in guild.members:
                yield member

    # listeners/waiters

    @asyncio.coroutine
    def wait_until_ready(self):
        """|coro|

        Waits until the client's internal cache is all ready.
        """
        yield from self._ready.wait()

    def wait_for(self, event, *, check=None, timeout=None):
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto `asyncio.wait_for`_. By default,
        it does not timeout. Note that this does propagate the
        ``asyncio.TimeoutError`` for you in case of timeout and is provided for
        ease of use.

        In case the event returns multiple arguments, a tuple containing those
        arguments is returned instead. Please check the
        :ref:`documentation <discord-api-events>` for a list of events and their
        parameters.

        This function returns the **first event that meets the requirements**.

        .. _asyncio.wait_for: https://docs.python.org/3/library/asyncio-task.html#asyncio.wait_for

        Examples
        ---------

        Waiting for a user reply: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')

                    def check(m):
                        return m.content == 'hello' and m.channel == channel

                    msg = await client.wait_for('message', check=check)
                    await channel.send('Hello {.author}!'.format(msg))

        Parameters
        ------------
        event: str
            The event name, similar to the :ref:`event reference <discord-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[predicate]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[float]
            The number of seconds to wait before timing out and raising
            ``asyncio.TimeoutError``\.

        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        --------
        Any
            Returns no arguments, a single argument, or a tuple of multiple
            arguments that mirrors the parameters passed in the
            :ref:`event reference <discord-api-events>`.
        """

        future = compat.create_future(self.loop)
        if check is None:
            def _check(*args):
                return True
            check = _check

        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout, loop=self.loop)

    # event registration

    def event(self, coro):
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a |corourl|_, if not, :exc:`ClientException` is raised.

        Examples
        ---------

        Using the basic :meth:`event` decorator: ::

            @client.event
            @asyncio.coroutine
            def on_ready():
                print('Ready!')

        Saving characters by using the :meth:`async_event` decorator: ::

            @client.async_event
            def on_ready():
                print('Ready!')

        """

        if not asyncio.iscoroutinefunction(coro):
            raise ClientException('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        log.info('{0.__name__} has successfully been registered as an event'.format(coro))
        return coro

    def async_event(self, coro):
        """A shorthand decorator for ``asyncio.coroutine`` + :meth:`event`."""
        if not asyncio.iscoroutinefunction(coro):
            coro = asyncio.coroutine(coro)

        return self.event(coro)

    @asyncio.coroutine
    def change_presence(self, *, game=None, status=None, afk=False):
        """|coro|

        Changes the client's presence.

        The game parameter is a Game object (not a string) that represents
        a game being played currently.

        Parameters
        ----------
        game: Optional[:class:`Game`]
            The game being played. None if no game is being played.
        status: Optional[:class:`Status`]
            Indicates what status to change to. If None, then
            :attr:`Status.online` is used.
        afk: bool
            Indicates if you are going AFK. This allows the discord
            client to know how to handle push notifications better
            for you in case you are actually idle and not lying.

        Raises
        ------
        InvalidArgument
            If the ``game`` parameter is not :class:`Game` or None.
        """

        if status is None:
            status = 'online'
            status_enum = Status.online
        elif status is Status.offline:
            status = 'invisible'
            status_enum = Status.offline
        else:
            status_enum = status
            status = str(status)

        yield from self.ws.change_presence(game=game, status=status, afk=afk)

        for guild in self.connection.guilds:
            me = guild.me
            if me is None:
                continue

            me.game = game
            me.status = status_enum

    # Invite management

    @asyncio.coroutine
    def get_invite(self, url):
        """|coro|

        Gets a :class:`Invite` from a discord.gg URL or ID.

        Note
        ------
        If the invite is for a guild you have not joined, the guild and channel
        attributes of the returned invite will be :class:`Object` with the names
        patched in.

        Parameters
        -----------
        url : str
            The discord invite ID or URL (must be a discord.gg URL).

        Raises
        -------
        NotFound
            The invite has expired or is invalid.
        HTTPException
            Getting the invite failed.

        Returns
        --------
        :class:`Invite`
            The invite from the URL/ID.
        """

        invite_id = self._resolve_invite(url)
        data = yield from self.http.get_invite(invite_id)
        return Invite.from_incomplete(state=self.connection, data=data)

    @asyncio.coroutine
    def delete_invite(self, invite):
        """|coro|

        Revokes an :class:`Invite`, URL, or ID to an invite.

        The ``invite`` parameter follows the same rules as
        :meth:`accept_invite`.

        Parameters
        ----------
        invite
            The invite to revoke.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke invites.
        NotFound
            The invite is invalid or expired.
        HTTPException
            Revoking the invite failed.
        """

        invite_id = self._resolve_invite(invite)
        yield from self.http.delete_invite(invite_id)

    # Miscellaneous stuff

    @asyncio.coroutine
    def application_info(self):
        """|coro|

        Retrieve's the bot's application information.

        Returns
        --------
        :class:`AppInfo`
            A namedtuple representing the application info.

        Raises
        -------
        HTTPException
            Retrieving the information failed somehow.
        """
        data = yield from self.http.application_info()
        return AppInfo(id=data['id'], name=data['name'],
                       description=data['description'], icon=data['icon'],
                       owner=User(state=self.connection, data=data['owner']))

    @asyncio.coroutine
    def get_user_info(self, user_id):
        """|coro|

        Retrieves a :class:`User` based on their ID. This can only
        be used by bot accounts. You do not have to share any guilds
        with the user to get this information, however many operations
        do require that you do.

        Parameters
        -----------
        user_id: str
            The user's ID to fetch from.

        Returns
        --------
        :class:`User`
            The user you requested.

        Raises
        -------
        NotFound
            A user with this ID does not exist.
        HTTPException
            Fetching the user failed.
        """
        data = yield from self.http.get_user_info(user_id)
        return User(state=self.connection, data=data)

    @asyncio.coroutine
    def get_user_profile(self, user_id):
        """|coro|

        Gets an arbitrary user's profile. This can only be used by non-bot accounts.

        Parameters
        ------------
        user_id: int
            The ID of the user to fetch their profile for.

        Raises
        -------
        Forbidden
            Not allowed to fetch profiles.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`Profile`
            The profile of the user.
        """

        state = self.connection
        data = yield from self.http.get_user_profile(user_id)

        def transform(d):
            return state._get_guild(int(d['id']))

        mutual_guilds = list(filter(None, map(transform, data.get('mutual_guilds', []))))
        return Profile(premium=data['premium'],
                       premium_since=utils.parse_time(data.get('premium_since')),
                       mutual_guilds=mutual_guilds,
                       user=User(data=data['user'], state=state),
                       connected_accounts=data['connected_accounts'])
