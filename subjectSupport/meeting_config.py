"""
Meeting Platform API Configuration

This file contains configuration for video conferencing platforms.
For production, use environment variables instead of hardcoding credentials.
"""

import os

# Google Meet API Configuration
# To use real Google Meet API, you'll need to:
# 1. Create a Google Cloud Project
# 2. Enable Google Calendar API
# 3. Create OAuth 2.0 credentials
# 4. Download credentials JSON file
GOOGLE_MEET_CONFIG = {
    'enabled': False,  # Set to True when you have real API credentials
    'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
    'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/oauth/google/callback'),
    'scopes': [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
    ]
}

# Zoom API Configuration
# To use real Zoom API, you'll need to:
# 1. Create a Zoom App (Server-to-Server OAuth)
# 2. Get your Account ID, Client ID, and Client Secret
# 3. Add required scopes: meeting:write, meeting:read
ZOOM_CONFIG = {
    'enabled': False,  # Set to True when you have real API credentials
    'account_id': os.getenv('ZOOM_ACCOUNT_ID', ''),
    'client_id': os.getenv('ZOOM_CLIENT_ID', ''),
    'client_secret': os.getenv('ZOOM_CLIENT_SECRET', ''),
    'api_base_url': 'https://api.zoom.us/v2',
    'oauth_url': 'https://zoom.us/oauth/token'
}

# Custom Meeting Platform Configuration
CUSTOM_MEETING_CONFIG = {
    'enabled': True,  # Always enabled as fallback
    'base_url': os.getenv('CUSTOM_MEETING_BASE_URL', 'https://meet.subjectsupport.com'),
    'password_length': 8
}

# Default meeting platform if none is specified
DEFAULT_MEETING_PLATFORM = 'google_meet'

# Meeting URL expiration time (in hours)
MEETING_URL_EXPIRATION_HOURS = 24

# Enable meeting recordings (requires API integration)
ENABLE_MEETING_RECORDINGS = False

# Meeting settings
MEETING_SETTINGS = {
    'waiting_room': True,  # Enable waiting room for security
    'join_before_host': False,  # Participants can't join before host
    'mute_upon_entry': True,  # Mute participants when they join
    'auto_recording': 'none',  # Options: 'local', 'cloud', 'none'
}


# Instructions for setting up environment variables:
"""
For development, create a .env file in the project root:

# Google Meet
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback

# Zoom
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret

# Custom
CUSTOM_MEETING_BASE_URL=https://meet.subjectsupport.com

For production, set these as environment variables in your hosting platform.
"""
