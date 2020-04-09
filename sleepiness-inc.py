import os
import time
import textwrap

from datetime import timedelta

from discord import Client, Status
from discord.ext import tasks

from utils import Logger, DateTime

"""
SleepinessInc is a discord bot that force disconnect all users in voice channel on weekday midnight.
"""
class SleepinessInc(Client):

    """
    exec disconnect time list.
    format: [HH:MM]. 
    """
    exection_time_list = [
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
    exclude_time_tist = [
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
    notify_channel_name = 'bed-room'

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
        self.exection_time_list = self.__class__.exection_time_list
        self.exclude_time_tist = self.__class__.exclude_time_tist
        self.notify_channel_name = self.__class__.notify_channel_name

        self.sleeping_list = {}

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
    exec when received an message.

    @param message discord.Message
    """
    async def on_message(self, message):
        if (self.find_user_from_list(message.mentions, self.user.name) is None):
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
            return
        
        if (commands[1] == 'run'):
            for voice_channel in guild.voice_channels:
                await self.disconnect(guild, voice_channel)
            return
        
        if (commands[1] == 'list'):
            await self.do_list(channel)
            return
        
        if (commands[1] == 'sleep'):
            if (len(commands) < 3):
                await channel.send('minutes is required.')
                return

            await self.do_sleep(int(commands[2]), guild, channel)
            return
        
        if (commands[1] == 'awake'):
            await self.do_awake(guild, channel)
            return

        if (commands[1] == 'status'):
            await self.do_status(guild, channel)
            return

        await self.do_help(channel)

    """
    check voice channel and force disconnect users.
    """
    @tasks.loop(seconds=30)
    async def watch(self):
        now = DateTime.now()

        if (not await self.check_awake(self.guilds, now)):
            return

        if (now.strftime('%H:%M') not in self.exection_time_list):
            return

        if (now.second > 31):
            return

        self.logger.info('started execution disconnect at %s.' % (now))
        
        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))

            if (self.sleeping_list.get(guild.id) is not None):
                self.logger.info('sleeping guild: %s.' % (guild.name))
                return

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
        now = DateTime.now()
        disconnect_members = []
        notify_channel = self.find_channel(guild, self.notify_channel_name)

        if (notify_channel is None):
            self.logger.info('not found notify channel. channel_name = ' % (self.notify_channel_name))
            return

        for member in voice_channel.members:
            disconnect_members.append(member)

        if (len(disconnect_members) != 0):
            await self.notify(notify_channel, 'good night.', disconnect_members)

            time.sleep(10)

            if (now.strftime('%A %H:%M') in self.exclude_time_tist):
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
    @param users list[discord.User] (optional)users list.
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
    return user guild name or account user name.

    @param user discord.User
    @return string
    """
    def get_user_display_name(self, user):
        if (user.nick is not None):
            return user.nick
        
        return user.name
    
    """
    response exection time list.

    @param channel discord.Channel
    """
    async def do_list(self, channel):
        text = ''

        if (len(self.exection_time_list) > 0):
            text += 'execute:\n'

            for time in self.exection_time_list:
                text += '\t%s\n' % (time)

        if (len(self.exclude_time_tist) > 0):
            text += 'execlude:\n'

            for time in self.exclude_time_tist:
                text += '\t%s\n' % (time)
        
        await channel.send(text)
    
    """
    response status.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_status(self, guild, channel):
        if (self.sleeping_list.get(guild.id) is not None):
            await channel.send('sleepness inc is sleeping until %s.' % (self.sleeping_list[guild.id].isoformat()))
            return
        
        await channel.send('sleepness inc is ruuning.')

    """
    sleep.

    @param minutes int sleep minutes.
    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_sleep(self, minutes, guild, channel):
        if (minutes < 1):
            await channel.send('minutes must be greater than or equal 1.')
            return

        if (self.sleeping_list.get(guild.id) is not None):
            del self.sleeping_list[guild.id]

        if (minutes > 120):
            await channel.send('minutes must be less than 120.')
            return

        awake_time = DateTime.now().replace(microsecond=0) + timedelta(minutes=minutes)
        text = 'start sleeping %s minutes. until %s.' % (minutes, awake_time.isoformat())
        await channel.send(text)
        await self.change_presence(status=Status.idle) # fix me.
        self.sleeping_list[guild.id] = awake_time

    """
    awake from sleep.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_awake(self, guild, channel):
        if (self.sleeping_list.get(guild.id) is None):
            return

        await channel.send('good morning everyone!')
        del self.sleeping_list[guild.id]
        
        await self.change_presence(status=Status.online) # fix me.

    """
    help.

    @param channel discord.Channel
    """
    async def do_help(self, channel):
        text = textwrap.dedent("""
        ```
        usage: @sleepness-inc <command> [<args>]
        ---
        run               do good night.
        list              list exection time list & exclude time list.
        sleep <minute>    sleep exection for minute.
        awake             wake up from sleep mode.
        status            get running status.
        help              list available commands and some.
        ```
        """).strip()

        await channel.send(text)

    """
    check awake.
    
    @param guilds list[discord.Guild]
    @param now datetime.datetime
    """
    async def check_awake(self, guilds, now):
        for guild in guilds:
            if (self.sleeping_list.get(guild.id) is None):
                continue

            if (self.sleeping_list[guild.id] > now):
                continue

            await self.do_awake(guild, self.find_channel(guild, self.notify_channel_name))

client = SleepinessInc(os.environ.get('SI_TOKEN', None))
