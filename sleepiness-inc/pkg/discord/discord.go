package discord

import (
	"errors"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/bwmarrin/discordgo"
	"github.com/toro-ponz/discord-bots/sleepiness-inc/pkg/utils"
)

type Discord struct {
	session  *discordgo.Session
	status   string
	timeList *utils.TimeList
}

var (
	notifyChannelName = os.Getenv("NOTIFY_CHANNEL_NAME")
)

const (
	HelloMessage string = "Hello everyone! I'm ready."
	HelpMessage  string = "```" + `
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
` + "```"
	ActiveStatusMessage   string = "sleepiness inc is running."
	SleepingStatusMessage string = "sleepiness inc is sleeping."
	UnknownStatusMessage  string = "sleepiness inc is unknown."
	SleepMessage          string = "sleepiness inc fall asleep."
	AwakeMessage          string = "sleepiness inc awake!"
	DisconnectMessage     string = "good night."
	HolidayMessage        string = "Today is a holiday!\nHave a nice day!"
	AddedMessage          string = "Added to execute time list."
	RemovedMessage        string = "Removed from execute time list."
	IncludedMessage       string = "Removed from exclude time list."
	ExcludedMessage       string = "Added to exclude time list."
)

// New generate new instance
func New(token string) (*Discord, error) {
	session, err := discordgo.New("Bot " + token)

	if err != nil {
		fmt.Println(err)
		return nil, fmt.Errorf("discordgo.New failed. reason: %s", err)
	}

	discord := Discord{
		session:  session,
		status:   "online",
		timeList: utils.NewTimeList(),
	}

	discord.session.AddHandler(discord.onMessageCreateHandler())

	err = discord.session.Open()
	if err != nil {
		fmt.Println(err)
		return nil, fmt.Errorf("discordgo.session.Open failed. reason: %s", err)
	}

	discord.notify(HelloMessage)

	return &discord, nil
}

// Watch
func (discord *Discord) Watch() {
	discord.disconnect()
}

func (discord *Discord) disconnect() {
	now := utils.Now()

	if !discord.timeList.IsExecutable(now) {
		return
	}

	for _, guild := range discord.session.State.Guilds {
		channel, err := discord.findChannelByNameFromGuild(guild, notifyChannelName)
		if err != nil {
			fmt.Println("Error getting notify channel: ", err)
			continue
		}

		channelVoiceStates := make(map[string][]*discordgo.VoiceState)
		for _, voiceState := range guild.VoiceStates {
			channelVoiceStates[voiceState.ChannelID] = append(channelVoiceStates[voiceState.ChannelID], voiceState)
		}

		mentionsMessage := ""
		for _, voiceStates := range channelVoiceStates {
			for _, voiceState := range voiceStates {
				mentionsMessage += fmt.Sprintf("<@%s>", voiceState.UserID)
			}
			discord.sendMessage(channel, fmt.Sprintf("%s\n%s", mentionsMessage, DisconnectMessage))
		}

		go func(guild *discordgo.Guild, channelVoiceStates map[string][]*discordgo.VoiceState) {
			time.Sleep(10 * time.Second)

			for _, voiceStates := range channelVoiceStates {
				if discord.timeList.IsExcluded(now) {
					discord.sendMessage(channel, HolidayMessage)
					continue
				}

				for _, voiceState := range voiceStates {
					discord.disconnectFromVoiceChannel(guild, voiceState)
				}
			}
		}(guild, channelVoiceStates)
	}
}

func (discord *Discord) forceDisconnect(channel *discordgo.Channel) error {
	for _, guild := range discord.session.State.Guilds {
		if guild.ID != channel.GuildID {
			continue
		}

		channel, err := discord.findChannelByNameFromGuild(guild, notifyChannelName)
		if err != nil {
			return fmt.Errorf("Error getting notify channel. reason: %s ", err)
		}

		channelVoiceStates := make(map[string][]*discordgo.VoiceState)
		for _, voiceState := range guild.VoiceStates {
			channelVoiceStates[voiceState.ChannelID] = append(channelVoiceStates[voiceState.ChannelID], voiceState)
		}

		mentionsMessage := ""
		for _, voiceStates := range channelVoiceStates {
			for _, voiceState := range voiceStates {
				mentionsMessage += fmt.Sprintf("<@%s>", voiceState.UserID)
			}
			discord.sendMessage(channel, fmt.Sprintf("%s\n%s", mentionsMessage, DisconnectMessage))
		}

		go func(guild *discordgo.Guild, channelVoiceStates map[string][]*discordgo.VoiceState) {
			time.Sleep(10 * time.Second)

			for _, voiceStates := range channelVoiceStates {
				for _, voiceState := range voiceStates {
					discord.disconnectFromVoiceChannel(guild, voiceState)
				}
			}
		}(guild, channelVoiceStates)
	}

	return nil
}

func (discord *Discord) disconnectFromVoiceChannel(guild *discordgo.Guild, voiceState *discordgo.VoiceState) {
	err := discord.session.GuildMemberMove(guild.ID, voiceState.UserID, nil)

	if err != nil {
		fmt.Println("Error GuildMemberMove: ", err)
	}
}

func (discord *Discord) notify(message string) {
	for _, guild := range discord.session.State.Guilds {
		channel, err := discord.findChannelByNameFromGuild(guild, notifyChannelName)

		if err != nil {
			fmt.Println("Error getting notify channel: ", err)
			continue
		}

		discord.sendMessage(channel, message)
	}
}

func (discord *Discord) findChannelByName(guild *discordgo.Guild, channelName string) (*discordgo.Channel, error) {
	channels, err := discord.session.GuildChannels(guild.ID)

	if err != nil {
		return nil, err
	}

	for _, channel := range channels {
		if channel.Name == channelName {
			return channel, nil
		}
	}

	return nil, fmt.Errorf("not found %s channel", channelName)
}

func (discord *Discord) findChannelByNameFromGuild(guild *discordgo.Guild, channelName string) (*discordgo.Channel, error) {
	channels, err := discord.session.GuildChannels(guild.ID)

	if err != nil {
		return nil, err
	}

	for _, channel := range channels {
		if channel.Name == channelName {
			return channel, nil
		}
	}

	return nil, fmt.Errorf("not found %s channel", channelName)
}

func (discord *Discord) sendMessage(channel *discordgo.Channel, message string) {
	_, err := discord.session.ChannelMessageSend(channel.ID, message)

	if err != nil {
		log.Println("Error sending message: ", err)
	}
}

func (discord *Discord) echoStatus(channel *discordgo.Channel) error {
	if discord.status == "idle" {
		discord.sendMessage(channel, SleepingStatusMessage)
		return nil
	}

	discord.sendMessage(channel, ActiveStatusMessage)
	return nil
}

func (discord *Discord) isMentioned(message *discordgo.MessageCreate) bool {
	meUser, err := discord.session.User("@me")

	if err != nil {
		log.Println("Error getting current user: ", err)
		return false
	}

	if !containsUser(message.Mentions, meUser) {
		return false
	}

	if meUser.ID == message.Author.ID {
		return false
	}

	return true
}

func (discord *Discord) doList(channel *discordgo.Channel) error {
	message := "execute time list\n```"
	for _, executeTime := range discord.timeList.ExecuteTimeList {
		message += executeTime + "\n"
	}
	message += "```\n"

	message += "exclude time list\n```"
	for _, excludeTime := range discord.timeList.ExcludeTimeList {
		message += excludeTime + "\n"
	}
	message += "```"

	discord.sendMessage(channel, message)

	return nil
}

func (discord *Discord) doAwake() error {
	discord.status = "online"
	discord.notify(SleepMessage)

	return nil
}

func (discord *Discord) doSleep(args []string) error {
	if len(args) < 1 {
		return errors.New("doSleep required 1 argument(minutes: numeric).")
	}

	minutes := args[0]
	minutesDuration, err := time.ParseDuration(minutes + "m")

	if err != nil {
		return errors.New("doSleep minutes is must be numeric.")
	}

	discord.status = "idle"
	discord.notify(SleepMessage)

	go func(minutes time.Duration) {
		time.Sleep(minutes)
		if discord.status == "idle" {
			discord.status = "online"
			discord.notify(AwakeMessage)
		}
	}(minutesDuration)

	return nil
}

func (discord *Discord) doAdd(channel *discordgo.Channel, args []string) error {
	if len(args) < 1 {
		return errors.New("doAdd required 1 argument(time).")
	}

	time := args[0]
	discord.timeList.Add(time)
	discord.sendMessage(channel, AddedMessage)

	return nil
}

func (discord *Discord) doRemove(channel *discordgo.Channel, args []string) error {
	if len(args) < 1 {
		return errors.New("doRemove required 1 argument(time).")
	}

	time := args[0]
	discord.timeList.Remove(time)
	discord.sendMessage(channel, RemovedMessage)

	return nil
}

func (discord *Discord) doInclude(channel *discordgo.Channel, args []string) error {
	if len(args) < 1 {
		return errors.New("doInclude required 1 argument(time).")
	}

	time := args[0]
	discord.timeList.Include(time)
	discord.sendMessage(channel, IncludedMessage)

	return nil
}

func (discord *Discord) doExclude(channel *discordgo.Channel, args []string) error {
	if len(args) < 1 {
		return errors.New("doExclude required 1 argument(time).")
	}

	time := args[0]
	discord.timeList.Exclude(time)
	discord.sendMessage(channel, ExcludedMessage)

	return nil
}

func (discord *Discord) onMessageCreateHandler() func(session *discordgo.Session, message *discordgo.MessageCreate) {
	return func(session *discordgo.Session, message *discordgo.MessageCreate) {
		if !discord.isMentioned(message) {
			return
		}

		channel, err := discord.session.State.Channel(message.ChannelID)
		if err != nil {
			log.Println("Error getting channel: ", err)
			return
		}

		command := getCommand(message)
		args := getArgs(message)

		switch command {
		case CommandNone:
			fallthrough
		case CommandHello:
			discord.sendMessage(channel, HelloMessage)
		case CommandStatus:
			err = discord.echoStatus(channel)
		case CommandRun:
			err = discord.forceDisconnect(channel)
		case CommandAwake:
			err = discord.doAwake()
		case CommandSleep:
			err = discord.doSleep(args)
		case CommandList:
			discord.doList(channel)
		case CommandAdd:
			err = discord.doAdd(channel, args)
		case CommandRemove:
			err = discord.doRemove(channel, args)
		case CommandInclude:
			err = discord.doInclude(channel, args)
		case CommandExclude:
			err = discord.doExclude(channel, args)
		case CommandHelp:
			fallthrough
		default:
			discord.sendMessage(channel, HelpMessage)
		}

		if err != nil {
			log.Printf("command %s failed. reason: %s", command, err)
			discord.sendMessage(channel, fmt.Sprintf("command %s failed. reason: %s", command, err))
			return
		}

		log.Printf("command %s succeeded.", command)
	}
}

func containsUser(users []*discordgo.User, searchUser *discordgo.User) bool {
	for _, user := range users {
		if user.ID == searchUser.ID {
			return true
		}
	}

	return false
}

const (
	CommandNone    Command = "none"
	CommandHello   Command = "hello"
	CommandStatus  Command = "status"
	CommandRun     Command = "run"
	CommandAwake   Command = "awake"
	CommandSleep   Command = "sleep"
	CommandList    Command = "list"
	CommandAdd     Command = "add"
	CommandRemove  Command = "remove"
	CommandInclude Command = "include"
	CommandExclude Command = "exclude"
	CommandHelp    Command = "help"
	CommandUnknown Command = "unknown"
)

type Command string

func getCommand(message *discordgo.MessageCreate) Command {
	splitedMessage := strings.Split(message.Content, " ")

	if len(splitedMessage) < 2 {
		return CommandNone
	}

	rawCommand := splitedMessage[1]

	switch rawCommand {
	case "hello":
		return CommandHello
	case "status":
		return CommandStatus
	case "run":
		return CommandRun
	case "awake":
		return CommandAwake
	case "sleep":
		return CommandSleep
	case "list":
		return CommandList
	case "add":
		return CommandAdd
	case "remove":
		return CommandRemove
	case "exclude":
		return CommandExclude
	case "include":
		return CommandInclude
	case "help":
		return CommandHelp
	}

	return CommandUnknown
}

func getArgs(message *discordgo.MessageCreate) []string {
	splitedMessage := strings.Split(message.Content, " ")

	if len(splitedMessage) < 3 {
		return []string{}
	}

	return splitedMessage[2:]
}
