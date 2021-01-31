package utils

import (
	"os"
	"time"
)

var (
	timezone = os.Getenv("TZ")
)

type Time struct {
	Date time.Time
}

func Now() *Time {
	loc, err := time.LoadLocation(timezone)

	if err != nil {
		loc = time.FixedZone(timezone, 9*60*60)
	}

	time.Local = loc

	return &Time{
		Date: time.Now(),
	}
}
