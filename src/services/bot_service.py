"""Bot management service."""

import logging
import threading
import random
import requests
import time
from typing import Dict, Optional
from datetime import datetime

import telebot
from telebot.apihelper import ApiTelegramException

from ..models.bot import Bot, Channel
from .data_service import DataService

logger = logging.getLogger(__name__)


class BotService:
    """Service for managing Telegram bots."""
    
    def __init__(self, data_service: Optional[DataService] = None):
        """
        Initialize bot service.
        
        Args:
            data_service: Optional data service instance
        """
        self.data_service = data_service or DataService()
        self.bots: Dict[str, Bot] = {}
        self.channels: Dict[str, Channel] = {}
        self.running_bots: Dict[str, telebot.TeleBot] = {}
        self._load_data()
    
    def _load_data(self):
        """Load bots and channels from data service."""
        data = self.data_service.load_data()
        
        # Load bots
        for bot_id, bot_data in data.get('bots', {}).items():
            try:
                self.bots[bot_id] = Bot.from_dict(bot_data)
            except Exception as e:
                logger.error(f"Error loading bot {bot_id}: {e}")
        
        # Load channels
        for channel_id, channel_data in data.get('channels', {}).items():
            try:
                self.channels[channel_id] = Channel.from_dict(channel_data)
            except Exception as e:
                logger.error(f"Error loading channel {channel_id}: {e}")
        
        # Sync state: reset is_running for bots not actually running (after server restart)
        # Since running_bots is empty on startup, any bot with is_running=True should be reset
        state_changed = False
        for bot_id, bot in self.bots.items():
            if bot.is_running and bot_id not in self.running_bots:
                bot.is_running = False
                state_changed = True
                logger.info(f"Reset is_running flag for bot {bot_id} (not in running_bots)")
        
        # Save the corrected state if any changes were made
        if state_changed:
            self._save_data()
        
        logger.info(f"Loaded {len(self.bots)} bots and {len(self.channels)} channels")
    
    def _save_data(self):
        """Save bots and channels to data service."""
        # Save full tokens to data file (not masked)
        bots_dict = {}
        for bot_id, bot in self.bots.items():
            bot_data = {
                'id': bot.id,
                'token': bot.token,  # Save full token, not masked
                'name': bot.name,
                'is_running': bot.is_running,
                'created_at': bot.created_at
            }
            bots_dict[bot_id] = bot_data
        
        channels_dict = {channel_id: channel.to_dict() for channel_id, channel in self.channels.items()}
        self.data_service.save_data(bots_dict, channels_dict)
    
    def add_bot(self, token: str, name: str) -> bool:
        """
        Add a new bot.
        
        Args:
            token: Bot token from BotFather
            name: Bot name
            
        Returns:
            True if successful, False otherwise
        """
        if not token or len(token) < 40:
            logger.warning("Invalid bot token provided")
            return False
        
        bot_id = f"bot_{int(datetime.now().timestamp() * 1000)}"
        bot = Bot(
            id=bot_id,
            token=token,
            name=name or f"Bot {len(self.bots) + 1}"
        )
        
        self.bots[bot_id] = bot
        self._save_data()
        logger.info(f"Added bot: {bot.name} ({bot_id})")
        return True
    
    def remove_bot(self, bot_id: str) -> bool:
        """
        Remove a bot.
        
        Args:
            bot_id: Bot ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id in self.running_bots:
            self.stop_bot(bot_id)
        
        if bot_id in self.bots:
            bot_name = self.bots[bot_id].name
            del self.bots[bot_id]
            self._save_data()
            logger.info(f"Removed bot: {bot_name} ({bot_id})")
            return True
        
        return False
    
    def add_channel(self, channel_id: str, name: str) -> bool:
        """
        Add a new channel.
        
        Args:
            channel_id: Channel ID or username
            name: Channel name
            
        Returns:
            True if successful, False otherwise
        """
        if not channel_id:
            logger.warning("Invalid channel ID provided")
            return False
        
        channel_key = f"channel_{int(datetime.now().timestamp() * 1000)}"
        channel = Channel(
            id=channel_key,
            channel_id=channel_id,
            name=name or f"Channel {len(self.channels) + 1}"
        )
        
        self.channels[channel_key] = channel
        self._save_data()
        logger.info(f"Added channel: {channel.name} ({channel_id})")
        return True
    
    def remove_channel(self, channel_id: str) -> bool:
        """
        Remove a channel.
        
        Args:
            channel_id: Channel ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        if channel_id in self.channels:
            channel_name = self.channels[channel_id].name
            del self.channels[channel_id]
            self._save_data()
            logger.info(f"Removed channel: {channel_name} ({channel_id})")
            return True
        
        return False
    
    def start_bot(self, bot_id: str) -> bool:
        """
        Start a bot in a new thread.
        
        Args:
            bot_id: Bot ID to start
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id not in self.bots:
            logger.error(f"Bot {bot_id} not found")
            return False
        
        if bot_id in self.running_bots:
            logger.warning(f"Bot {bot_id} is already running")
            return False
        
        bot = self.bots[bot_id]
        
        # Validate token exists
        if not bot.token:
            logger.error(f"No token found for bot {bot_id}")
            return False
        
        # Check if token appears to be masked (contains '...')
        if '...' in bot.token:
            logger.error(f"Token appears to be masked for bot {bot_id}. Please re-add the bot with the full token.")
            return False
        
        try:
            # Create telebot instance
            tb = telebot.TeleBot(bot.token)
            
            # Get list of channel IDs to monitor
            monitored_channels = [channel.channel_id for channel in self.channels.values()]
            
            # Store bot_id in bot instance for handlers
            tb._bot_id = bot_id
            tb._bot_service = self
            
            @tb.message_handler(commands=['start'])
            def handle_start(message):
                """Handle /start command in private chats."""
                if message.chat.type == 'private':
                    tb.reply_to(message, 'Hello! Bot is running from TG Reactor Bot Manager!')
            
            @tb.message_handler(func=lambda m: m.chat.type == 'private' and m.text and not m.text.startswith('/'))
            def handle_echo(message):
                """Echo handler for text messages in private chats."""
                tb.reply_to(message, f'You said: {message.text}')
            
            # Handler for all channel post types including GIFs (animation) and stickers
            @tb.channel_post_handler(content_types=['text', 'photo', 'video', 'sticker', 'animation', 'document', 'audio', 'voice', 'video_note'])
            def handle_channel_post(message):
                """React to all types of posts (text, photo, video, sticker, GIF/animation, etc.) in monitored channels."""
                chat = message.chat
                chat_id = chat.id
                message_id = message.message_id
                chat_username = getattr(chat, 'username', None)
                # Call helper function to add reactions
                _add_reactions_to_channel_post(chat_id, message_id, chat_username, bot)
            
            # Fallback handler for any other content types not explicitly listed
            @tb.channel_post_handler(func=lambda m: True)
            def handle_channel_post_fallback(message):
                """Fallback handler for any channel post types not explicitly listed."""
                chat = message.chat
                chat_id = chat.id
                message_id = message.message_id
                chat_username = getattr(chat, 'username', None)
                # Call helper function to add reactions
                _add_reactions_to_channel_post(chat_id, message_id, chat_username, bot)
            
            # Handler for edited channel posts
            @tb.edited_channel_post_handler(content_types=['text', 'photo', 'video', 'sticker', 'animation', 'document', 'audio', 'voice', 'video_note'])
            def handle_edited_channel_post(message):
                """React to edited posts in monitored channels."""
                chat = message.chat
                chat_id = chat.id
                message_id = message.message_id
                chat_username = getattr(chat, 'username', None)
                # Call helper function to add reactions
                _add_reactions_to_channel_post(chat_id, message_id, chat_username, bot)
            
            # Fallback for edited posts
            @tb.edited_channel_post_handler(func=lambda m: True)
            def handle_edited_channel_post_fallback(message):
                """Fallback handler for edited channel posts."""
                chat = message.chat
                chat_id = chat.id
                message_id = message.message_id
                chat_username = getattr(chat, 'username', None)
                # Call helper function to add reactions
                _add_reactions_to_channel_post(chat_id, message_id, chat_username, bot)
            
            def _add_reactions_to_channel_post(chat_id, message_id, chat_username, bot):
                """Helper function to add reactions to channel posts."""
                
                # Check if this channel is in our monitored list
                channel_found = False
                matched_channel = None
                
                for channel in self.channels.values():
                    channel_id_str = str(channel.channel_id).strip()
                    
                    # Check numeric ID match (handle negative IDs)
                    try:
                        channel_id_int = int(channel_id_str)
                        if channel_id_int == chat_id:
                            channel_found = True
                            matched_channel = channel
                            break
                    except (ValueError, TypeError):
                        pass
                    
                    # Check username match (handle @ prefix)
                    if chat_username:
                        channel_username = channel_id_str.lstrip('@').lower()
                        chat_username_lower = chat_username.lower()
                        if channel_username == chat_username_lower:
                            channel_found = True
                            matched_channel = channel
                            break
                    
                    # Also check string match for usernames with @
                    if channel_id_str.startswith('@'):
                        if chat_username and channel_id_str.lower() == f"@{chat_username}".lower():
                            channel_found = True
                            matched_channel = channel
                            break
                
                if not channel_found:
                    logger.debug(f"Channel {chat_id} ({chat_username or 'no username'}) not in monitored list, skipping reaction")
                    return
                
                logger.info(f"Channel {matched_channel.name} ({str(matched_channel.channel_id)}) matched, adding reactions")
                
                # Mixed reaction emojis (only Telegram-supported reactions)
                # Telegram supports: 👍, 👎, ❤️, 🔥, ⭐, 💯, 🚀
                reaction_emojis = [
                    "👍", "❤️", "🔥", "⭐", "💯", "🚀"
                ]
                
                # Select 1-3 random reactions
                num_reactions = random.randint(1, 3)
                selected_reactions = random.sample(reaction_emojis, min(num_reactions, len(reaction_emojis)))
                
                try:
                    # Add reactions to the post using direct Telegram Bot API call
                    # Send all reactions in a single call (Bot API supports multiple reactions)
                    url = f"https://api.telegram.org/bot{bot.token}/setMessageReaction"
                    
                    # Format all reactions as an array of ReactionType objects
                    reaction_array = [{"type": "emoji", "emoji": emoji} for emoji in selected_reactions]
                    
                    payload = {
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "reaction": reaction_array
                    }
                    
                    try:
                        response = requests.post(url, json=payload, timeout=10)
                        response.raise_for_status()
                        result = response.json()
                        
                        if result.get('ok', False):
                            logger.info(f"Added reactions {selected_reactions} to post {message_id} in channel {matched_channel.name} ({chat_id})")
                        else:
                            error_desc = result.get('description', 'Unknown error')
                            logger.warning(f"Failed to add reactions {selected_reactions}: {error_desc}")
                            # Fallback: try sending reactions one at a time if batch fails
                            logger.info(f"Attempting to add reactions one at a time as fallback...")
                            successful_reactions = []
                            for emoji in selected_reactions:
                                try:
                                    single_payload = {
                                        "chat_id": chat_id,
                                        "message_id": message_id,
                                        "reaction": [{"type": "emoji", "emoji": emoji}]
                                    }
                                    single_response = requests.post(url, json=single_payload, timeout=10)
                                    single_response.raise_for_status()
                                    single_result = single_response.json()
                                    if single_result.get('ok', False):
                                        successful_reactions.append(emoji)
                                        # Small delay between reactions to avoid rate limiting
                                        time.sleep(0.2)
                                    else:
                                        error_desc = single_result.get('description', 'Unknown error')
                                        logger.warning(f"Failed to add reaction {emoji}: {error_desc}")
                                except Exception as e:
                                    logger.warning(f"Error adding reaction {emoji}: {e}")
                            
                            if successful_reactions:
                                logger.info(f"Added reactions {successful_reactions} to post {message_id} in channel {matched_channel.name} ({chat_id})")
                            else:
                                logger.warning(f"Failed to add any reactions to post {message_id} in channel {matched_channel.name} ({chat_id})")
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 400:
                            try:
                                error_data = e.response.json()
                                error_desc = error_data.get('description', str(e))
                                logger.warning(f"Failed to add reactions {selected_reactions}: {error_desc}")
                                # Check if it's a "too many reactions" error - try fewer reactions
                                if "too many" in error_desc.lower() or "reactions_uniq_max" in error_desc.lower():
                                    logger.info(f"Too many reactions, trying with fewer reactions...")
                                    # Try with just 1 reaction
                                    if len(selected_reactions) > 1:
                                        single_reaction = selected_reactions[0]
                                        single_payload = {
                                            "chat_id": chat_id,
                                            "message_id": message_id,
                                            "reaction": [{"type": "emoji", "emoji": single_reaction}]
                                        }
                                        try:
                                            single_response = requests.post(url, json=single_payload, timeout=10)
                                            single_response.raise_for_status()
                                            single_result = single_response.json()
                                            if single_result.get('ok', False):
                                                logger.info(f"Added reaction {single_reaction} to post {message_id} in channel {matched_channel.name} ({chat_id})")
                                        except Exception as e2:
                                            logger.warning(f"Failed to add single reaction {single_reaction}: {e2}")
                            except:
                                logger.warning(f"Failed to add reactions {selected_reactions}: {e}")
                        else:
                            logger.warning(f"HTTP error adding reactions {selected_reactions}: {e}")
                    except Exception as e:
                        logger.warning(f"Error adding reactions {selected_reactions}: {e}")
                except Exception as e:
                    error_msg = str(e).lower()
                    logger.error(f"Error adding reaction to post {message_id} in channel {chat_id}: {e}")
                    # Log more details for debugging
                    if "not enough rights" in error_msg or "forbidden" in error_msg:
                        logger.warning(f"Bot may not have permission to react in channel {matched_channel.name}. Make sure the bot is an admin with reaction permissions.")
            
            def run_bot():
                """Run the bot in a thread with automatic restart on failure."""
                max_retries = 5
                retry_count = 0
                import time
                
                while retry_count < max_retries:
                    # Check if bot should still be running
                    if bot_id not in self.bots or bot_id not in self.running_bots:
                        logger.info(f"Bot {bot.name} ({bot_id}) was removed or stopped. Exiting polling loop.")
                        break
                    
                    try:
                        logger.info(f"Starting polling for bot {bot.name} ({bot_id}) - Attempt {retry_count + 1}/{max_retries}")
                        # Use skip_pending to avoid processing old updates
                        tb.infinity_polling(none_stop=True, interval=0, timeout=20, long_polling_timeout=20, skip_pending=True)
                        # If we exit polling normally (not due to exception), break
                        logger.info(f"Bot {bot.name} ({bot_id}) polling exited normally")
                        break
                    except ApiTelegramException as e:
                        error_msg = str(e)
                        if "conflict" in error_msg.lower() or "terminated by other getUpdates" in error_msg.lower():
                            logger.warning(f"Bot {bot.name} ({bot_id}) conflict: Another instance is already running this bot.")
                            break
                        else:
                            logger.error(f"Telegram API error in bot polling {bot_id}: {e}")
                            retry_count += 1
                            if retry_count < max_retries:
                                wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30 seconds
                                logger.info(f"Retrying bot {bot.name} ({bot_id}) in {wait_time} seconds...")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"Max retries reached for bot {bot.name} ({bot_id}). Stopping.")
                                break
                    except KeyboardInterrupt:
                        logger.info(f"Bot {bot.name} ({bot_id}) stopped by user")
                        break
                    except Exception as e:
                        error_str = str(e).lower()
                        # Ignore "Break infinity polling" errors - these are expected when stopping
                        if "break infinity polling" in error_str or "polling exited" in error_str:
                            logger.debug(f"Bot {bot.name} ({bot_id}) polling stopped (expected)")
                            break
                        logger.error(f"Unexpected error in bot thread {bot_id}: {e}", exc_info=True)
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30 seconds
                            logger.info(f"Retrying bot {bot.name} ({bot_id}) in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Max retries reached for bot {bot.name} ({bot_id}). Stopping.")
                            break
                
                # Mark as not running if we exit the loop
                if bot_id in self.bots:
                    self.bots[bot_id].is_running = False
                    self._save_data()
                if bot_id in self.running_bots:
                    del self.running_bots[bot_id]
                logger.info(f"Bot {bot.name} ({bot_id}) polling stopped")
            
            # Start bot in a separate thread
            thread = threading.Thread(target=run_bot, daemon=True)
            thread.start()
            
            self.running_bots[bot_id] = tb
            bot.is_running = True
            self._save_data()
            logger.info(f"Started bot: {bot.name} ({bot_id}) with {len(monitored_channels)} monitored channels")
            return True
            
        except ApiTelegramException as e:
            error_msg = str(e)
            if "conflict" in error_msg.lower() or "terminated by other getUpdates" in error_msg.lower():
                logger.warning(f"Bot {bot.name} ({bot_id}) is already running in another instance: {e}")
                logger.warning("Make sure only one instance of the bot manager is running, or stop the bot in the other instance.")
                bot.is_running = False
                self._save_data()
            elif "rejected" in error_msg.lower() or "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                logger.error(f"Bot token rejected for bot {bot.name} ({bot_id}): {error_msg}")
                logger.error("Please check if the bot token is valid and hasn't been revoked. Get a new token from @BotFather on Telegram.")
            else:
                logger.error(f"Error starting bot {bot.name} ({bot_id}): {error_msg}")
            return False
        except Exception as e:
            error_msg = str(e)
            if "rejected" in error_msg.lower() or "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
                logger.error(f"Bot token rejected for bot {bot.name} ({bot_id}): {error_msg}")
                logger.error("Please check if the bot token is valid and hasn't been revoked. Get a new token from @BotFather on Telegram.")
            else:
                logger.error(f"Error starting bot {bot.name} ({bot_id}): {error_msg}")
            return False
    
    def stop_bot(self, bot_id: str) -> bool:
        """
        Stop a bot.
        
        Args:
            bot_id: Bot ID to stop
            
        Returns:
            True if successful, False otherwise
        """
        # If bot is in running_bots, stop it properly
        if bot_id in self.running_bots:
            try:
                tb = self.running_bots[bot_id]
                # Remove from running_bots first to signal the polling loop to exit
                del self.running_bots[bot_id]
                # Mark as not running
                if bot_id in self.bots:
                    self.bots[bot_id].is_running = False
                    self._save_data()
                # Stop polling (this may raise "Break infinity polling" which is expected)
                try:
                    tb.stop_polling()
                except Exception as e:
                    # Ignore "Break infinity polling" errors - these are expected
                    error_str = str(e).lower()
                    if "break infinity polling" not in error_str and "polling exited" not in error_str:
                        logger.warning(f"Error stopping polling for bot {bot_id}: {e}")
                logger.info(f"Stopped bot: {bot_id}")
                return True
            except Exception as e:
                logger.error(f"Error stopping bot {bot_id}: {e}")
                # Still remove from running_bots even if stop fails
                if bot_id in self.running_bots:
                    del self.running_bots[bot_id]
                if bot_id in self.bots:
                    self.bots[bot_id].is_running = False
                    self._save_data()
                return False
        
        # If bot is not in running_bots but has is_running=True, just clear the flag
        # This can happen after server restart when state is out of sync
        if bot_id in self.bots and self.bots[bot_id].is_running:
            self.bots[bot_id].is_running = False
            self._save_data()
            logger.info(f"Cleared is_running flag for bot {bot_id} (was not actually running)")
            return True
        
        return False
    
    def start_all_bots(self) -> int:
        """
        Start all bots.
        
        Returns:
            Number of bots started
        """
        started = 0
        for bot_id in self.bots:
            if not self.bots[bot_id].is_running:
                if self.start_bot(bot_id):
                    started += 1
        
        logger.info(f"Started {started} bots")
        return started
    
    def stop_all_bots(self) -> int:
        """
        Stop all bots.
        
        Returns:
            Number of bots stopped
        """
        stopped = 0
        for bot_id in list(self.running_bots.keys()):
            if self.stop_bot(bot_id):
                stopped += 1
        
        logger.info(f"Stopped {stopped} bots")
        return stopped
    
    def get_bot(self, bot_id: str) -> Optional[Bot]:
        """Get a bot by ID."""
        return self.bots.get(bot_id)
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID."""
        return self.channels.get(channel_id)
    
    def get_all_bots(self) -> Dict[str, Bot]:
        """Get all bots."""
        return self.bots.copy()
    
    def get_all_channels(self) -> Dict[str, Channel]:
        """Get all channels."""
        return self.channels.copy()
    
    def is_server_running(self) -> bool:
        """Check if any bots are running."""
        # Check both in-memory running_bots and persisted is_running flags
        if len(self.running_bots) > 0:
            return True
        # Also check if any bot has is_running flag set
        return any(bot.is_running for bot in self.bots.values())
