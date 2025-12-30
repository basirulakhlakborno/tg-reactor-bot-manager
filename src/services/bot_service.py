"""Bot management service."""

import logging
import threading
import random
import requests
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
            
            @tb.channel_post_handler(func=lambda m: True)
            def handle_channel_post(message):
                """React to posts in monitored channels with mixed reactions."""
                chat = message.chat
                chat_id = chat.id
                message_id = message.message_id
                chat_username = getattr(chat, 'username', None)
                
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
                
                logger.info(f"Channel {matched_channel.name} ({str(matched_channel.channel_id)}) matched, adding reaction")
                
                # Single reaction emoji (to avoid REACTIONS_TOO_MANY error)
                reaction_emojis = ["❤️", "🔥", "🎉", "👍"]
                
                # Select just 1 random reaction
                selected_reactions = [random.choice(reaction_emojis)]
                
                try:
                    # Add reactions to the post using direct Telegram API call
                    # Format reactions as list of ReactionTypeEmoji objects
                    reactions = [{"type": "emoji", "emoji": emoji} for emoji in selected_reactions]
                    
                    # Make direct API call to Telegram
                    url = f"https://api.telegram.org/bot{bot.token}/setMessageReaction"
                    payload = {
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "reaction": reactions,
                        "is_big": False
                    }
                    
                    response = requests.post(url, json=payload, timeout=10)
                    
                    # Parse response to get detailed error info
                    try:
                        result = response.json()
                    except:
                        result = {"ok": False, "description": response.text}
                    
                    # Check response status
                    if response.status_code != 200 or not result.get('ok', False):
                        error_desc = result.get('description', f'HTTP {response.status_code}')
                        
                        # Check for specific permission errors
                        error_lower = error_desc.lower()
                        if "not enough rights" in error_lower or "forbidden" in error_lower:
                            logger.warning(f"Bot lacks admin permissions in channel {matched_channel.name} ({chat_id}). Skipping reactions.")
                        elif "reactions are unavailable" in error_lower or "not available" in error_lower:
                            logger.warning(f"Reactions are not enabled in channel {matched_channel.name} ({chat_id}).")
                        else:
                            logger.error(f"Failed to add reactions to post {message_id} in channel {chat_id}: {error_desc}")
                        return
                    
                    logger.info(f"Added reactions {selected_reactions} to post {message_id} in channel {matched_channel.name} ({chat_id})")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Network error adding reaction to post {message_id} in channel {chat_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error adding reaction to post {message_id} in channel {chat_id}: {e}")
            
            def run_bot():
                """Run the bot in a thread."""
                try:
                    logger.info(f"Starting polling for bot {bot.name} ({bot_id}) - will only react to new messages")
                    # skip_pending=True ensures only NEW messages after bot starts will be processed
                    tb.infinity_polling(none_stop=True, interval=0, timeout=20, skip_pending=True)
                except ApiTelegramException as e:
                    error_msg = str(e)
                    if "conflict" in error_msg.lower() or "terminated by other getUpdates" in error_msg.lower():
                        logger.warning(f"Bot {bot.name} ({bot_id}) conflict: Another instance is already running this bot.")
                        # Mark as not running
                        if bot_id in self.bots:
                            self.bots[bot_id].is_running = False
                            self._save_data()
                        if bot_id in self.running_bots:
                            del self.running_bots[bot_id]
                    else:
                        logger.error(f"Error in bot polling {bot_id}: {e}")
                except Exception as e:
                    logger.error(f"Error in bot thread {bot_id}: {e}")
                    # Mark as not running
                    if bot_id in self.bots:
                        self.bots[bot_id].is_running = False
                        self._save_data()
                    if bot_id in self.running_bots:
                        del self.running_bots[bot_id]
            
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
                tb.stop_polling()
                del self.running_bots[bot_id]
                if bot_id in self.bots:
                    self.bots[bot_id].is_running = False
                    self._save_data()
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
