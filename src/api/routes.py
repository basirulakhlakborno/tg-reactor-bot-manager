"""API routes."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import jsonify, request, session, current_app
from src.api import api_bp
from src.services.bot_service import BotService
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Get bot_service from app context or create a new one
# This will be set by app.py to share the same instance
bot_service = None

def init_bot_service(service_instance):
    """Initialize bot service from app.py"""
    global bot_service
    bot_service = service_instance


def require_auth():
    """Check if user is authenticated."""
    if 'logged_in' not in session or not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    return None


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Server is running'})


@api_bp.before_request
def check_auth():
    """Check authentication for all API routes except health."""
    if request.endpoint != 'api.health_check':
        auth_check = require_auth()
        if auth_check:
            return auth_check


@api_bp.route('/bots', methods=['GET'])
def get_bots():
    """Get all bots."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        bots = bot_service.get_all_bots()
        bots_data = {bot_id: bot.to_dict() for bot_id, bot in bots.items()}
        return jsonify({'success': True, 'bots': bots_data})
    except Exception as e:
        logger.error(f"Error getting bots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/bots', methods=['POST'])
def add_bot():
    """Add a new bot."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        data = request.get_json()
        token = data.get('token', '').strip()
        name = data.get('name', '').strip()
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is required'}), 400
        
        if bot_service.add_bot(token, name):
            return jsonify({'success': True, 'message': 'Bot added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invalid bot token'}), 400
    except Exception as e:
        logger.error(f"Error adding bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/bots/<bot_id>', methods=['DELETE'])
def remove_bot(bot_id):
    """Remove a bot."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        if bot_service.remove_bot(bot_id):
            return jsonify({'success': True, 'message': 'Bot removed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
    except Exception as e:
        logger.error(f"Error removing bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/bots/<bot_id>/start', methods=['POST'])
def start_bot(bot_id):
    """Start a bot."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        if bot_service.start_bot(bot_id):
            return jsonify({'success': True, 'message': 'Bot started successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start bot'}), 400
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/bots/<bot_id>/stop', methods=['POST'])
def stop_bot(bot_id):
    """Stop a bot."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        if bot_service.stop_bot(bot_id):
            return jsonify({'success': True, 'message': 'Bot stopped successfully'})
        else:
            return jsonify({'success': False, 'error': 'Bot is not running'}), 400
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/bots/start-all', methods=['POST'])
def start_all_bots():
    """Start all bots."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        count = bot_service.start_all_bots()
        return jsonify({'success': True, 'message': f'Started {count} bots', 'count': count})
    except Exception as e:
        logger.error(f"Error starting all bots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/bots/stop-all', methods=['POST'])
def stop_all_bots():
    """Stop all bots."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        count = bot_service.stop_all_bots()
        return jsonify({'success': True, 'message': f'Stopped {count} bots', 'count': count})
    except Exception as e:
        logger.error(f"Error stopping all bots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/channels', methods=['GET'])
def get_channels():
    """Get all channels."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        channels = bot_service.get_all_channels()
        channels_data = {channel_id: channel.to_dict() for channel_id, channel in channels.items()}
        return jsonify({'success': True, 'channels': channels_data})
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/channels', methods=['POST'])
def add_channel():
    """Add a new channel."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        data = request.get_json()
        channel_id = data.get('channel_id', '').strip()
        name = data.get('name', '').strip()
        
        if not channel_id:
            return jsonify({'success': False, 'error': 'Channel ID is required'}), 400
        
        if bot_service.add_channel(channel_id, name):
            return jsonify({'success': True, 'message': 'Channel added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invalid channel ID'}), 400
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/channels/<channel_id>', methods=['DELETE'])
def remove_channel(channel_id):
    """Remove a channel."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        if bot_service.remove_channel(channel_id):
            return jsonify({'success': True, 'message': 'Channel removed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Channel not found'}), 404
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get server status."""
    try:
        if bot_service is None:
            return jsonify({'success': False, 'error': 'Bot service not initialized'}), 500
        bots = bot_service.get_all_bots()
        channels = bot_service.get_all_channels()
        running_count = sum(1 for bot in bots.values() if bot.is_running)
        # Check if server is running - either bots are in running_bots dict or have is_running flag
        server_running = bot_service.is_server_running() or running_count > 0
        
        return jsonify({
            'success': True,
            'status': {
                'total_bots': len(bots),
                'running_bots': running_count,
                'stopped_bots': len(bots) - running_count,
                'total_channels': len(channels),
                'server_running': server_running
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

