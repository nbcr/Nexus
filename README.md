# Nexus - AI-Powered Content Personalization Engine

A FastAPI-based platform that automatically fetches trending Canadian news from Google Trends and provides personalized content recommendations with session-based user tracking.

## Features

- **Real-time Trending Content**: Fetches trending topics from Google Trends Canada RSS feed
- **User Authentication**: JWT-based authentication with registration/login
- **Session Tracking**: Anonymous session tracking with cookie-based persistence
- **Content Personalization**: AI-generated summaries and user interest tracking
- **Modern UI**: Responsive single-page application with expandable cards

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Asyncpg
- **Frontend**: Vanilla JavaScript, CSS3, HTML5
- **Authentication**: JWT, bcrypt
- **Deployment**: Uvicorn, Linux

## Project Structure

nexus/
├── app/
│ ├── api/routes/ # API endpoints
│ ├── core/ # Configuration and settings
│ ├── database/ # Database configuration
│ ├── models/ # SQLAlchemy models
│ ├── services/ # Business logic
│ └── static/ # Frontend assets
├── scripts/ # Utility scripts
└── requirements.txt # Python dependencies

text

## Quick Start

1. **Setup Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Database Setup:

bash
./db_setup.sh
Run Development Server:

bash
python run_server.py
Access Application:

Main App: <http://localhost:8000/app>

API Docs: <http://localhost:8000/docs>

API Endpoints
GET /api/v1/trending/enhanced-trends - Get trending topics with images and sources

POST /api/v1/auth/register - User registration

POST /api/v1/auth/login - User login

POST /api/v1/session/track-view/{content_id} - Track content views

GET /api/v1/session/history - Get user viewing history

Development
The project uses:

FastAPI for async API development

PostgreSQL with SQLAlchemy ORM

Modular frontend with vanilla JavaScript

Git for version control
