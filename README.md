# RWA Protection Bot

Telegram group protection + quiz + advertisement bot.

## Features

- Owner-only controls
- Admin ban limit
- Quiz system
- 30 / 60 second quiz timer
- Automatic advertisements
- Dynamic ad group name and username
- Group name change command
- PDF/photo detection
- SQLite settings storage

## Owner Commands

/start

/setname NAME

/setusername USERNAME

/setad TEXT

/setadgroup CHAT_ID

/adtime 6h

/adtime 12h

/adtime 24h

/adnow

/adstop

/quiztime 30

/quiztime 60

/quiz QUESTION | A | B | C | D | A

/setgroupname NAME

/id

## Railway Variables

BOT_TOKEN=Your BotFather token

OWNER_ID=Your Telegram numeric ID

DEFAULT_AD_INTERVAL_HOURS=24

## Important

The bot needs appropriate Telegram administrator permissions.

For Telegram's forward/save protection, enable the group's Content Protection setting.

If only the owner should delete messages, do not give other admins the Telegram "Delete Messages" permission.
