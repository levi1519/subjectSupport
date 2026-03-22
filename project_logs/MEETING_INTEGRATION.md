# Meeting Platform Integration Guide

## Overview

SubjectSupport now supports automatic video meeting link generation for tutoring sessions with three platforms:

1. **Google Meet** - Free for Gmail users
2. **Zoom** - Professional video conferencing
3. **Custom** - SubjectSupport's own meeting platform (placeholder)

## Current Implementation

### What Works Now (Without API Keys)

The system currently generates **placeholder URLs** that follow the same format as real meeting platforms:

- **Google Meet**: `https://meet.google.com/{unique-id}`
- **Zoom**: `https://zoom.us/j/{meeting-id}?pwd={password}`
- **Custom**: `https://meet.subjectsupport.com/room/{room-id}`

These URLs are automatically generated when a tutor confirms a session.

### Features

- ✅ Meeting platform selection (Google Meet, Zoom, Custom)
- ✅ Automatic meeting URL generation
- ✅ Meeting ID and password generation (for Zoom)
- ✅ Host-specific join URLs
- ✅ Professional meeting room page with session details
- ✅ Meeting status tracking (started/not started)
- ✅ Dashboard integration showing meeting platform
- ✅ Secure access control (only tutor and client can access)

## How It Works

### 1. Session Request Flow

```
Client → Selects Tutor → Requests Session → Session Created (status: pending)
```

### 2. Session Confirmation Flow

```
Tutor → Reviews Request → Selects Meeting Platform → Confirms
  ↓
System automatically generates:
  - Meeting URL
  - Meeting ID (for Zoom)
  - Meeting Password (for Zoom)
  - Host join URL
```

### 3. Joining Meeting Flow

```
Tutor/Client → Dashboard → Click "Unirse/Iniciar" → Meeting Room Page → Join Meeting
```

## Files Modified

### Models
- `core/models.py` - Added meeting platform fields to ClassSession

### Services
- `core/services/meeting_service.py` - Meeting URL generation logic

### Views
- `core/views.py` - Added `meeting_room` view, updated `confirm_session`

### Forms
- `core/forms.py` - Updated SessionConfirmationForm to include meeting_platform

### Templates
- `core/templates/core/meeting_room.html` - Professional meeting join page
- `core/templates/core/confirm_session.html` - Platform selector
- `accounts/templates/accounts/client_dashboard.html` - Meeting platform display
- `accounts/templates/accounts/tutor_dashboard.html` - Meeting platform display

### URLs
- `core/urls.py` - Added meeting room route

### Configuration
- `subjectSupport/meeting_config.py` - API configuration (for future use)

## Database Fields

New fields added to `ClassSession` model:

```python
meeting_platform = CharField(max_length=20, choices=MEETING_PLATFORM_CHOICES, default='google_meet')
meeting_url = URLField(blank=True, null=True)
meeting_id = CharField(max_length=200, blank=True, null=True)
meeting_password = CharField(max_length=100, blank=True, null=True)
host_join_url = URLField(blank=True, null=True)
meeting_started = BooleanField(default=False)
```

## URL Structure

- `/sessions/<session_id>/meeting/` - Meeting room page
- `/sessions/<session_id>/confirm/` - Confirm session (with platform selection)
- `/sessions/<session_id>/cancel/` - Cancel session

## Future Enhancements (Real API Integration)

### For Google Meet API

1. **Setup Google Cloud Project**
   - Create project at https://console.cloud.google.com
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Download credentials JSON

2. **Install Dependencies**
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```

3. **Update `meeting_service.py`**
   ```python
   from google.oauth2 import service_account
   from googleapiclient.discovery import build

   def generate_real_google_meet_url(session):
       credentials = service_account.Credentials.from_service_account_file(
           'path/to/credentials.json',
           scopes=['https://www.googleapis.com/auth/calendar']
       )
       service = build('calendar', 'v3', credentials=credentials)

       event = {
           'summary': f"{session.subject} - {session.tutor.name} con {session.client.name}",
           'start': {
               'dateTime': f"{session.scheduled_date}T{session.scheduled_time}",
               'timeZone': 'America/Guayaquil',
           },
           'end': {
               # Add duration
           },
           'conferenceData': {
               'createRequest': {
                   'requestId': f"session-{session.id}",
                   'conferenceSolutionKey': {'type': 'hangoutsMeet'}
               }
           }
       }

       event = service.events().insert(
           calendarId='primary',
           body=event,
           conferenceDataVersion=1
       ).execute()

       return event['hangoutLink']
   ```

### For Zoom API

1. **Create Zoom App**
   - Go to https://marketplace.zoom.us/
   - Create Server-to-Server OAuth app
   - Get Account ID, Client ID, Client Secret
   - Add scopes: `meeting:write`, `meeting:read`

2. **Install Dependencies**
   ```bash
   pip install requests
   ```

3. **Update `meeting_service.py`**
   ```python
   import requests
   from subjectSupport.meeting_config import ZOOM_CONFIG

   def get_zoom_access_token():
       response = requests.post(
           ZOOM_CONFIG['oauth_url'],
           auth=(ZOOM_CONFIG['client_id'], ZOOM_CONFIG['client_secret']),
           data={'grant_type': 'account_credentials', 'account_id': ZOOM_CONFIG['account_id']}
       )
       return response.json()['access_token']

   def generate_real_zoom_url(session):
       token = get_zoom_access_token()
       headers = {
           'Authorization': f'Bearer {token}',
           'Content-Type': 'application/json'
       }

       meeting_data = {
           'topic': f"{session.subject} - {session.tutor.name} con {session.client.name}",
           'type': 2,  # Scheduled meeting
           'start_time': f"{session.scheduled_date}T{session.scheduled_time}:00Z",
           'duration': session.duration,
           'timezone': 'America/Guayaquil',
           'settings': {
               'waiting_room': True,
               'join_before_host': False,
               'mute_upon_entry': True
           }
       }

       response = requests.post(
           f"{ZOOM_CONFIG['api_base_url']}/users/me/meetings",
           headers=headers,
           json=meeting_data
       )

       meeting = response.json()
       return {
           'meeting_url': meeting['join_url'],
           'host_join_url': meeting['start_url'],
           'meeting_id': str(meeting['id']),
           'meeting_password': meeting.get('password', '')
       }
   ```

4. **Update `meeting_config.py`**
   - Set `enabled: True` for the platforms you want to use
   - Add your API credentials to environment variables

## Security Considerations

1. **Access Control**: Only tutors and clients involved in a session can access meeting room
2. **URL Obfuscation**: Meeting URLs use UUID for uniqueness
3. **Password Protection**: Zoom meetings include passwords
4. **Session Validation**: Meeting room checks session status before allowing access
5. **Environment Variables**: Use `.env` file for API credentials (never commit to git)

## Testing

1. **Create a test session**:
   - Login as client
   - Select a tutor
   - Request a session

2. **Confirm session**:
   - Login as tutor
   - Go to dashboard
   - Confirm pending session
   - Select meeting platform

3. **Join meeting**:
   - Both users can access meeting room from dashboard
   - Click "Unirse" (client) or "Iniciar" (tutor)
   - Meeting details displayed
   - External link opens to video platform

## Environment Setup (.env file)

Create a `.env` file in project root:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Google Meet API (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback

# Zoom API (optional)
ZOOM_ACCOUNT_ID=your-zoom-account-id
ZOOM_CLIENT_ID=your-zoom-client-id
ZOOM_CLIENT_SECRET=your-zoom-client-secret

# Custom Meeting Platform
CUSTOM_MEETING_BASE_URL=https://meet.subjectsupport.com
```

## Support

For issues or questions about meeting integration:
1. Check this documentation
2. Review `core/services/meeting_service.py`
3. Check Django logs for errors
4. Verify API credentials if using real APIs
