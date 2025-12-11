# Naad Bailgada - Digital Platform for Bullock Cart Racing

A comprehensive digital platform to manage, track, and celebrate Maharashtra's traditional Bailgada Sharyat (bullock cart races). This system provides race management, real-time leaderboards, and a premium mobile experience for fans and participants.

---

## Project Overview

**Domain**: Traditional bullock cart racing (Bailgada Sharyat)

**Key Features**:
- Bull and owner registration
- Race management and result tracking
- Monthly Top 10 leaderboards by region
- Regional hierarchy (District → Taluka → Tahsil → Village)
- Premium mobile app for end users
- Simple web-based admin panel

**Ranking Logic**: Bulls ranked by number of 1st place wins per month

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic v2
- **Testing**: pytest

### Mobile App
- **Framework**: Flutter 3.16+
- **State Management**: Riverpod / Bloc
- **HTTP Client**: Dio
- **Local Storage**: Hive / SQLite
- **UI**: Material Design 3

### Admin Panel
- **Framework**: FastAPI + Jinja2 Templates
- **Interactivity**: HTMX + Alpine.js
- **CSS**: Tailwind CSS

### Infrastructure (GCP)
- **Compute**: Cloud Run (serverless containers)
- **Database**: Cloud SQL (PostgreSQL)
- **Storage**: Cloud Storage + CDN
- **Secrets**: Secret Manager
- **CI/CD**: Cloud Build
- **Monitoring**: Cloud Monitoring & Logging
- **Scheduler**: Cloud Scheduler

---

## Project Structure

```
naad_bailgada/
├── backend/                    # FastAPI backend + admin panel
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/            # API endpoints
│   │   ├── core/              # Config, security, dependencies
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── db/                # Database utilities
│   ├── tests/                 # Backend tests
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
│
├── mobile_app/                # Flutter mobile application
│   ├── lib/
│   │   ├── models/           # Data models
│   │   ├── services/         # API services
│   │   ├── screens/          # UI screens
│   │   ├── widgets/          # Reusable widgets
│   │   └── utils/            # Utilities
│   ├── assets/               # Images, fonts
│   ├── test/                 # Flutter tests
│   ├── pubspec.yaml
│   └── README.md
│
├── admin_panel/               # Admin web interface (optional separate)
│   └── templates/            # Jinja2 templates
│
├── docs/                      # Documentation
│   ├── database_schema.sql   # Complete DB schema
│   ├── API_CONTRACT.md       # API documentation
│   ├── GCP_ARCHITECTURE.md   # Infrastructure design
│   └── IMPLEMENTATION_ROADMAP.md
│
├── scripts/                   # Utility scripts
│   ├── seed_data.py          # Sample data generator
│   ├── deploy.sh             # Deployment script
│   └── backup_db.sh          # Database backup
│
├── .gitignore
├── docker-compose.yml         # Local development
├── cloudbuild.yaml           # GCP Cloud Build config
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Flutter 3.16+
- Docker & Docker Compose (for local development)
- GCP account (for deployment)

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd naad_bailgada
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Seed sample data (optional)
python scripts/seed_data.py

# Start development server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

#### 3. Mobile App Setup
```bash
cd mobile_app

# Install dependencies
flutter pub get

# Run on emulator/device
flutter run

# Or build APK
flutter build apk --release
```

#### 4. Docker Compose (All-in-One)
```bash
# Start all services (backend + database)
docker-compose up -d

# Stop services
docker-compose down
```

---

## Development Workflow

### Backend Development
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes to FastAPI code
3. Write tests: `pytest tests/`
4. Run linter: `black app/ && ruff check app/`
5. Test locally: `uvicorn app.main:app --reload`
6. Commit and push

### Mobile App Development
1. Create feature branch
2. Implement UI/features
3. Test on device: `flutter run`
4. Write tests: `flutter test`
5. Check formatting: `flutter format lib/`
6. Analyze: `flutter analyze`
7. Commit and push

### Database Changes
1. Modify SQLAlchemy models in `backend/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`

---

## Deployment

### GCP Deployment (Production)

#### Prerequisites
- GCP project created
- gcloud CLI installed and authenticated
- Cloud SQL instance created
- Cloud Storage bucket created

#### Deploy Backend
```bash
cd backend

# Build and deploy to Cloud Run
gcloud builds submit --config cloudbuild.yaml

# Or manually
gcloud run deploy naad-bailgada-api \
  --source . \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated
```

#### Deploy Mobile App
```bash
cd mobile_app

# Build release APK
flutter build apk --release

# Upload to Google Play Console
# (Follow Google Play Store submission process)
```

See `docs/GCP_ARCHITECTURE.md` for detailed deployment instructions.

---

## API Documentation

Full API contract available in: `docs/API_CONTRACT.md`

**Base URL**: `http://localhost:8000` (local) | `https://api.naadbailgada.com` (production)

**Interactive API Docs**: `http://localhost:8000/docs` (Swagger UI)

### Key Endpoints

**Public (Mobile App)**:
- `GET /api/v1/leaderboards` - Get Top 10 bulls by region
- `GET /api/v1/bulls/{id}` - Get bull details
- `GET /api/v1/races/{id}` - Get race results

**Admin**:
- `POST /api/v1/admin/login` - Admin authentication
- `POST /api/v1/admin/bulls` - Register bull
- `POST /api/v1/admin/races` - Create race
- `POST /api/v1/admin/races/{id}/results` - Enter results

---

## Database Schema

Complete schema in: `docs/database_schema.sql`

**Core Tables**:
- `districts`, `talukas`, `tahsils`, `villages` - Regional hierarchy
- `bulls` - Bull registry
- `owners` - Owner information
- `races` - Race events
- `race_results` - Race results with timing
- `leaderboards` - Materialized monthly Top 10

---

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Mobile App Tests
```bash
cd mobile_app
flutter test
flutter test --coverage
```

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## Roadmap

See `docs/IMPLEMENTATION_ROADMAP.md` for detailed development phases.

**Phase 1**: Database + Backend API (Weeks 1-2)
**Phase 2**: Admin Panel (Weeks 3-4)
**Phase 3**: Mobile App MVP (Weeks 5-6)
**Phase 4**: Leaderboards + GCP Deployment (Weeks 7-8)

---

## License

[To be determined]

---

## Support

For issues, questions, or contributions, please contact the development team.

---

## Acknowledgments

Built to preserve and digitize Maharashtra's traditional Bailgada Sharyat racing culture.
