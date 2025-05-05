# Telegram Channel Message Editor Bot

This bot monitors Telegram channels and automatically edits messages by applying text filters and converting timestamps between timezones.

## Features

- Monitor multiple Telegram channels
- Apply regex-based text filters to messages and captions
- Convert timestamps between timezones
- Easy configuration via Telegram commands
- Standalone operation without a web interface

## Setup on Termux

### Prerequisites

1. Install [Termux from F-Droid](https://f-droid.org/packages/com.termux/) (not from Google Play Store)
2. Create a Telegram bot using [@BotFather](https://t.me/botfather) and get your bot token

### Installation Options

#### Option 1: Install from GitHub (Recommended)

1. Update Termux packages:
   ```bash
   pkg update && pkg upgrade
   ```

2. Install Git and Python:
   ```bash
   pkg install git python
   ```

3. Clone this repository:
   ```bash
   cd ~
   git clone https://github.com/YourUsername/telegram-channel-editor-bot.git
   cd telegram-channel-editor-bot
   ```

4. Run the installer script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

5. Follow the prompts to configure your bot token and timezones

#### Option 2: Manual Installation

If you downloaded the files directly:

1. Update Termux packages:
   ```bash
   pkg update && pkg upgrade
   ```

2. Install required packages:
   ```bash
   pkg install python
   ```

3. Setup a directory for the bot:
   ```bash
   mkdir -p ~/telegram-editor-bot
   cd ~/telegram-editor-bot
   ```
   
4. Copy all the files to this directory

5. Install Python dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

6. Set up your bot token:
   ```bash
   echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'" >> ~/.bashrc
   echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'" >> ~/.profile
   source ~/.bashrc
   ```

7. Run the test script to verify configuration:
   ```bash
   python test_bot.py
   ```

### Running the Bot

After installation, you can:

1. Test the configuration:
   ```bash
   python test_bot.py
   ```

2. Run the bot:
   ```bash
   python main.py
   ```

3. Run in background (even when Termux is closed):
   ```bash
   ./start-bot.sh
   ```

4. Check if the bot is running:
   ```bash
   ps aux | grep python
   ```

5. View logs:
   ```bash
   cat bot.log
   ```

### Running on a VPS/Server

If you're using a VPS (like Hostinger):

1. Connect to your VPS using SSH
2. Follow the GitHub installation steps above
3. To keep the bot running after you disconnect:
   ```bash
   # Install screen
   apt-get install screen
   
   # Create a screen session
   screen -S telegram-bot
   
   # Run your bot
   cd ~/telegram-channel-editor-bot
   python main.py
   
   # Detach from screen: Ctrl+A followed by D
   ```

4. Reconnect to the bot session later:
   ```bash
   screen -r telegram-bot
   ```

## Bot Commands

Once your bot is running, you can control it with these Telegram commands:

- `/start` - Start the bot and get a welcome message
- `/help` - Show all available commands and usage information
- `/status` - Check the bot's current status
- `/channels` - List all monitored channels
- `/addchannel @channel_name` - Add a channel to monitor
- `/removechannel @channel_name` - Remove a channel from monitoring
- `/filters` - List all active text filters
- `/addfilter pattern replacement` - Add a new text filter
- `/removefilter pattern` - Remove a text filter
- `/testfilter "sample text" pattern` - Test a regex pattern on sample text

## Adding Your Bot to a Channel

1. Add your bot as an administrator to your Telegram channel
2. Give it permission to post and edit messages
3. Send `/addchannel @your_channel_name` to your bot in a direct message
4. The bot will now monitor and edit messages in that channel

## Customizing Text Filters

You can add text filters using regex patterns. For example:

- `/addfilter "(?i)\\b(urgent)\\b" "URGENT"` - Replace "urgent" with "URGENT" (case insensitive)

The bot also includes some pre-configured filters in `config.py` that you can modify.

## Troubleshooting Common Issues

### Command Not Found Errors
If you get command not found errors for `pip` or `python`, use these alternatives:
```bash
python -m pip install -r requirements.txt
```

### Bot Token Not Working
Make sure your bot token is correctly set in both environment and .env file:
```bash
echo $TELEGRAM_BOT_TOKEN  # Should show your token
```

### Timezone Conversion Issues
Verify that both source and target timezones are valid:
```bash
python -c "import pytz; print(pytz.all_timezones)"
```

### Bot Not Running in Background
If the bot stops when you close Termux, make sure to:
1. Use the start-bot.sh script
2. Install Termux:Boot from F-Droid
3. Link the script to ~/.termux/boot/

### Checking the Log File
Always check the log file for errors:
```bash
cat bot.log
```

## Keeping the Bot Running After Termux Closes

To ensure the bot stays running even when Termux is closed:

1. Make sure you've run the installer with "y" for creating a startup script
2. Install Termux:Boot from F-Droid
3. Link the startup script to boot directory:
   ```bash
   mkdir -p ~/.termux/boot
   ln -sf ~/telegram-channel-editor-bot/start-bot.sh ~/.termux/boot/
   ```
4. Grant Termux:Boot the permission to auto-start

## Updating the Bot

When updates are available:

```bash
# If installed from GitHub
cd ~/telegram-channel-editor-bot
git pull

# Restart the bot
pkill -f "python main.py"
./start-bot.sh
```

## Support

If you encounter any issues:
1. Check the bot.log file
2. Make sure your bot has admin permissions in the channel
3. Verify your bot token is set correctly
4. Ensure both Termux and python-telegram-bot are up to date

For more help, create an issue on the GitHub repository.