#!/bin/bash

# Define installation directory
INSTALL_DIR="/usr/local/bin"

# Download the latest release
echo "Downloading PyHooker..."
curl -L -o pyhooker "https://github.com/Muriano/pyhooker/releases/latest/download/pyhooker"

# Make it executable
chmod +x pyhooker

# Move to installation directory
echo "Installing PyHooker to $INSTALL_DIR..."
sudo mv pyhooker "$INSTALL_DIR/"

echo "PyHooker has been installed successfully!"
echo "You can now run it from anywhere using the 'pyhooker' command." 