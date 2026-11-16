# Dyno-Style Discord Bot

A moderation/utility bot with slash commands: kick, ban, timeout, warn, nuke, auto-mod, reaction roles, and logging.

## Setup

### 1. Create the bot on Discord
1. Go to https://discord.com/developers/applications → **New Application**
2. Go to the **Bot** tab → **Add Bot** → copy the token
3. Under **Privileged Gateway Intents**, enable:
   - Server Members Intent
   - Message Content Intent
4. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: Kick Members, Ban Members, Moderate Members, Manage Channels, Manage Roles, Manage Messages, Send Messages, Read Message History
5. Copy the generated URL and open it to invite the bot to your test server

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
(If you get an externally-managed-environment error, use a virtual environment: `python -m venv venv && source venv/bin/activate` first.)

### 3. Set your token
Copy `.env.example` to `.env` and paste your bot token in:
```bash
cp .env.example .env
```
Then edit `.env` so it reads `DISCORD_TOKEN=your_actual_token`.

### 4. Run it
```bash
python main.py
```
You should see `Logged in as YourBot#1234` and `Synced N slash command(s)`.

## Commands

| Command | Description | Permission needed |
|---|---|---|
| `/kick` | Kick a member | Kick Members |
| `/ban` | Ban a member | Ban Members |
| `/timeout` | Timeout a member for N minutes | Moderate Members |
| `/warn` | Warn a member (saved to DB) | Moderate Members |
| `/warnings` | View a member's warnings | — |
| `/clearwarns` | Clear a member's warnings | Moderate Members |
| `/nuke` | Clear a channel (asks for confirmation) | Manage Channels |
| `/setmodlog` | Set the channel for mod logs | Administrator |
| `/automod` | Enable/disable auto-mod | Administrator |
| `/reactionrole` | Bind an emoji reaction to a role | Manage Roles |

## Project structure
```
discordbot/
├── main.py              # entrypoint, loads cogs, syncs slash commands
├── requirements.txt
├── .env.example
├── database.db          # created automatically on first run
├── cogs/
│   ├── moderation.py     # kick/ban/timeout/warn/nuke
│   ├── automod.py        # spam + invite link filtering
│   ├── roles.py          # reaction roles
│   └── logging_cog.py    # message edit/delete + join/leave logs
└── utils/
    └── db.py             # SQLite helper functions
```

## Notes / gotchas
- Slash commands can take up to an hour to show up globally the *first* time; for instant testing, sync per-guild instead (ask me if you want that swapped in).
- The bot needs a role **above** any role it tries to assign/remove, and above members it kicks/bans/times out.
- `automod.py` has a tiny placeholder `BANNED_WORDS` set — expand it with real words for your server.
- `/nuke` deletes and recreates the channel — it's irreversible, hence the confirmation button.

## Next steps to extend this
- Per-server custom prefix / settings command
- A `/setmuterole` + a real "mute" fallback for servers without native timeout permission needs
- Pagination for `/warnings` if a user has more than 10
- Deploy to Railway or a small VPS for 24/7 uptime
