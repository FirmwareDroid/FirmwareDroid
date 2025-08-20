# FirmwareDroid GitHub Copilot Instructions

**ALWAYS follow these instructions first. Only use additional search or bash commands when the information here is incomplete or found to be in error.**

FirmwareDroid is a Python Django web application for automated static analysis of Android firmware and APK files. It runs as a containerized multi-service application with MongoDB, Redis, and multiple specialized worker containers for different analysis tasks.

## Quick Start & Environment Setup

**CRITICAL SETUP REQUIREMENT:** Create missing frontend directory before setup:
```bash
mkdir -p firmware-droid-client/src
```

Run setup script to configure environment:
```bash
python setup.py
```
- **Time:** ~30 seconds. NEVER CANCEL.
- **Creates:** `.env` file, environment directories, SSL certificates, database configs
- **Default mode:** Development settings (use `-p` flag for production)

## Dependencies & Build Process

### Python Dependencies
Install core requirements (required before any Django commands):
```bash
pip install -r requirements.txt
```
- **Time:** ~2 minutes. NEVER CANCEL. Set timeout to 5+ minutes.
- **May fail:** SSL/network issues in some environments. Document if fails: "pip install fails due to network/SSL limitations"

Install backend-specific requirements (if needed):
```bash
pip install -r requirements/requirements_backend.txt
```
- **May fail:** Network timeouts. Document the issue.

### Docker Build Process
**CRITICAL:** Docker builds may take 45+ minutes. NEVER CANCEL builds or long-running commands.

Build base image:
```bash
docker build ./ -f ./Dockerfile_BASE -t firmwaredroid-base --platform="linux/amd64"
```
- **Time:** 20-45 minutes. NEVER CANCEL. Set timeout to 60+ minutes.
- **May fail:** SSL certificate verification issues with PyPI in some environments

Build all worker images:
```bash
./docker/build_docker_images.sh
```
- **Time:** 45+ minutes. NEVER CANCEL. Set timeout to 90+ minutes.
- **Note:** Builds frontend, backend, and multiple worker containers in parallel

Build with docker-compose:
```bash
docker compose build
```
- **Time:** 30-60 minutes. NEVER CANCEL. Set timeout to 90+ minutes.

## Running the Application

**PREFERRED METHOD:** Use Docker Compose for full functionality:
```bash
docker compose up -d
```

**Development mode:** Individual services (requires running setup first):
```bash
# Start dependencies first
docker compose up -d mongo-db-1 redis

# Run Django development server (REQUIRES all Python dependencies)
cd source
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:5000
```

**Production mode:** Uses gunicorn (see `docker_entrypoint.sh`)

## Validation & Testing

### Manual Validation Scenarios
**ALWAYS run these validation steps after making changes:**

1. **Health Check:** Verify basic application startup
   ```bash
   curl http://localhost/api/health/
   ```

2. **Django Admin Access:** Test admin interface
   - Navigate to `http://localhost/admin/`
   - Use credentials from `.env` file (`DJANGO_SUPERUSER_USERNAME`/`DJANGO_SUPERUSER_PASSWORD`)

3. **API Endpoints:** Test core REST and GraphQL APIs
   ```bash
   curl http://localhost/api/
   curl http://localhost/graphql/
   ```

4. **Worker Status:** Check Redis queues are working
   ```bash
   curl http://localhost/django-rq/
   ```

### Test Suite
**LIMITED TESTING AVAILABLE:**
```bash
python -m unittest source/setup/tests.py
```
- **Note:** Minimal test coverage - mainly Django boilerplate tests
- **Integration tests:** Require full Docker stack running

## Common Issues & Workarounds

### Setup Issues
- **Frontend directory missing:** Run `mkdir -p firmware-droid-client/src` before setup
- **'.env file already exists':** Delete `.env` and re-run setup

### Build Issues  
- **Docker SSL errors:** Network/firewall limitations. Document as "Docker builds fail due to SSL limitations"
- **pip timeout errors:** Use `--timeout 300` flag or document network issues
- **Missing dependencies:** Install `requirements/requirements_backend.txt` first

### Runtime Issues
- **'redis_lock' module missing:** Install `python-redis-lock` or document network issue
- **MongoDB connection errors:** Ensure MongoDB container is running first
- **Django import errors:** Set `PYTHONPATH="/path/to/source:$PYTHONPATH"`

## Project Structure & Key Files

### Repository Layout
```
/
├── setup.py                    # Environment setup script
├── docker-compose.yml         # Main service orchestration
├── source/                    # Django application code
│   ├── manage.py             # Django management
│   ├── webserver/            # Django settings & URLs
│   ├── api/                  # REST API endpoints
│   └── static_analysis/      # Analysis tool integrations
├── docker/                   # Docker build files
│   └── build_docker_images.sh # Build script
├── requirements/             # Dependency files per module
└── templates/               # Configuration templates
```

### Important Configuration Files
- **`.env`:** Environment variables (created by setup.py)
- **`docker-compose.yml`:** Service definitions and volumes
- **`source/webserver/settings.py`:** Django configuration
- **`requirements.txt`:** Core Python dependencies

### Analysis Modules
FirmwareDroid includes these static analysis tools:
- AndroGuard, APKiD, APKLeaks, FlowDroid, Trueseeing, Quark-Engine
- Each has separate requirements file in `requirements/`

## Development Guidelines

### Making Code Changes
1. **ALWAYS validate setup works first:** Run setup.py and verify .env creation
2. **Install dependencies:** Core requirements + backend requirements  
3. **Test Django commands:** Verify `python manage.py check` works
4. **Manual validation:** Test API endpoints and admin interface
5. **Docker validation:** Build and run full stack if possible

### Timeout Guidelines
- **Setup commands:** 5+ minutes timeout
- **Python installs:** 5+ minutes timeout  
- **Docker builds:** 60-90+ minutes timeout
- **NEVER CANCEL:** Long builds are normal - wait for completion

### Required Environment
- **Python:** 3.11+ (tested with 3.12)
- **Docker:** Latest version with docker-compose
- **Memory:** 10GB+ recommended for Docker builds
- **Network:** Internet access for package installation

## Debugging Common Tasks

### "Django won't start"
1. Check if setup.py completed successfully
2. Verify all Python dependencies installed
3. Check PYTHONPATH includes source directory
4. Ensure MongoDB/Redis containers running if using Docker

### "Docker build fails"
1. Check network connectivity
2. Verify sufficient disk space (10GB+)
3. Try building base image first, then workers
4. Document SSL/network issues if persistent

### "Can't access web interface"
1. Verify services running: `docker compose ps`
2. Check nginx configuration in `env/nginx/`
3. Verify port mappings (80/443 for production, 5000 for dev)
4. Check logs: `docker compose logs nginx web`

**Remember:** FirmwareDroid is designed as a research tool. Many components require the full Docker stack to function properly.