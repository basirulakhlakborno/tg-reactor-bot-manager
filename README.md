# TG Reactor Bot Manager

A professional, web-based Telegram bot management system that allows you to manage multiple Telegram bots and automatically react to channel posts with mixed emoji reactions.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🤖 **Multi-Bot Management**: Manage multiple Telegram bots from a single admin panel
- 📢 **Channel Monitoring**: Automatically react to posts in specified channels
- 🎭 **Mixed Reactions**: Randomly selects 1-3 emoji reactions from a curated set
- 📱 **All Message Types**: Reacts to text, photos, videos, stickers, and all other message types
- 🔐 **Secure Authentication**: Password-protected admin panel with first-run setup
- 🎨 **Modern UI**: Professional, minimal design with responsive layout
- ⚡ **Auto-Start**: Automatically starts all configured bots on application startup
- 📊 **Real-time Status**: Live dashboard showing bot and channel statistics

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Telegram bot token (get one from [@BotFather](https://t.me/BotFather))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tg-reactor-bot-manager.git
   cd tg-reactor-bot-manager
   ```

2. **Run the application**
   ```bash
   python app.py
   ```
   
   On Windows, you can also use:
   ```bash
   run.bat
   ```

3. **First Run Setup**
   - Open your browser and navigate to `http://localhost:5000`
   - Complete the setup wizard:
     - Install required Python modules (automatic)
     - Create an admin account
   - Log in with your credentials

4. **Add Your First Bot**
   - Click "Add Bot" in the admin panel
   - Enter your bot token from @BotFather
   - Optionally provide a name for your bot
   - Click "Add Bot"

5. **Add Channels to Monitor**
   - Click "Add Channel"
   - Enter the channel ID (e.g., `@mychannel` or `-1001234567890`)
   - Optionally provide a name for the channel
   - Click "Add Channel"

6. **Start Your Bot**
   - Click "Start" next to your bot in the bots list
   - Your bot will now automatically react to all posts in the monitored channels!

## 📖 Usage

### Managing Bots

- **Add Bot**: Click "Add Bot" and provide your bot token
- **Start Bot**: Click the "Start" button next to a bot
- **Stop Bot**: Click the "Stop" button next to a running bot
- **Remove Bot**: Click the "Remove" button to delete a bot
- **Start All**: Click "Start All Bots" to start all configured bots at once
- **Stop All**: Click "Stop All Bots" to stop all running bots

### Managing Channels

- **Add Channel**: Click "Add Channel" and provide the channel ID or username
- **Remove Channel**: Click "Remove" next to a channel to stop monitoring it

### Bot Permissions

For the bot to react to channel posts, it must:
1. Be added as an administrator to the channel
2. Have permission to add reactions to messages

To grant permissions:
1. Go to your channel settings
2. Add your bot as an administrator
3. Enable "Add Reactions" permission

## 🏗️ Project Structure

```
tg-reactor-bot-manager/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── run.bat               # Windows startup script
├── config/
│   └── config.py         # Configuration settings
├── src/
│   ├── api/              # API routes
│   ├── auth/             # Authentication service
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── setup/            # Setup wizard service
│   └── utils/            # Utility functions
├── static/
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
└── templates/            # HTML templates
```

## 🔧 Configuration

### Server Settings

Edit `config/config.py` to customize:
- Server host (default: `0.0.0.0`)
- Server port (default: `5000`)
- Debug mode (default: `False`)

### Environment Variables

You can also configure via environment variables:
- `SERVER_HOST`: Server host address
- `SERVER_PORT`: Server port number
- `FLASK_DEBUG`: Enable debug mode (`true`/`false`)

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.0
- **Bot Library**: pyTelegramBotAPI 4.14.0
- **Frontend**: Vanilla JavaScript, CSS3
- **Data Storage**: JSON files
- **Authentication**: Session-based with password hashing

## 📝 API Endpoints

- `GET /api/bots` - Get all bots
- `POST /api/bots` - Add a new bot
- `DELETE /api/bots/<bot_id>` - Remove a bot
- `POST /api/bots/<bot_id>/start` - Start a bot
- `POST /api/bots/<bot_id>/stop` - Stop a bot
- `POST /api/bots/start-all` - Start all bots
- `POST /api/bots/stop-all` - Stop all bots
- `GET /api/channels` - Get all channels
- `POST /api/channels` - Add a channel
- `DELETE /api/channels/<channel_id>` - Remove a channel
- `GET /api/status` - Get server status

## 🔒 Security

- Passwords are hashed using Werkzeug's secure password hashing
- Session-based authentication
- Bot tokens are masked in API responses
- Full tokens stored securely in encrypted JSON files

## 🐛 Troubleshooting

### Bot Not Reacting to Posts

1. **Check Bot Permissions**: Ensure the bot is an admin with reaction permissions
2. **Verify Channel ID**: Make sure the channel ID is correct (use `@channelname` or numeric ID)
3. **Check Logs**: Review the application logs for error messages
4. **Bot Status**: Verify the bot is running (status should show "Running")

### "Bot token rejected" Error

- Verify your bot token is correct
- Check if the token has been revoked in @BotFather
- Ensure you're using the full token (not a masked version)

### "Conflict: terminated by other getUpdates" Error

- Only one instance of a bot can run at a time
- Stop the bot in other instances or applications
- Restart the bot manager

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Developer

Built by [Basirul Akhlak](https://basirulakhlak.tech/)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/tg-reactor-bot-manager/issues).

## ⭐ Show Your Support

If you find this project helpful, please give it a star on GitHub!

---

**Note**: This project is for educational and personal use. Make sure to comply with Telegram's Terms of Service when using bots.
