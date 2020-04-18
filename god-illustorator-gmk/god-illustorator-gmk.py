import os
import random
import time

from discord import Client, Status
from discord.ext import tasks

from utils import Logger, DateTime

"""
GodIllustratorGmk is a discord bot that encourage drawing illustration.
"""
class GodIllustratorGmk(Client):

    """
    begin time.
    format: [HH:MM]. 
    """
    beginTime = os.environ.get('BEGIN_TIME', '21:00')

    """
    end time.
    format: [HH:MM]. 
    """
    endTime = os.environ.get('END_TIME', '00:00')

    """
    notify channel name.
    """
    notify_channel_name = os.environ.get('NOTIFY_CHANNEL_NAME', 'illustration')

    """
    target role name.
    """
    role_name = os.environ.get('ROLE_NAME', 'Illustrator')

    """
    reply message list.
    """
    reply_message_list = [
        'つべこべ言わずに絵描け',
        'お前がそうやって御託を並べている間にも神絵師は努力している',
        '今日は休め',
        '左右反転をこまめにしろ',
        '色塗って誤魔化す前にちゃんと線画描け',
    ]

    """
    constructor.

    @param token string (required)discord token.
    @param logger Logger (optional)utils.Logger instance.
    """
    def __init__(self, token, logger=None):
        super().__init__()

        if (token is None):
            raise Exception('token is required.')

        self.token = token
        self.logger = logger
        self.notify_channel_name = self.__class__.notify_channel_name

        if (self.logger is None):
            self.logger = Logger(os.environ.get('LOG_LEVEL', 'INFO'))

        self.run()

    """
    launch a bot.
    """
    def run(self):
        super().run(self.token)

    """
    exec when launched a bot.
    """
    async def on_ready(self):
        await self.change_presence(status=Status.online)

        for guild in self.guilds:
            notify_channel = self.find_channel(guild, self.notify_channel_name)
            if (notify_channel is not None):
                await notify_channel.send('Hello everyone! I\'m ready.')

        # self.watch.start()

    """
    received an message.
    """
    async def on_message(self, message):
        if (self.find_user_from_list(message.mentions, self.user.name) is None):
            return 

        if (message.author.bot):
            return
        
        text = '<@%s>\n%s' % (message.author.id, random.choice(self.__class__.reply_message_list))

        await message.channel.send(text)

    """
    .
    """
    @tasks.loop(seconds=86400)
    async def watch(self):
        now = DateTime.now().strftime('%H:%M')

        if (now != self.__class__.beginTime):
            return

        self.logger.info('started notify at %s.' % (now))
        
        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))

            channel_name = self.__class__.channel_name
            channel = self.find_channel(guild, channel_name)

            if (channel is None):
                self.logger.error('channel not found by name (%s)' % (channel_name))
                break

            role_name = self.__class__.role_name
            role = self.find_role(guild, role_name)

            if (role is None):
                self.logger.error('role not found by name (%s)' % (role_name))
                break

            await self.notify(channel, 'ワイが神絵師や！', role)
        
        self.logger.info('finished notify at %s.' % (now))

    """
    notify.

    @param channel discord.Channel (required)notify text channel.
    @param text string (required)notify text.
    @param role discord.Role (optional)target mention role.
    """
    async def notify(self, channel, text, role=None):
        message = ''

        if (role is not None):
            message += '<@&%s>\n' % (role.id)

        message += text

        await channel.send(message)
    
    """
    find channel by channel name from guild.

    @param guild discord.Guild
    @param name string search channel name.
    @return discord.Channel or None
    """
    def find_channel(self, guild, name):
        for channel in guild.channels:
            if (channel.name == name):
                return channel
        
        return None
    
    """
    find role by role name from guild.

    @param guild discord.Guild
    @param name string search role name.
    @return discord.Role or None
    """
    def find_role(self, guild, name):
        for role in guild.roles:
            if (role.name == name):
                return role
        
        return None

    """
    find user by user name from user list.

    @param users array[discord.User]
    @param name string search user name.
    @return discord.User or None
    """
    def find_user_from_list(self, users, name):
        for user in users:
            if (user.name == name):
                return user
        
        return None

client = GodIllustratorGmk(os.environ.get('TOKEN', None))
