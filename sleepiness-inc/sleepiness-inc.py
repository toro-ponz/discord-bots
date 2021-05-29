import os
import time
import textwrap

from datetime import timedelta

from discord import Client, MemberCacheFlags, Intents, Status
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
    execution_time_list = [
        '00:00',
        '00:30',
        '01:00',
        '01:30',
        '02:00',
        '02:30',
        '03:00',
        '03:30',
        '04:00',
        '05:00',
        '06:00',
    ]

    """
    not exec disconnect time list.
    format: [%A %H:%M]. 
    """
    exclude_time_list = []

    """
    notify channel name.
    """
    notify_channel_name = os.environ.get('NOTIFY_CHANNEL_NAME', 'bed-room')

    """
    ignore channel names.
    """
    ignore_channel_names = os.environ.get('IGNORE_CHANNEL_NAMES', '').split(',')

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
        self.notify_channel_name = self.__class__.notify_channel_name

        self.sleeping_list_per_guild = {}
        self.execution_time_list_per_guild = {}
        self.exclude_time_list_per_guild = {}

        if (self.logger is None):
            self.logger = Logger(os.environ.get('LOG_LEVEL', 'INFO'))

        self.run(self.token)

    """
    exec when launched a bot.
    """
    async def on_ready(self):
        await self.change_presence(status=Status.online)

        for guild in self.guilds:
            if (self.execution_time_list_per_guild.get(guild.id) is None):
                self.execution_time_list_per_guild[guild.id] = self.__class__.execution_time_list
            
            if (self.exclude_time_list_per_guild.get(guild.id) is None):
                self.exclude_time_list_per_guild[guild.id] = self.__class__.exclude_time_list
            
            notify_channel = self.find_channel(guild, self.notify_channel_name)
            if (notify_channel is not None):
                await notify_channel.send('Hello everyone! I\'m ready.')

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
        now = DateTime.now()
        commands = message.content.split(' ')
        guild = message.guild
        channel = message.channel

        if (commands is None or len(commands) < 2):
            return
        
        if (commands[1] == 'run'):
            for voice_channel in guild.voice_channels:
                await self.disconnect(guild, voice_channel, now)
            return
        
        if (commands[1] == 'add'):
            if (len(commands) < 3):
                await channel.send('time is required.')
                return

            await self.do_add(commands[2], guild, channel)
            return
        
        if (commands[1] == 'remove'):
            if (len(commands) < 3):
                await channel.send('time is required.')
                return

            await self.do_remove(commands[2], guild, channel)
            return
        
        if (commands[1] == 'exclude'):
            if (len(commands) < 3):
                await channel.send('weekday is required.')
                return

            if (len(commands) < 4):
                await channel.send('time is required.')
                return

            await self.do_exclude(commands[2], commands[3], guild, channel)
            return
        
        if (commands[1] == 'include'):
            if (len(commands) < 3):
                await channel.send('weekday is required.')
                return

            if (len(commands) < 4):
                await channel.send('time is required.')
                return

            await self.do_include(commands[2], commands[3], guild, channel)
            return
        
        if (commands[1] == 'list'):
            await self.do_list(guild, channel)
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
    @tasks.loop(seconds=59)
    async def watch(self):
        now = DateTime.now()
        self.logger.debug('started execution disconnect at %s.' % (now))

        await self.check_awake(self.guilds, now)

        for guild in self.guilds:
            self.logger.debug('guild: %s.' % (guild.name))

            if (not await self.is_executable(guild, now)):
                continue

            for voice_channel in guild.voice_channels:
                self.logger.debug('voice_channel: %s.' % (voice_channel.name))
                await self.disconnect(guild, voice_channel, now)
        
        self.logger.debug('finished execution disconnect at %s.' % (now))

    """
    force disconnect all users on voice_channel

    @param guild discord.Guild (required)target guild.
    @param voice_channel discord.VoiceChannel (required)target voice channel.
    @param now datetime.datetime
    """
    async def disconnect(self, guild, voice_channel, now):
        disconnect_members = []
        notify_channel = self.find_channel(guild, self.notify_channel_name)

        if (notify_channel is None):
            self.logger.info('not found notify channel. channel_name = %s.' % (self.notify_channel_name))
            return

        if (voice_channel.name in self.ignore_channel_names):
            self.logger.info('ignore channel. channel_name = %s.' % (voice_channel.name))
            return

        if (len(voice_channel.members) == 0):
            self.logger.debug('voice_channel.member is empty on %s.' % (voice_channel.name))

        for member in voice_channel.members:
            display_name = self.get_user_display_name(member)
            self.logger.debug('voice_channel.member %s on %s.'% (display_name, voice_channel.name))
            disconnect_members.append(member)

        if (len(disconnect_members) != 0):
            await self.notify(notify_channel, 'good night.', disconnect_members)

            time.sleep(10)

            if (await self.is_excludable(guild, now)):
                message = 'It`s %s!\nHave a nice day!' % (now.strftime('%A'))
                await self.notify(notify_channel, message, disconnect_members)
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
    add to execution list.

    @param time string add time string, format: [%H:%M].
    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_add(self, time, guild, channel):
        if (self.execution_time_list_per_guild.get(guild.id) is None):
            self.execution_time_list_per_guild[guild.id] = []

        if (time in self.execution_time_list_per_guild[guild.id]):
            await channel.send('time has allready added to execution time list.')
            return
        
        self.execution_time_list_per_guild[guild.id].append(time)
        self.execution_time_list_per_guild[guild.id].sort()
        await channel.send('time has successfully added.')

    """
    remove from execution list.

    @param time string remove time string, format: [%H:%M].
    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_remove(self, time, guild, channel):
        if (self.execution_time_list_per_guild.get(guild.id) is None):
            self.execution_time_list_per_guild[guild.id] = []

        if (not time in self.execution_time_list_per_guild[guild.id]):
            await channel.send('time was not found in execution time list.')
            return
        
        index = self.execution_time_list_per_guild[guild.id].index(time)
        del self.execution_time_list_per_guild[guild.id][index]
        await channel.send('time has successfully removed.')

    """
    add to exclude list.

    @param weekday string format: [%A].
    @param time string add time string, format: [%H:%M].
    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_exclude(self, weekday, time, guild, channel):
        exclude_time = '%s %s' % (weekday, time)

        if (self.exclude_time_list_per_guild.get(guild.id) is None):
            self.exclude_time_list_per_guild[guild.id] = []

        if (exclude_time in self.exclude_time_list_per_guild[guild.id]):
            await channel.send('exclude time has allready added to exclude time list.')
            return
        
        self.exclude_time_list_per_guild[guild.id].append(exclude_time)
        self.exclude_time_list_per_guild[guild.id].sort()
        await channel.send('exclude time has successfully added.')

    """
    remove from exclude list.

    @param weekday string format: [%A].
    @param time string add time string, format: [%H:%M].
    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_include(self, weekday, time, guild, channel):
        exclude_time = '%s %s' % (weekday, time)

        if (self.exclude_time_list_per_guild.get(guild.id) is None):
            self.exclude_time_list_per_guild[guild.id] = []

        if (not exclude_time in self.exclude_time_list_per_guild[guild.id]):
            await channel.send('exclude time was not found in exclude time list.')
            return

        index = self.exclude_time_list_per_guild[guild.id].index(exclude_time)
        del self.exclude_time_list_per_guild[guild.id][index]
        await channel.send('exclude time has successfully removed.')

    """
    response execution time list.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_list(self, guild, channel):
        text = ''

        if (len(self.execution_time_list_per_guild[guild.id]) > 0):
            text += 'execute:\n'

            for time in self.execution_time_list_per_guild[guild.id]:
                text += '\t%s\n' % (time)

        if (len(self.exclude_time_list_per_guild[guild.id]) > 0):
            text += 'exclude:\n'

            for time in self.exclude_time_list_per_guild[guild.id]:
                text += '\t%s\n' % (time)
        
        await channel.send(text)
    
    """
    response status.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_status(self, guild, channel):
        if (self.sleeping_list_per_guild.get(guild.id) is not None):
            await channel.send('sleepness inc is sleeping until %s.' % (self.sleeping_list_per_guild[guild.id].isoformat()))
            return
        
        await channel.send('sleepness inc is running.')

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

        if (self.sleeping_list_per_guild.get(guild.id) is not None):
            del self.sleeping_list_per_guild[guild.id]

        if (minutes > 120):
            await channel.send('minutes must be less than 120.')
            return

        awake_time = DateTime.now().replace(microsecond=0) + timedelta(minutes=minutes)
        text = 'start sleeping %s minutes. until %s.' % (minutes, awake_time.isoformat())
        await channel.send(text)
        await self.change_presence(status=Status.idle) # fix me.
        self.sleeping_list_per_guild[guild.id] = awake_time

    """
    awake from sleep.

    @param guild discord.Guild
    @param channel discord.Channel
    """
    async def do_awake(self, guild, channel):
        if (self.sleeping_list_per_guild.get(guild.id) is None):
            return

        await channel.send('good morning everyone!')
        del self.sleeping_list_per_guild[guild.id]
        
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
        run                     do good night.
        add <HH:MM>             add time to execution time list. e.g. "00:45".
        remove <HH:MM>          remove time from execution time list. e.g. "01:00".
        exclude <%A> <%H:%M>    add time to exclude time list. e.g. "Sunday 01:00".
        include <%A> <%H:%M>    remove time from exclude time list. e.g. "Monday 02:00".
        list                    list execution time list & exclude time list.
        sleep <minute>          sleep execution for minute.
        awake                   wake up from sleep mode.
        status                  get running status.
        help                    list available commands and some.
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
            if (self.sleeping_list_per_guild.get(guild.id) is None):
                continue

            if (self.sleeping_list_per_guild[guild.id] > now):
                continue

            await self.do_awake(guild, self.find_channel(guild, self.notify_channel_name))

    """
    return is executable.
    
    @param guild discord.Guild
    @param now datetime.datetime
    @return boolean
    """
    async def is_executable(self, guild, now):
        if (self.sleeping_list_per_guild.get(guild.id) is not None):
            self.logger.info('sleeping guild: %s.' % (guild.name))
            return False

        if (self.execution_time_list_per_guild.get(guild.id) is None):
            return False

        if (now.strftime('%H:%M') in self.execution_time_list_per_guild[guild.id]):
            return True

        return False

    """
    return is excludable.
    
    @param guild discord.Guild
    @param now datetime.datetime
    @return boolean
    """
    async def is_excludable(self, guild, now):
        if (now.strftime('%A %H:%M') in self.exclude_time_list_per_guild[guild.id]):
            return True
        
        return False

client = SleepinessInc(os.environ.get('TOKEN', None))
