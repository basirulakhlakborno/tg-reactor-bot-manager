"""Reusable UI components."""

import tkinter as tk


class ModernButton(tk.Button):
    """Custom styled button with modern appearance."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize modern button.
        
        Args:
            parent: Parent widget
            **kwargs: Additional button arguments
        """
        default_config = {
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'font': ('Segoe UI', 10, 'bold'),
            'bd': 0,
            'highlightthickness': 0,
            'activebackground': kwargs.get('bg', '#007AFF'),
            'activeforeground': 'white'
        }
        default_config.update(kwargs)
        super().__init__(parent, **default_config)

