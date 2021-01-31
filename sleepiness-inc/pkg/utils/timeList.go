package utils

import (
	"fmt"
)

var (
	executeTimeList = []string{
		// "00:00",
		// "00:30",
		"01:00",
		"01:30",
		"02:00",
		"02:30",
		"03:00",
		"04:00",
		"05:00",
		"06:00",
	}
	excludeTimeList = []string{
		// "Saturday 00:00",
		// "Saturday 00:30",
		"Saturday 01:00",
		"Saturday 01:30",
		"Saturday 02:00",
		"Saturday 02:30",
		"Saturday 03:00",
		// "Sunday 00:00",
		// "Sunday 00:30",
		"Sunday 01:00",
		"Sunday 01:30",
		"Sunday 02:00",
		"Sunday 02:30",
		"Sunday 03:00",
	}
)

type TimeList struct {
	ExecuteTimeList []string
	ExcludeTimeList []string
}

func NewTimeList() *TimeList {
	return &TimeList{
		ExecuteTimeList: executeTimeList,
		ExcludeTimeList: excludeTimeList,
	}
}

func (timeList *TimeList) IsExecutable(time *Time) bool {
	hourAndMinute := fmt.Sprintf("%d:%d", time.Date.Hour(), time.Date.Minute())

	for _, executeTime := range timeList.ExecuteTimeList {
		if executeTime == hourAndMinute {
			return true
		}
	}

	return false
}

func (timeList *TimeList) IsExcluded(time *Time) bool {
	weekdayAndHourAndMinute := fmt.Sprintf("%s %d:%d", time.Date.Weekday(), time.Date.Hour(), time.Date.Minute())

	for _, excludeTime := range timeList.ExcludeTimeList {
		if excludeTime == weekdayAndHourAndMinute {
			return true
		}
	}

	return false
}

func (timeList *TimeList) Add(addTime string) {
	timeList.ExecuteTimeList = append(timeList.ExecuteTimeList, addTime)
}

func (timeList *TimeList) Remove(removeTime string) {
	executeTimeList := []string{}

	for _, executeTime := range timeList.ExecuteTimeList {
		if executeTime != removeTime {
			executeTimeList = append(executeTimeList, executeTime)
		}
	}

	timeList.ExecuteTimeList = executeTimeList
}

func (timeList *TimeList) Include(includeTime string) {
	excludeTimeList := []string{}

	for _, excludeTime := range timeList.ExcludeTimeList {
		if excludeTime != includeTime {
			excludeTimeList = append(excludeTimeList, excludeTime)
		}
	}

	timeList.ExcludeTimeList = excludeTimeList
}

func (timeList *TimeList) Exclude(excludeTime string) {
	timeList.ExcludeTimeList = append(timeList.ExcludeTimeList, excludeTime)
}
