import os
import textwrap

import openai

from discord import Client, MemberCacheFlags, Intents, Status
from discord.ext import tasks

from utils import Logger, DateTime

openai.api_key = os.environ.get('OPENAI_API_KEY')

"""
OpenAI is a discord bot that based by GPT.
"""
class OpenAI(Client):

    """
    chat history per guild.
    """
    chat_histories = {}

    """
    hour that reset chat histories.
    """
    history_reset_hour = 6

    """
    constructor.

    @param token string (required)discord token.
    @param logger Logger (optional)utils.Logger instance.
    """
    def __init__(self, token, logger=None):
        super().__init__(
            intents = Intents.all(),
            member_cache_flags = MemberCacheFlags.all()
        )

        if (token is None):
            raise Exception('token is required.')

        self.token = token
        self.logger = logger

        if (self.logger is None):
            self.logger = Logger(os.environ.get('LOG_LEVEL', 'INFO'))

        self.logger.info('Application starting.')
        self.run(self.token)

    """
    exec when launched a bot.
    """
    async def on_ready(self):
        self.logger.debug('on_ready')

        await self.change_presence(status=Status.online)

        self.watch.start()

    """
    exec when received an message.

    @param message discord.Message
    """
    async def on_message(self, message):
        self.logger.debug('on_message')

        if (self.find_user_from_list(message.mentions, self.user.name) is None):
            if (self.find_role_from_list(message.role_mentions, self.user.name) is None):
                return

        if (message.author.bot):
            return
        
        await self.command(message)

    """
    exec command.

    @param message discord.Message
    """
    async def command(self, message):
        commands = message.content.split(' ')
        guild = message.guild
        channel = message.channel

        if (commands is None or len(commands) < 2):
            await self.do_help(channel)
            return

        if (commands[1] == 'system'):
            await self.do_system(guild, channel, message.content.split(' ', 2)[2])
            return
        
        if (commands[1] == 'history'):
            await self.do_history(guild, channel)
            return
        
        if (commands[1] == 'reset'):
            await self.do_reset_history(guild, channel)
            return
        
        if (commands[1] == 'help'):
            await self.do_help(channel)
            return

        await self.do_user(guild, channel, message.content.split(' ', 1)[1])

    """
    loop tasks.
    """
    @tasks.loop(hours=1)
    async def watch(self):
        now = DateTime.now()
        self.logger.debug('started watch at %s.' % (now))

        if (now.hour == self.history_reset_hour):
            for guild in self.guilds:
                self.do_reset_history(guild)

    """
    send chat message to openai.

    @param guild discord.Guild
    @param role string role of openai message.
    @param content string content of openai message.
    """
    def do_openai(self, guild, role, content):
        messages = []

        if (self.chat_histories.get(guild.id) is not None):
            messages = self.chat_histories.get(guild.id)

        messages.append({'role': role, 'content': content})

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
        )
        reply = response.choices[0]['message']['content'].strip()

        messages.append({'role': 'assistant', 'content': reply})
        self.chat_histories[guild.id] = messages

        return reply

    """
    send user message to openai.

    @param guild discord.Guild
    @param channel discord.Channel
    @param text string content of chat message.
    """
    async def do_user(self, guild, channel, text):
        self.logger.debug('do_user: guild=%s, channel=%s, text=%s' % (guild.name, channel.name, text))
        reply = self.do_openai(guild, 'user', text)
        self.logger.debug('do_user: reply=%s' % (reply))
        await channel.send(reply)

    """
    send system message to openai.

    @param guild discord.Guild
    @param channel discord.Channel
    @param text string content of chat message.
    """
    async def do_system(self, guild, channel, text):
        self.logger.debug('do_system: guild=%s, channel=%s, text=%s' % (guild.name, channel.name, text))
        reply = self.do_openai(guild, 'system', text)
        self.logger.debug('do_system: reply=%s' % (reply))
        await channel.send(reply)

    """
    get chat histories.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_history(self, guild, channel):
        if (self.chat_histories.get(guild.id) is None or self.chat_histories.get(guild.id) == {}):
            await channel.send('histories are empty.')
            return

        await channel.send('%s' % (self.chat_histories.get(guild.id)))

    """
    reset chat histories.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_reset_history(self, guild, channel):
        self.chat_histories[guild.id] = {}
        self.logger.info('reset chat histories for %s.' % (guild.name))

        if (channel is not None):
            await channel.send('reset history.')

    """
    help.

    @param channel discord.Channel
    """
    async def do_help(self, channel):
        text = textwrap.dedent("""
        ```
        usage: @openai <command> [<args>]
        ---
        <message>         send user message(role=user).
        system <message>  send system message(role=system).
        history           get chat history.
        reset             reset chat history.
        help              list available commands and some.
        ```
        """).strip()

        await channel.send(text)

    """
    find user by user name from user list.

    @param users list[discord.User]
    @param name string search user name.
    @return discord.User or None
    """
    def find_user_from_list(self, users, name):
        for user in users:
            if (user.name == name):
                return user

    """
    find role by role name from role list.

    @param roles list[discord.Role]
    @param name string search role name.
    @return discord.Role or None
    """
    def find_role_from_list(self, roles, name):
        for role in roles:
            if (role.name == name):
                return role


client = OpenAI(os.environ.get('TOKEN', None))
