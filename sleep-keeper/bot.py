import os

from datetime import datetime

from discord import Client
from discord.ext import tasks

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

    @param token string [required]discord token.
    """
    def __init__(self, token):
        super().__init__()

        if (token is None):
            raise Exception('token is required.')

        self.token = token

    """
    launch a bot.
    """
    def run(self):
        super().run(self.token)

    """
    exec when launched a bot.
    """
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    """
    exec when recieved a message.

    @param message string recieved message.
    """
    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

    """
    check voice channel and force disconnect users.
    """
    @tasks.loop(seconds=30)
    async def exec(self):
        now = datetime.now().strftime('%H:%M')

        if (now not in self.__class__.exectionTimeList):
            return
        
        self.disconnect()

    """
    force disconnect all users on voice_channel.
    """
    async def disconnect(self):
        for guild in self.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    member.edit(voice_channel=None)

client = SleepKeeper(os.environ.get('TOKEN', None))
client.run()
