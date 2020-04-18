package main

import (
	"fmt"
	"log"
	"os"

	"github.com/bwmarrin/discordgo"
)

var (
	token             = os.Getenv("TOKEN")
	notifyChannelName = os.Getenv("NOTIFY_CHANNEL_NAME")
)

func main() {
	discord, err := discordgo.New("Bot " + token)

	if err != nil {
		fmt.Println(err)
		return
	}

	discord.AddHandler(onMessageCreate)
	err = discord.Open()

	if err != nil {
		fmt.Println(err)
		return
	}

	notifyReady(discord)

	<-make(chan bool)
	return
}

func notifyReady(session *discordgo.Session) {
	userGuilds, err := findUserGuilds(session)

	if err != nil {
		fmt.Println("Error getting user guilds: ", err)
		return
	}

	for _, userGuild := range userGuilds {
		channel, err := findChannelByNameFromUserGuild(session, userGuild, notifyChannelName)

		if err != nil {
			fmt.Println("Error getting notify channel: ", err)
			continue
		}

		sendMessage(session, channel, "Hello everyone! I'm ready.")
	}
}

func findUserGuilds(session *discordgo.Session) ([]*discordgo.UserGuild, error) {
	userGuilds, limit, before, after := []*discordgo.UserGuild{}, 100, "", ""

	for {
		limitedUserGuild, err := session.UserGuilds(limit, before, after)

		if err != nil {
			return nil, err
		}

		for _, userGuild := range limitedUserGuild {
			userGuilds = append(userGuilds, userGuild)
			after = userGuild.ID
		}

		if len(limitedUserGuild) < limit || len(limitedUserGuild) == 0 {
			return userGuilds, nil
		}
	}
}

func findChannelByName(session *discordgo.Session, guild *discordgo.Guild, channelName string) (*discordgo.Channel, error) {
	channels, err := session.GuildChannels(guild.ID)

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

func findChannelByNameFromUserGuild(session *discordgo.Session, userGuild *discordgo.UserGuild, channelName string) (*discordgo.Channel, error) {
	channels, err := session.GuildChannels(userGuild.ID)

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

func onMessageCreate(session *discordgo.Session, message *discordgo.MessageCreate) {
	currentUser, err := session.User("@me")
	if err != nil {
		log.Println("Error getting current user: ", err)
		return
	}

	if !containsUser(message.Mentions, currentUser) {
		return
	}

	if currentUser.ID == message.Author.ID {
		return
	}

	channel, err := session.State.Channel(message.ChannelID)
	if err != nil {
		log.Println("Error getting channel: ", err)
		return
	}

	sendMessage(session, channel, "Hello, world!")
}

func sendMessage(session *discordgo.Session, channel *discordgo.Channel, message string) {
	_, err := session.ChannelMessageSend(channel.ID, message)

	if err != nil {
		log.Println("Error sending message: ", err)
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
