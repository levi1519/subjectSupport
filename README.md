# EduLatam

**Academic tutoring platform connecting university students with qualified tutors in Ecuador.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-darkgreen)](https://www.djangoproject.com/)
[![Railway Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E)](https://railway.app/)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Description

EduLatam connects university students with qualified tutors through a streamlined digital platform. Students search for tutors by name, subject, or knowledge area; request sessions with optional learning materials; and join video conferences once tutors confirm availability. All operations are restricted to Ecuador through IP-based geolocation detection, ensuring compliance with regional requirements.

The platform automates geographic verification at registration, automatically detecting city location and enforcing country restrictions. Video meeting links are shared directly between participants, enabling flexible scheduling and seamless real-time collaboration.

## Features

**For Tutors:**
- Manage subjects across 5+ knowledge areas
- Set personalized hourly rates
- Upload custom avatar
- Accept or reject student session requests
- Share video conference links (Google Meet, Zoom)

**For Students:**
- Search and filter tutors by name, subject, or knowledge area
- Filter tutors by country (Ecuador-based by default)
- Request sessions with optional material URL attachments
- View complete session history
- Join meetings once confirmed

**System-wide:**
- Geo-restriction to 23 LATAM countries (configurable; currently Ecuador only)
- Automatic city detection at registration via IP geolocation
- Bootstrap 5 responsive design for mobile & desktop
- Admin panel at `/gestion-ss-2026/`

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Django 5.2, Python 3.12 | Web framework, business logic |
| **Database** | PostgreSQL + PostGIS | Relational DB, geospatial queries |
| **Hosting** | Supabase | Managed PostgreSQL, real-time features |
| **Deploy** | Railway + Nixpacks | Continuous deployment, auto-scaling |
| **Frontend** | Bootstrap 5, Django Templates | Responsive UI, server-rendered HTML |
| **Geolocation** | ipgeolocation.io API | IP-based country/city detection |
| **Meetings** | Google Meet, Zoom | Video conferencing integration |

## Project Structure

```
apps/accounts/          User authentication & profiles
apps/academicTutoring/  Tutoring sessions & subject management
geoconfig/              Geographic restriction middleware & utilities
templates/              Django HTML templates
static/                 CSS, JavaScript, images
subjectSupport/         Django settings & project configuration
```

## Setup — Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/edulatam.git
   cd edulatam
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   ```

3. **Activate and install dependencies**
   ```bash
   # Windows
   env\Scripts\activate
   # macOS/Linux
   source env/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values (see Environment Variables section below)
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

**Note:** GDAL/GEOS libraries are not required for local development. PostGIS features activate only in production with proper database configuration.

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Development mode flag | `True` |
| `SECRET_KEY` | Django secret key (50+ chars) | `your-random-key-here` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://yourdomain.railway.app` |
| `SKIP_GEO_CHECK` | Bypass geolocation (dev only) | `True` |
| `IPGEOLOCATION_API_KEY` | IP geolocation service API key | `your-api-key` |

## Deploy on Railway

1. Connect your GitHub repository to Railway
2. Set environment variables in the Railway dashboard (see Environment Variables section)
3. Railway auto-detects Nixpacks and deploys automatically
4. Database migrations run automatically on each deployment

**Note:** Configuration files `nixpacks.toml` and `build.sh` are at the repository root.

## Admin Panel

The Django admin panel is accessible at `/gestion-ss-2026/`. Administrators can:
- Manage user accounts and permissions
- Create and modify tutor profiles and qualifications
- Configure subjects and knowledge areas
- Enable/disable supported countries
- Monitor and manage active sessions
- View platform analytics and statistics

## Key Architecture Decisions

- **Services Layer:** All business logic resides in `services.py` files, never in views. Views remain thin and delegate to services.
- **Database Managers:** Custom managers (e.g., `TutorProfileManager`) handle all database queries, ensuring consistency and reusability.
- **Geo-restriction:** Middleware intercepts all requests and delegates geographic verification to `geoconfig/geo.py`.
- **Subject Mapping:** Tutors' subjects reference `accounts.Subject` via M2M relation, not `SubjectLevel`.

## Contributing

EduLatam follows a deterministic, directive-based development workflow. All code changes are planned through explicit directives before implementation. This ensures consistency, traceability, and quality across the codebase.

## License

MIT License — see [LICENSE](LICENSE) file for details.
