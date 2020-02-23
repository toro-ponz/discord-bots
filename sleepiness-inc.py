import os
import time

from datetime import datetime

from discord import Client, Status
from discord.ext import tasks

from utils import Logger

"""
SleepinessInc is a discord bot that force disconnect all users in voice channel on weekday midnight.
"""
class SleepinessInc(Client):

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
    def __init__(self, token, logger=None):
        super().__init__()

        if (token is None):
            raise Exception('token is required.')

        self.token = token
        self.logger = logger

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
        await self.change_presence(status=Status.idle)

        self.watch.start()

    """
    check voice channel and force disconnect users.
    """
    @tasks.loop(seconds=30)
    async def watch(self):
        now = datetime.now().strftime('%H:%M')

        if (now not in self.__class__.exectionTimeList):
            return

        self.logger.info('started execution disconnect at %s.' % (now))
        await self.change_presence(status=Status.online)
        
        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))

            for voice_channel in guild.voice_channels:
                self.logger.debug('voice_channel: %s.' % (voice_channel.name))
                await self.disconnect(guild, voice_channel)
        
        await self.change_presence(status=Status.idle)
        self.logger.info('finished execution disconnect at %s.' % (now))

        time.sleep(30)

    """
    force disconnect all users on voice_channel

    @param guild discord.Guild (required)target guild.
    @param voice_channel discord.VoiceChannel (required)target voice channel.
    """
    async def disconnect(self, guild, voice_channel):
        disconnect_members = []

        for member in voice_channel.members:
            disconnect_members.append(member)

        if (len(disconnect_members) != 0):
            await self.notify_disconnect(guild, voice_channel, disconnect_members)

            time.sleep(10)

            for member in disconnect_members:
                display_name = self.get_user_display_name(member)
                self.logger.info('found still connected user %s on %s. force disconnect.' % (display_name, voice_channel.name))
                await member.edit(voice_channel=None)

    """
    notify to disconnected users.

    @param guild discord.Guild (required)disconnected users guild.
    @param voice_channel discord.VoiceChannel (required)disconnected users voice channel.
    @param disconnected_users array[discord.User] (required)disconnected users list.
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
    
    """
    return user guild name or account user name.

    @param user discord.User
    @return string
    """
    def get_user_display_name(self, user):
        if (user.nick is not None):
            return user.nick
        
        return user.name

client = SleepinessInc(os.environ.get('TOKEN', None))
