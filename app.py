"""Main Flask application."""

import os
import sys
from pathlib import Path
from functools import wraps

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from pathlib import Path
from config.config import SERVER_HOST, SERVER_PORT, DEBUG
from src.api import api_bp
from src.utils.logger import setup_logger
from src.auth.auth_service import AuthService
from src.setup.setup_service import SetupService
from src.services.bot_service import BotService

logger = setup_logger(__name__)

# Create Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
# Generate a consistent secret key (in production, use a fixed secret key)
if os.path.exists('data/secret.key'):
    with open('data/secret.key', 'r') as f:
        app.secret_key = f.read().strip()
else:
    app.secret_key = os.urandom(24).hex()
    Path('data').mkdir(parents=True, exist_ok=True)
    with open('data/secret.key', 'w') as f:
        f.write(app.secret_key)
CORS(app)

# Initialize services
auth_service = AuthService()
setup_service = SetupService()
bot_service = BotService()


def login_required(f):
    """Decorator for routes that require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_service.is_setup_complete():
            return redirect(url_for('setup'))
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Redirect to appropriate page."""
    if not auth_service.is_setup_complete():
        return redirect(url_for('setup'))
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('admin.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if auth_service.is_setup_complete():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if auth_service.verify_login(username, password):
                session['logged_in'] = True
                session['username'] = username
                return jsonify({'success': True, 'redirect': url_for('index')})
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'})
        
        return render_template('login.html')
    else:
        return redirect(url_for('setup'))


@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup page for first run."""
    if auth_service.is_setup_complete():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.json.get('action')
        
        if action == 'check_modules':
            status = setup_service.get_installation_status()
            return jsonify({'success': True, 'modules': status})
        
        elif action == 'install_module':
            module_name = request.json.get('module')
            result = setup_service.install_module(module_name)
            return jsonify(result)
        
        elif action == 'install_all':
            results = setup_service.install_all_modules()
            return jsonify({'success': True, 'results': results})
        
        elif action == 'complete_setup':
            username = request.json.get('username', '').strip()
            password = request.json.get('password', '').strip()
            confirm_password = request.json.get('confirm_password', '').strip()
            
            if not username or not password:
                return jsonify({'success': False, 'error': 'Username and password are required'})
            
            if password != confirm_password:
                return jsonify({'success': False, 'error': 'Passwords do not match'})
            
            if len(password) < 6:
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
            
            # Check if all modules are installed
            status = setup_service.get_installation_status()
            missing_modules = [name for name, installed in status.items() if not installed]
            if missing_modules:
                return jsonify({
                    'success': False, 
                    'error': f'Please install all required modules first. Missing: {", ".join(missing_modules)}'
                })
            
            auth_service.complete_setup(username, password)
            session['logged_in'] = True
            session['username'] = username
            
            return jsonify({'success': True, 'redirect': url_for('index')})
    
    return render_template('setup.html')


# Share bot_service instance with API routes
from src.api import routes as api_routes
api_routes.init_bot_service(bot_service)

# Register API blueprint (will be protected by login_required in routes)
app.register_blueprint(api_bp)


@app.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


def main():
    """Run the Flask application."""
    logger.info(f"Starting TG Reactor Bot Manager Admin Panel")
    
    if not auth_service.is_setup_complete():
        logger.info("First run detected - Setup required")
        logger.info(f"Setup page: http://localhost:{SERVER_PORT}/setup")
    else:
        logger.info(f"Admin panel: http://localhost:{SERVER_PORT}")
        # Auto-start all bots on application startup
        try:
            started_count = bot_service.start_all_bots()
            if started_count > 0:
                logger.info(f"Auto-started {started_count} bot(s) on application startup")
            else:
                logger.info("No bots to start or all bots already running")
        except Exception as e:
            logger.error(f"Error auto-starting bots: {e}")
    
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=DEBUG,
        threaded=True
    )


if __name__ == '__main__':
    main()
