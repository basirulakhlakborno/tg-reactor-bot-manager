"""Setup service for module installation."""

import subprocess
import sys
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SetupService:
    """Service for managing module installation."""
    
    def __init__(self):
        """Initialize setup service."""
        self.required_modules = {
            'flask': 'Flask==3.0.0',
            'flask-cors': 'flask-cors==4.0.0',
            'pyTelegramBotAPI': 'pyTelegramBotAPI==4.14.0',
            'python-dotenv': 'python-dotenv==1.0.0'
        }
    
    def check_module_installed(self, module_name: str) -> bool:
        """
        Check if a module is installed.
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if module is installed
        """
        # Map package names to their import names
        import_map = {
            'flask': 'flask',
            'flask-cors': 'flask_cors',
            'pyTelegramBotAPI': 'telebot',
            'python-dotenv': 'dotenv'
        }
        
        import_name = import_map.get(module_name, module_name.replace('-', '_'))
        
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False
    
    def get_installation_status(self) -> Dict[str, bool]:
        """
        Get installation status of all required modules.
        
        Returns:
            Dictionary mapping module names to installation status
        """
        status = {}
        for module in self.required_modules.keys():
            status[module] = self.check_module_installed(module)
        return status
    
    def install_module(self, module_name: str) -> Dict[str, any]:
        """
        Install a module.
        
        Args:
            module_name: Module name or package specification
            
        Returns:
            Dictionary with installation result
        """
        try:
            package_spec = self.required_modules.get(module_name, module_name)
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_spec],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {module_name}")
                return {
                    'success': True,
                    'message': f'{module_name} installed successfully',
                    'output': result.stdout
                }
            else:
                logger.error(f"Error installing {module_name}: {result.stderr}")
                return {
                    'success': False,
                    'message': f'Error installing {module_name}',
                    'error': result.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': f'Installation timeout for {module_name}',
                'error': 'Installation took too long'
            }
        except Exception as e:
            logger.error(f"Exception installing {module_name}: {e}")
            return {
                'success': False,
                'message': f'Exception installing {module_name}',
                'error': str(e)
            }
    
    def install_all_modules(self) -> Dict[str, any]:
        """
        Install all required modules.
        
        Returns:
            Dictionary with installation results
        """
        results = {}
        for module_name in self.required_modules.keys():
            if not self.check_module_installed(module_name):
                results[module_name] = self.install_module(module_name)
            else:
                results[module_name] = {
                    'success': True,
                    'message': f'{module_name} is already installed',
                    'skipped': True
                }
        return results
    
    def get_required_modules(self) -> Dict[str, str]:
        """Get list of required modules."""
        return self.required_modules.copy()

