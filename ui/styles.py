import tkinter as tk
from tkinter import ttk

COLORS = {
    'primary': '#0d6efd',
    'secondary': '#6c757d',
    'success': '#198754',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'light': '#f8f9fa',
    'dark': '#212529',
    'bg': '#f4f6f9',
    'white': '#ffffff'
}

FONTS = {
    'h1': ('Helvetica', 24, 'bold'),
    'h2': ('Helvetica', 20, 'bold'),
    'h3': ('Helvetica', 16, 'bold'),
    'body': ('Helvetica', 12),
    'body_bold': ('Helvetica', 12, 'bold'),
    'small': ('Helvetica', 10),
    'small_italic': ('Helvetica', 10, 'italic')
}

def setup_styles():
    style = ttk.Style()
    
    # Attempt to use a native-looking theme
    themes = style.theme_names()
    if 'clam' in themes:
        style.theme_use('clam')
        
    # Standard widget configurations
    style.configure('TFrame', background=COLORS['bg'])
    style.configure('Card.TFrame', background=COLORS['white'], relief='flat')
    
    style.configure('TLabel', background=COLORS['bg'], font=FONTS['body'], foreground=COLORS['dark'])
    style.configure('Card.TLabel', background=COLORS['white'], font=FONTS['body'])
    
    style.configure('Title.TLabel', font=FONTS['h1'], foreground=COLORS['primary'], background=COLORS['bg'])
    style.configure('Subtitle.TLabel', font=FONTS['h2'], foreground=COLORS['dark'], background=COLORS['bg'])
    style.configure('Error.TLabel', font=FONTS['body'], foreground=COLORS['danger'], background=COLORS['bg'])
    style.configure('Success.TLabel', font=FONTS['body'], foreground=COLORS['success'], background=COLORS['bg'])
    
    # Buttons
    style.configure('TButton', font=FONTS['body_bold'], padding=5)
    style.configure('Primary.TButton', background=COLORS['primary'], foreground=COLORS['white'])
    style.map('Primary.TButton', background=[('active', '#0b5ed7')])
    
    style.configure('Danger.TButton', background=COLORS['danger'], foreground=COLORS['white'])
    style.map('Danger.TButton', background=[('active', '#bb2d3b')])
    
    style.configure('Success.TButton', background=COLORS['success'], foreground=COLORS['white'])
    style.map('Success.TButton', background=[('active', '#157347')])
    
    # Entries
    style.configure('TEntry', padding=5, font=FONTS['body'])
