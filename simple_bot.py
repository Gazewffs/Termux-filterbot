#!/usr/bin/env python3
"""
Simplified Telegram Channel Message Editor Bot
All-in-one version with minimal dependencies

Usage:
1. Install python-telegram-bot and pytz:
   python -m pip install python-telegram-bot>=20.0 pytz
2. Set your bot token:
   export TELEGRAM_BOT_TOKEN='your_token_here'
3. Run this script:
   python simple_bot.py
"""

import os
import re
import json
import logging
import asyncio
from datetime import datetime
import pytz
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get("7763436231:AAG91yNdCBjEivu4FyHzCTNBEhaZUjhuAqA")
SOURCE_TIMEZONE = "Etc/GMT+2"     # Source timezone of timestamps in messages
TARGET_TIMEZONE = "Asia/Kolkata"   # Target timezone to convert timestamps to
PROCESS_TEXT = True                # Process text messages
PROCESS_CAPTIONS = True            # Process captions in media messages
REPLY_ON_EDIT_FAILURE = True       # Reply with corrected text when editing fails

# Static filters to always apply (regex pattern, replacement)
STATIC_FILTERS = [
    (r'(?i)\b(urgent)\b', 'URGENT'),
    (r'(?i)\b(important)\b', 'IMPORTANT'),
    (r'@Gazew_07', '@BILLIONAIREBOSS101'),
    (r'🚧', '🚀')
]

# File paths
CHANNELS_FILE = "monitored_channels.json"
FILTERS_FILE = "user_filters.json"

# Create files if they don't exist
for file in [CHANNELS_FILE, FILTERS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)

# Filter Manager Functions
def load_filters():
    """Load user-defined filters from the JSON file."""
    if not os.path.exists(FILTERS_FILE):
        save_filters([])
        return []
    
    try:
        with open(FILTERS_FILE, 'r') as f:
            filters = json.load(f)
            return filters
    except Exception as e:
        logger.error(f"Error loading filters: {e}")
        return []

def save_filters(filters_list):
    """Save filters to the JSON file."""
    try:
        with open(FILTERS_FILE, 'w') as f:
            json.dump(filters_list, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving filters: {e}")
        return False

def add_filter(pattern, replacement):
    """Add a new filter pattern and replacement."""
    filters = load_filters()
    
    # Check if filter already exists with same pattern
    for i, (p, _) in enumerate(filters):
        if p == pattern:
            # Update replacement for existing pattern
            filters[i] = (pattern, replacement)
            return save_filters(filters)
    
    # Add new filter
    filters.append((pattern, replacement))
    return save_filters(filters)

def remove_filter(pattern):
    """Remove a filter by its pattern."""
    filters = load_filters()
    initial_count = len(filters)
    
    filters = [f for f in filters if f[0] != pattern]
    
    if len(filters) < initial_count:
        return save_filters(filters)
    
    return False

def list_filters():
    """Return a formatted list of all filters."""
    # Static filters from config
    static_filters = STATIC_FILTERS
    logger.info(f"Static filters from config: {static_filters}")
    
    # User-defined filters from JSON
    user_filters = load_filters()
    logger.info(f"Dynamic filters from user_filters.json: {user_filters}")
    
    # Combine both lists for display
    all_filters = static_filters + user_filters
    logger.info(f"Total filters: {len(all_filters)}")
    
    if not all_filters:
        return "No text filters configured."
    
    result = "📋 *Text Filters:*\n\n"
    result += "*Static filters (from config):*\n"
    
    for i, (pattern, replacement) in enumerate(static_filters, 1):
        result += f"{i}. `{pattern}` → `{replacement}`\n"
    
    if user_filters:
        result += "\n*User-defined filters:*\n"
        for i, (pattern, replacement) in enumerate(user_filters, 1):
            result += f"{i}. `{pattern}` → `{replacement}`\n"
    
    return result

def test_filter(text, pattern):
    """Test a regex pattern on a sample text."""
    try:
        # Compile the pattern
        regex = re.compile(pattern)
        
        # Find all matches
        matches = regex.findall(text)
        
        # Create result message
        result = f"*Pattern:* `{pattern}`\n\n*Text:* {text}\n\n"
        
        if matches:
            result += f"*Matches found:* {len(matches)}\n"
            for i, match in enumerate(matches, 1):
                if isinstance(match, tuple):
                    # If match is a tuple (for capture groups), show each group
                    match_str = ', '.join(match)
                    result += f"{i}. `{match_str}`\n"
                else:
                    result += f"{i}. `{match}`\n"
            
            # Show the text with the pattern applied/replaced
            try:
                replaced_text = regex.sub(r'*\1*', text)
                result += f"\n*With matches highlighted:*\n{replaced_text}"
            except:
                # In case of complex patterns where replacement fails
                pass
        else:
            result += "*No matches found*"
        
        return result
    except re.error as e:
        return f"*Error in regex pattern:* {e}"
    except Exception as e:
        return f"*Error testing filter:* {e}"

def get_all_filters():
    """Get all filters (dynamic and static)."""
    static_filters = STATIC_FILTERS
    user_filters = load_filters()
    return static_filters + user_filters

# Utility Functions
def apply_text_filters(text):
    """Apply text filters to the message text"""
    filters = get_all_filters()
    logger.info(f"Got {len(filters)} filters to apply")
    logger.info(f"Original text: {text}")
    
    modified_text = text
    
    # Apply each filter pattern
    for pattern, replacement in filters:
        logger.info(f"Applying filter: pattern='{pattern}', replacement='{replacement}'")
        
        try:
            text_before = modified_text
            modified_text = re.sub(pattern, replacement, modified_text)
            
            if modified_text != text_before:
                logger.info(f"Text changed: '{text_before}' -> '{modified_text}'")
        except Exception as e:
            logger.error(f"Error applying filter pattern '{pattern}': {e}")
    
    logger.info(f"Final modified text: {modified_text}")
    return modified_text

def convert_timezone(text):
    """
    Find timestamps in the text and convert them from SOURCE_TIMEZONE to TARGET_TIMEZONE
    """
    logger.info(f"Attempting to convert timestamps in: {text}")
    logger.info(f"Source timezone: {SOURCE_TIMEZONE}, Target timezone: {TARGET_TIMEZONE}")
    
    # Define source and target timezone objects
    source_tz = pytz.timezone(SOURCE_TIMEZONE)
    target_tz = pytz.timezone(TARGET_TIMEZONE)
    
    # Various timestamp patterns to match
    # Main pattern: HH:MM:SS DD/MM/YYYY or DD/MM/YYYY HH:MM:SS
    timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?\s+\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?)'
    
    # Additional patterns
    # Just time pattern: HH:MM:SS or HH:MM
    time_pattern_1 = r'(\d{1,2}:\d{2}(?::\d{2})?)'
    
    # Time with emoji pattern: ⏰ HH:MM:SS or ⏰ HH:MM
    time_pattern_2 = r'⏰\s*(\d{1,2}:\d{2}(?::\d{2})?)'
    
    modified_text = text
    
    # Function to convert a timestamp to the target timezone
    def convert_timestamp(match):
        timestamp_str = match.group(1)
        try:
            # Parse the timestamp based on its format
            if '/' in timestamp_str:
                # Has date component
                if timestamp_str.index(':') < timestamp_str.index('/'):
                    # Format: HH:MM:SS DD/MM/YYYY
                    time_part, date_part = timestamp_str.split()
                    dt_format = '%H:%M:%S %d/%m/%Y' if ':' in time_part else '%H:%M %d/%m/%Y'
                else:
                    # Format: DD/MM/YYYY HH:MM:SS
                    date_part, time_part = timestamp_str.split()
                    dt_format = '%d/%m/%Y %H:%M:%S' if ':' in time_part else '%d/%m/%Y %H:%M'
                
                dt = datetime.strptime(timestamp_str, dt_format)
            else:
                # Time only: HH:MM:SS or HH:MM
                time_only = timestamp_str
                today = datetime.now()
                dt_format = '%H:%M:%S' if time_only.count(':') == 2 else '%H:%M'
                
                try:
                    dt = datetime.strptime(f"{today.day}/{today.month}/{today.year} {time_only}", f"%d/%m/%Y {dt_format}")
                except ValueError:
                    # If it's just a time reference without context, just convert the time
                    hours, minutes = map(int, time_only.split(':')[:2])
                    seconds = 0
                    if time_only.count(':') == 2:
                        seconds = int(time_only.split(':')[2])
                    
                    src_time = datetime.now(source_tz).replace(hour=hours, minute=minutes, second=seconds)
                    tgt_time = src_time.astimezone(target_tz)
                    
                    # Format time as HH:MM:SS or HH:MM based on input
                    if time_only.count(':') == 2:
                        return f"{tgt_time.hour:02d}:{tgt_time.minute:02d}:{tgt_time.second:02d}"
                    else:
                        return f"{tgt_time.hour:02d}:{tgt_time.minute:02d}"
            
            # Create datetime with source timezone
            dt_with_tz = source_tz.localize(dt)
            
            # Convert to target timezone
            dt_target = dt_with_tz.astimezone(target_tz)
            
            # Format the converted timestamp to match the original format
            converted_timestamp = dt_target.strftime(dt_format)
            
            logger.info(f"Converted timestamp: '{timestamp_str}' -> '{converted_timestamp}'")
            return converted_timestamp
        
        except Exception as e:
            logger.error(f"Error converting timestamp '{timestamp_str}': {e}")
            return timestamp_str  # If conversion fails, keep the original
    
    # Find and convert timestamps using the main pattern
    timestamp_matches = re.findall(timestamp_pattern, modified_text)
    logger.info(f"Found {len(timestamp_matches)} timestamp pattern matches using main pattern")
    
    for timestamp_str in timestamp_matches:
        try:
            converted = convert_timestamp(re.match(r'(' + re.escape(timestamp_str) + r')', timestamp_str))
            modified_text = modified_text.replace(timestamp_str, converted)
        except Exception as e:
            logger.error(f"Error replacing timestamp '{timestamp_str}': {e}")
    
    # Find and convert time-only patterns
    time_matches_1 = re.findall(time_pattern_1, modified_text)
    logger.info(f"Found {len(time_matches_1)} timestamp matches using additional pattern 1")
    
    for time_str in time_matches_1:
        try:
            converted = convert_timestamp(re.match(r'(' + re.escape(time_str) + r')', time_str))
            modified_text = modified_text.replace(time_str, converted)
        except Exception as e:
            logger.error(f"Error replacing time '{time_str}': {e}")
    
    # Find and convert emoji time patterns
    emoji_time_matches = re.findall(time_pattern_2, modified_text)
    logger.info(f"Found {len(emoji_time_matches)} timestamp matches using additional pattern 2")
    
    for time_str in emoji_time_matches:
        try:
            converted = convert_timestamp(re.match(r'(' + re.escape(time_str) + r')', time_str))
            modified_text = modified_text.replace(time_str, converted)
        except Exception as e:
            logger.error(f"Error replacing emoji time '{time_str}': {e}")
    
    logger.info(f"Total timestamps found: {len(timestamp_matches) + len(time_matches_1) + len(emoji_time_matches)}")
    
    return modified_text

def process_message_text(text):
    """Process a message text by applying text filters and timezone conversion"""
    # First apply text replacements
    filtered_text = apply_text_filters(text)
    
    # Then convert timestamps
    result = convert_timezone(filtered_text)
    
    return result

# Channel Management Functions
def load_channels():
    """Load the list of channels to monitor from a JSON file."""
    if not os.path.exists(CHANNELS_FILE):
        # Create empty list with default channel from env var
        channels = []
        channel_id = os.environ.get("CHANNEL_ID")
        if channel_id:
            channels.append(channel_id)
        save_channels(channels)
        return channels
    
    try:
        with open(CHANNELS_FILE, 'r') as f:
            channels = json.load(f)
            return channels
    except Exception as e:
        logger.error(f"Error loading channels: {e}")
        return []

def save_channels(channels):
    """Save the list of channels to monitor to a JSON file."""
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(channels, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving channels: {e}")
        return False

def add_channel(channel_id):
    """Add a channel to the list of monitored channels."""
    channels = load_channels()
    
    # Normalize channel ID format
    if channel_id.startswith('@'):
        # Keep @ for usernames
        normalized_id = channel_id
    else:
        # Ensure numeric IDs are strings without @
        normalized_id = str(channel_id).replace('@', '')
    
    # Check if channel already exists
    if normalized_id in channels:
        return False, "Channel already in monitoring list."
    
    channels.append(normalized_id)
    if save_channels(channels):
        return True, f"Channel {normalized_id} added to monitoring list."
    else:
        return False, "Failed to save channel."

def remove_channel(channel_id):
    """Remove a channel from the list of monitored channels."""
    channels = load_channels()
    initial_count = len(channels)
    
    # Normalize channel ID for comparison
    normalized_id = str(channel_id).replace('@', '') if not channel_id.startswith('@') else channel_id
    
    # Check both formats (@username and username) for removal
    if normalized_id in channels:
        channels.remove(normalized_id)
    elif f"@{normalized_id}" in channels:
        channels.remove(f"@{normalized_id}")
    elif normalized_id.replace('@', '') in channels:
        channels.remove(normalized_id.replace('@', ''))
    
    if len(channels) < initial_count:
        if save_channels(channels):
            return True, f"Channel {channel_id} removed from monitoring list."
    
    return False, f"Channel {channel_id} not found in monitoring list."

def list_channels():
    """Get a formatted list of all monitored channels."""
    channels = load_channels()
    
    if not channels:
        return "No channels are being monitored."
    
    result = "Monitored channels:\n\n"
    for i, channel in enumerate(channels, 1):
        result += f"{i}. `{channel}`\n"
    
    return result

# Bot Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "👋 Hi! I'm a channel message editor bot. I automatically edit messages in the configured channels.\n\n"
        "I apply text filters and convert timestamps between timezones.\n\n"
        "Add me to your channel as an admin with edit permissions to get started.\n\n"
        "Type /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "🤖 *How to use this bot:*\n\n"
        "1️⃣ Add this bot to your channel as an admin\n"
        "2️⃣ Give it permission to post and edit messages\n"
        "3️⃣ Add your channel to the bot's monitoring list\n"
        "4️⃣ The bot will automatically edit new messages to apply text filters and convert timestamps\n\n"
        "*Channel management commands:*\n"
        "/channels - List all monitored channels\n"
        "/addchannel channel_id - Add a channel to monitor\n"
        "/removechannel channel_id - Remove a channel from monitoring\n\n"
        "*Filter management commands:*\n"
        "/filters - List all current text filters\n"
        "/addfilter pattern replacement - Add a new filter\n"
        "/removefilter pattern - Remove a filter\n"
        "/testfilter sample_text regex_pattern - Test a regex pattern on sample text",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display bot status."""
    
    channels = list_channels().replace('`', '')
    filters_text = list_filters().replace('`', '')
    
    status_text = (
        "📊 *Bot Status*\n\n"
        "✅ Bot is running and monitoring channels\n\n"
        f"*Source Timezone:* {SOURCE_TIMEZONE}\n"
        f"*Target Timezone:* {TARGET_TIMEZONE}\n\n"
        f"*Monitored Channels:*\n{channels}\n\n"
        f"*Active Filters:*\n{filters_text}"
    )
    
    await update.message.reply_text(status_text, parse_mode="Markdown")

async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all current filters."""
    filters_text = list_filters()
    await update.message.reply_text(filters_text, parse_mode="Markdown")

async def add_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new filter."""
    # Check arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /addfilter pattern replacement\n\n"
            "Example: /addfilter (?i)\\b(hello)\\b HELLO\n\n"
            "This would replace all instances of 'hello' (case insensitive) with 'HELLO'"
        )
        return
    
    # Get pattern and replacement
    pattern = context.args[0]
    replacement = ' '.join(context.args[1:])
    
    try:
        # Test if pattern is valid regex
        re.compile(pattern)
        
        # Add the filter
        if add_filter(pattern, replacement):
            await update.message.reply_text(
                f"✅ Filter added successfully!\n\n"
                f"Pattern: `{pattern}`\n"
                f"Replacement: `{replacement}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to add filter.")
    except re.error as e:
        await update.message.reply_text(f"❌ Invalid regex pattern: {e}")

async def remove_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a filter."""
    # Check arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /removefilter pattern\n\n"
            "Example: /removefilter (?i)\\b(hello)\\b"
        )
        return
    
    pattern = context.args[0]
    
    # Remove the filter
    if remove_filter(pattern):
        await update.message.reply_text(f"✅ Filter with pattern `{pattern}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ No filter found with pattern `{pattern}`.", parse_mode="Markdown")

async def test_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test a regex pattern on sample text."""
    # Check arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /testfilter sample_text pattern\n\n"
            "Example: /testfilter \"Hello world\" (?i)\\b(hello)\\b"
        )
        return
    
    sample_text = context.args[0]
    pattern = context.args[1]
    
    try:
        # Test the pattern
        result = test_filter(sample_text, pattern)
        await update.message.reply_text(f"Test result:\n\n{result}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error testing pattern: {e}")

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all monitored channels."""
    channels_text = list_channels()
    await update.message.reply_text(channels_text, parse_mode="Markdown")

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a channel to monitor."""
    # Check arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /addchannel channel_id\n\n"
            "Examples:\n"
            "/addchannel @channelname\n"
            "/addchannel -1001234567890"
        )
        return
    
    channel_id = context.args[0]
    
    # Add the channel
    success, message = add_channel(channel_id)
    if success:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")

async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a channel from monitoring."""
    # Check arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /removechannel channel_id\n\n"
            "Examples:\n"
            "/removechannel @channelname\n"
            "/removechannel -1001234567890"
        )
        return
    
    channel_id = context.args[0]
    
    # Remove the channel
    success, message = remove_channel(channel_id)
    if success:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")

async def process_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process new channel posts."""
    message = update.channel_post
    
    if not message:
        return
    
    # Check if the message is from a monitored channel
    monitored_channels = load_channels()
    channel_match = False
    
    for channel in monitored_channels:
        # Handle both username format (@channel) and numeric ID format
        if channel.startswith('@'):
            # Username format - compare with channel username
            if message.chat.username and message.chat.username.lower() == channel.replace('@', '').lower():
                channel_match = True
                break
        else:
            # Numeric ID format - compare with channel ID
            if message.chat.id and str(message.chat.id) == channel:
                channel_match = True
                break
    
    if not channel_match and monitored_channels:
        logger.info(f"Ignoring message from non-monitored channel: {message.chat.id}")
        return
    
    logger.info(f"Processing message {message.message_id} from channel {message.chat.id}")
    
    try:
        # Process text messages
        if message.text and PROCESS_TEXT:
            original_text = message.text
            logger.info(f"Original text before processing: '{original_text}'")
            
            processed_text = process_message_text(original_text)
            logger.info(f"Processed text after filters and time conversion: '{processed_text}'")
            
            # Only edit if the text has changed
            if processed_text != original_text:
                logger.info(f"Text was changed! Will attempt to edit message {message.message_id}")
                try:
                    # Try to edit message directly
                    await message.edit_text(processed_text, entities=message.entities)
                    logger.info(f"Edited text message {message.message_id}")
                except Exception as edit_error:
                    # If editing fails (e.g., no permission), try alternative method
                    logger.warning(f"Could not edit message directly: {edit_error}")
                    
                    try:
                        # Try using bot API directly with context.bot
                        await context.bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            text=processed_text,
                            entities=message.entities
                        )
                        logger.info(f"Edited text message {message.message_id} using bot API")
                    except Exception as api_error:
                        # If that also fails, log detailed error
                        logger.error(f"Failed to edit message {message.message_id}: {api_error}")
                        
                        # If both editing methods fail, create a reply that shows what the text should be
                        if REPLY_ON_EDIT_FAILURE:
                            try:
                                await context.bot.send_message(
                                    chat_id=message.chat.id,
                                    text=f"*Message text should be:*\n\n{processed_text}",
                                    parse_mode="Markdown",
                                    reply_to_message_id=message.message_id
                                )
                                logger.info(f"Sent reply with corrected text for message {message.message_id}")
                            except Exception as reply_error:
                                logger.error(f"Failed to send reply: {reply_error}")
            else:
                logger.info(f"No changes needed for message {message.message_id}")
        
        # Process captions in media messages
        elif message.caption and PROCESS_CAPTIONS:
            original_caption = message.caption
            processed_caption = process_message_text(original_caption)
            
            # Only edit if the caption has changed
            if processed_caption != original_caption:
                try:
                    # Try to edit caption directly
                    await message.edit_caption(processed_caption, caption_entities=message.caption_entities)
                    logger.info(f"Edited caption in message {message.message_id}")
                except Exception as edit_error:
                    # If editing fails, try alternative method
                    logger.warning(f"Could not edit caption directly: {edit_error}")
                    
                    try:
                        # Try using bot API directly
                        await context.bot.edit_message_caption(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            caption=processed_caption,
                            caption_entities=message.caption_entities
                        )
                        logger.info(f"Edited caption in message {message.message_id} using bot API")
                    except Exception as api_error:
                        # If that also fails, log detailed error
                        logger.error(f"Failed to edit caption in message {message.message_id}: {api_error}")
                        
                        # If both editing methods fail, create a reply that shows what the caption should be
                        if REPLY_ON_EDIT_FAILURE:
                            try:
                                await context.bot.send_message(
                                    chat_id=message.chat.id,
                                    text=f"*Caption should be:*\n\n{processed_caption}",
                                    parse_mode="Markdown",
                                    reply_to_message_id=message.message_id
                                )
                                logger.info(f"Sent reply with corrected caption for message {message.message_id}")
                            except Exception as reply_error:
                                logger.error(f"Failed to send reply: {reply_error}")
                
    except Exception as e:
        logger.error(f"Error processing message {message.message_id}: {e}")

async def start_bot_async():
    """Start the Telegram bot asynchronously."""
    if not BOT_TOKEN:
        logger.error("No bot token provided! Please set the TELEGRAM_BOT_TOKEN environment variable.")
        print("ERROR: Bot token not found! Please set the TELEGRAM_BOT_TOKEN environment variable.")
        print("Example: export TELEGRAM_BOT_TOKEN='your_token_here'")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("filters", filters_command))
    application.add_handler(CommandHandler("addfilter", add_filter_command))
    application.add_handler(CommandHandler("removefilter", remove_filter_command))
    application.add_handler(CommandHandler("testfilter", test_filter_command))
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("addchannel", add_channel_command))
    application.add_handler(CommandHandler("removechannel", remove_channel_command))
    
    # Register message handler for channel posts
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, process_channel_post))
    
    # Start the bot
    logger.info("Starting bot...")
    print("Starting Telegram Channel Message Editor Bot...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Bot started and polling")
    print("Bot is running and polling for updates!")
    print(f"Source Timezone: {SOURCE_TIMEZONE}")
    print(f"Target Timezone: {TARGET_TIMEZONE}")
    print("Use Ctrl+C to stop the bot")
    
    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopping...")
        print("Stopping bot...")
    finally:
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped")
        print("Bot stopped")

def main():
    """Main function to start the bot."""
    try:
        print("Telegram Channel Message Editor Bot (Simple Version)")
        print("=================================================")
        print("")
        if not BOT_TOKEN:
            print("No bot token found in environment!")
            print("Please enter your Telegram Bot Token (from @BotFather):")
            token = input("> ")
            if token:
                os.environ["TELEGRAM_BOT_TOKEN"] = token
                print("Token set for this session.")
                print("To avoid entering the token each time, set it permanently:")
                print("export TELEGRAM_BOT_TOKEN='your_token_here'")
                print("")
        
        asyncio.run(start_bot_async())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
        print("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
