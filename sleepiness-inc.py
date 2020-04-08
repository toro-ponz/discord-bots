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
        '00:30',
        '01:00',
        '01:30',
        '02:00',
        '02:30',
        '03:00',
        '04:00',
        '05:00',
        '06:00',
    ]

    """
    not exec disconnect time list.
    format: [Weekday HH:MM]. 
    """
    excludeTimeList = [
        'Saturday 00:30',
        'Saturday 01:00',
        'Saturday 01:30',
        'Saturday 02:00',
        'Saturday 02:30',
        'Sunday 00:30',
        'Sunday 01:00',
        'Sunday 01:30',
        'Sunday 02:00',
        'Sunday 02:30',
    ]

    """
    notify channel name.
    """
    notifyChannelName = 'bed-room'

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
        self.exectionTimeList = self.__class__.exectionTimeList
        self.excludeTimeList = self.__class__.excludeTimeList
        self.notifyChannelName = self.__class__.notifyChannelName

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

        self.watch.start()

    """
    check voice channel and force disconnect users.
    """
    @tasks.loop(seconds=30)
    async def watch(self):
        now = datetime.now()

        if (now.strftime('%H:%M') not in self.exectionTimeList):
            return
        
        if (now.second > 31):
            return

        self.logger.info('started execution disconnect at %s.' % (now))
        
        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))

            for voice_channel in guild.voice_channels:
                self.logger.debug('voice_channel: %s.' % (voice_channel.name))
                await self.disconnect(guild, voice_channel)
        
        self.logger.info('finished execution disconnect at %s.' % (now))

    """
    force disconnect all users on voice_channel

    @param guild discord.Guild (required)target guild.
    @param voice_channel discord.VoiceChannel (required)target voice channel.
    """
    async def disconnect(self, guild, voice_channel):
        now = datetime.now()
        disconnect_members = []
        notify_channel = self.find_channel(guild, self.notifyChannelName)

        if (notify_channel is None):
            self.logger.info('not found notify channel. channel_name = ' % (self.notifyChannelName))
            return

        for member in voice_channel.members:
            disconnect_members.append(member)

        if (len(disconnect_members) != 0):
            await self.notify(notify_channel, 'good night.', disconnect_members)

            time.sleep(10)

            if (now.strftime('%A %H:%M') in self.excludeTimeList):
                joke_message = 'It`s %s!\nHave a nice weekend!' % (now.strftime('%A'))
                await self.notify(notify_channel, joke_message, disconnect_members)
                return

            for member in disconnect_members:
                display_name = self.get_user_display_name(member)
                self.logger.info('found still connected user %s on %s. force disconnect.' % (display_name, voice_channel.name))
                await member.edit(voice_channel=None)
    
    """
    notify to users.

    @param channel discord.Channel (required)notify channel.
    @param text string notify text.
    @param users array[discord.User] (optional)users list.
    """
    async def notify(self, channel, text, users = None):
        message = ''

        if (channel is None):
            raise Exception('channel is None.')
            return
        
        if (text is None):
            raise Exception('text is None.')
            return

        if (users is not None):
            for user in users:
                message += '<@%s> ' % (user.id)
            message += '\n'

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
    return user guild name or account user name.

    @param user discord.User
    @return string
    """
    def get_user_display_name(self, user):
        if (user.nick is not None):
            return user.nick
        
        return user.name

client = SleepinessInc(os.environ.get('SI_TOKEN', None))
