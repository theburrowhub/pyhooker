#!/usr/bin/env python3
"""
PyHooker - A simple webhook receiver and inspector tool.
"""

import os
import sys
import app
import importlib.resources
import importlib.util
import site
import sys

def get_resource_path(relative_path):
    """Get the resource path, works for both development and PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    # Set environment variables for resource paths
    os.environ["TEMPLATES_DIR"] = get_resource_path("templates")
    os.environ["PUBLIC_DIR"] = get_resource_path("public")
    
    # Print a welcome message
    print("=" * 50)
    print("PyHooker - Webhook Receiver and Inspector")
    print("=" * 50)
    
    # Run the application
    app.main() 