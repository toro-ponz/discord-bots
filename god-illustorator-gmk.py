import os
import time

from datetime import datetime

from discord import Client, Status
from discord.ext import tasks

from utils import Logger

"""
GodIllustratorGmk is a discord bot that encourage drawing illustration.
"""
class GodIllustratorGmk(Client):

    """
    begin time.
    format: [HH:MM]. 
    """
    beginTime = os.environ.get('GIG_BEGIN_TIME', '21:00')

    """
    end time.
    format: [HH:MM]. 
    """
    endTime = os.environ.get('GIG_END_TIME', '00:00')

    """
    target text channel name.
    """
    channel_name = os.environ.get('GIG_CHANNEL_NAME', 'illustration')

    """
    target role name.
    """
    role_name = os.environ.get('GIG_ROLE_NAME', 'illustrator')

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
        await self.change_presence(status=Status.online)

        self.watch.start()

    """
    .
    """
    @tasks.loop(seconds=30)
    async def watch(self):
        now = datetime.now().strftime('%H:%M')

        if (now != self.__class__.beginTime):
            return

        self.logger.info('started notify at %s.' % (now))
        
        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))
            channel = self.find_channel(guild, channel_name)

            if (channel is None):
                self.logger.info('channel not found by name (%s)' % (channel_name))
                break

            self.notify(channel, 'Draw god illustration, right now.')
        
        self.logger.info('finished notify at %s.' % (now))

        time.sleep(30)

    """
    notify.

    @param channel discord.CHannel (required)notify text channel.
    @param text string (required)notify text.
    """
    async def notify(self, channel, text, role_name):
        message = '<@!%s>\n%s' % (self.__class__.role_name, text)

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

client = GodIllustratorGmk(os.environ.get('GIG_TOKEN', None))
