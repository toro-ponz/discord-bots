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
            await self.do_openai_chat(guild, channel, 'system', message.content.split(' ', 2)[2])
            return

        if (commands[1] == 'image'):
            await self.do_openai_image(guild, channel, message.content.split(' ', 2)[2])
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

        await self.do_openai_chat(guild, channel, 'user', message.content.split(' ', 1)[1])

    """
    loop tasks.
    """
    @tasks.loop(hours=1)
    async def watch(self):
        now = DateTime.now()
        self.logger.debug('started watch at %s.' % (now))

        if (now.hour == self.history_reset_hour):
            self.reset_all_chat_history()

    """
    send chat message to openai.

    @param guild discord.Guild?
    @param channel discord.Channel or discord.DMChannel
    @param role string role of chat message
    @param text string content of chat message.
    """
    async def do_openai_chat(self, guild, channel, role, text):
        self.logger.info(f'do_openai_chat: guild={self.get_guild_name(guild)}, channel={self.get_channel_name(channel)}, role={role}, text={" ".join(text.splitlines())}')

        messages = self.get_chat_history(guild, channel) or []
        messages.append({'role': role, 'content': text})

        async with channel.typing():
            try:
                response = await openai.ChatCompletion.acreate(
                    model='gpt-3.5-turbo',
                    messages=messages,
                )
                reply = response.choices[0]['message']['content'].strip()
            except Exception as e:
                self.logger.error(f'do_openai_chat: {e}')
                await channel.send(f'Sorry, got an error ({e.__class__}).')
            else:
                messages.append({'role': 'assistant', 'content': reply})
                self.set_chat_history(guild, channel, messages)
                self.logger.info(f'do_openai_chat: guild={self.get_guild_name(guild)}, channel={self.get_channel_name(channel)}, reply={" ".join(reply.splitlines())}')
                await channel.send(reply)

    """
    send image message to openai.

    @param guild discord.Guild?
    @param channel discord.Channel or discord.DMChannel
    @param text string content of chat message.
    """
    async def do_openai_image(self, guild, channel, text):
        self.logger.info(f'do_openai_image: guild={self.get_guild_name(guild)}, channel={self.get_channel_name(channel)}, text={" ".join(text.splitlines())}')

        async with channel.typing():
            try:
                response = await openai.Image.acreate(
                    prompt=text,
                    n=1,
                    size='1024x1024'
                )
                reply = response['data'][0]['url']
            except Exception as e:
                self.logger.error(f'do_openai_image: {e}')
                await channel.send(f'Sorry, got an error ({e.__class__}).')
            else:
                self.logger.info(f'do_openai_image: guild={self.get_guild_name(guild)}, channel={self.get_channel_name(channel)}, reply={" ".join(reply.splitlines())}')
                await channel.send(reply)


    """
    get chat histories.

    @param guild discord.Guild
    @param channel discord.Channel or discord.DMChannel
    """
    async def do_history(self, guild, channel):
        histories = self.get_chat_history(guild, channel)

        if (histories is None):
            await channel.send('histories are empty.')
            return

        await channel.send(histories)

    """
    reset chat histories.

    @param guild discord.Guild
    @param channel discord.Channel or discord.DMChannel
    """
    async def do_reset_history(self, guild, channel):
        self.set_chat_history(guild, channel, None)
        self.logger.debug(f'do_reset_history: guild={self.get_guild_name(guild)}, channel={self.get_channel_name(channel)}')
        await channel.send('reset history.')

    """
    help.

    @param channel discord.Channel or discord.DMChannel
    """
    async def do_help(self, channel):
        text = textwrap.dedent("""
        ```
        usage: @openai <command> [<args>]
        ---
        <message>         send user message(role=user).
        system <message>  send system message(role=system).
        image <message>   generate image by message.
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

    """
    stringfy guild

    @param guild discord.Guild
    @return string
    """
    def get_guild_name(self, guild):
        if (guild is None):
            return 'None'
        
        return guild.name

    """
    stringfy channel

    @param channel discord.Channel or discord.DMChannel
    @return string
    """
    def get_channel_name(self, channel):
        if (channel is None):
            return 'None'
        
        if (hasattr(channel, "name")):
            return channel.name
        
        if (hasattr(channel, "recipient")):
            return channel.recipient.name
        
        return 'None'

    """
    return chat history key

    @param guild discord.Guild
    @param channel discord.Channel or discord.DMChannel
    @return string
    """
    def get_chat_history_key(self, guild, channel):
        if (guild is not None):
            return f'{guild.id}-{channel.id}'
        
        return f'{channel.id}'

    """
    return chat history

    @param guild discord.Guild
    @param channel discord.Channel or discord.DMChannel
    @return array
    """
    def get_chat_history(self, guild, channel):
        key = self.get_chat_history_key(guild, channel)

        return self.chat_histories.get(key)

    """
    set chat history

    @param guild discord.Guild
    @param channel discord.Channel or discord.DMChannel
    @param histories array
    """
    def set_chat_history(self, guild, channel, histories):
        key = self.get_chat_history_key(guild, channel)

        self.chat_histories[key] = histories

    """
    reset all chat history
    """
    def reset_all_chat_history(self):
        self.chat_histories = {}


client = OpenAI(os.environ.get('TOKEN', None))
