package main

import (
	"fmt"
	"os"
	"time"

	"github.com/toro-ponz/discord-bots/sleepiness-inc/pkg/discord"
)

var (
	token = os.Getenv("TOKEN")
)

func main() {
	discord, err := discord.New(token)

	if err != nil {
		fmt.Println(err)
		panic(err)
	}

	go watch(discord)

	<-make(chan bool)
}

func watch(discord *discord.Discord) {
	for {
		time.Sleep(59 * time.Second)

		discord.Watch()
	}
}
