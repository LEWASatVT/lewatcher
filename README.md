# lewatcher
Notifications based on LEWAS live data

# Information

LEWatcher is a script which runs every 60 seconds and keeps an eye on the latest data. If more than X samples in the last Y minutes are above or below certain thresholds, the script will send IRC and/or email notifications. If there has been an event within the last Z minutes, the script will not send notifications (and assume that the event is part of the previous event).

LEWatcher is configured via an .ini-style configuration file, and each instance can accept a number of different trigger conditions. The configuration file is hardcoded as ./config because there are plans to replace this configuration file with a database and web management interface. With the current code, "interval" should always be set to a lesser value than "reset" (setting reset to less than interval wouldn’t make much sense and may cause notification spam if a sensor stops reporting during an event).
