import os

from datetime import datetime

from discord import Client, Status
from discord.ext import tasks

from utils import Logger

"""
SleepKeeper is a discord bot that force disconnect all users in voice channel on weekday midnight.
"""
class SleepKeeper(Client):

    """
    exec disconnect time list.
    format: [HH:MM]. 
    """
    exectionTimeList = [
        '01:00',
        '02:00',
        '03:00',
        '04:00',
        '05:00',
        '06:00',
    ]

    """
    constructor.

    @param token string (required)discord token.
    @param logger Logger (optional)utils.Logger instance.
    """
    def __init__(self, token, logger = Logger('INFO')):
        super().__init__()

        if (token is None):
            raise Exception('token is required.')

        self.token = token
        self.logger = logger

    """
    launch a bot.
    """
    def run(self):
        super().run(self.token)

    """
    exec when launched a bot.
    """
    async def on_ready(self):
        await self.change_presence(status=Status.offline)

        self.exec.start()

    """
    check voice channel and force disconnect users.
    """
    @tasks.loop(seconds=30)
    async def exec(self):
        now = datetime.now().strftime('%H:%M')

        if (now not in self.__class__.exectionTimeList):
            return

        self.logger.info('exec disconnect at %s.' % (now))
        
        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))

            for voice_channel in guild.voice_channels:
                self.logger.debug('voice_channel: %s.' % (voice_channel.name))
                await self.disconnect(guild, voice_channel)

    """
    force disconnect all users from voice_channel

    @param guild discord.Guild (required)target guild.
    @param voice_channel discord.VoiceChannel (required)target voice channel.
    """
    async def disconnect(self, guild, voice_channel):
        disconnect_users = []

        for member in voice_channel.members:
            username = member.name

            if (member.nick is not None):
                username = member.nick

            self.logger.info('found still connected user %s on %s. force disconnect.' % (username, voice_channel.name))
            disconnect_users.append(member)

        if (len(disconnect_users) != 0):
            await self.change_presence(status=Status.online)

            for user in disconnect_users:
                await member.edit(voice_channel=None)
            
            await self.notify_disconnect(guild, voice_channel, disconnect_users)
            await self.change_presence(status=Status.offline)

    """
    notify to disconnected users.

    @param guild discord.Guild (required)disconnected users guild.
    @param voice_channel discord.VoiceChannel (required)disconnected users voice channel.
    @param disconnected_users array[discord.Member] (required)disconnected users list.
    """
    async def notify_disconnect(self, guild, voice_channel, disconnected_users):
        message = ''
        channel_name = voice_channel.name.lower()
        channel = self.find_channel(guild, channel_name)

        if (channel is None):
            self.logger.info('channel not found by name (%s)' % (channel_name))
            return

        for user in disconnected_users:
            message += '<@%s> ' % (user.id)

        message += '\ngood night.'

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

logger = Logger(os.environ.get('LOG_LEVEL', 'INFO'))

client = SleepKeeper(os.environ.get('TOKEN', None), logger)
client.run()
