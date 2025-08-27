# FirmwareDroid Setup Guide

FirmwareDroid now supports multiple setup options to improve usability. Choose the approach that best fits your needs.

## Quick Start (Recommended)

The simplest way to get FirmwareDroid running:

```bash
git clone --recurse-submodules https://github.com/FirmwareDroid/FirmwareDroid.git
cd FirmwareDroid
docker compose up
```

This will automatically:
- Use `default.env` for configuration
- Create necessary directories (`data/`, `env/`)
- Generate SSL certificates and configuration files
- Start all services

Access FirmwareDroid at: `https://fmd.localhost`  
Default admin credentials: **`fmd-admin`** / **`admin`**

## Setup Options

### Option 1: One-Command Start
```bash
docker compose up
```
- Uses built-in defaults
- Creates config automatically on first run
- Best for development and testing

### Option 2: Quick Setup Script
```bash
./quick_setup.sh
docker compose up
```
- Pre-creates directories and `.env` file
- Gives you control over the setup process
- Shows what will be created

### Option 3: Custom Configuration (Advanced)
```bash
python setup.py  # Interactive configuration
docker compose up
```
- Full interactive setup with custom options
- Production-ready configuration
- Advanced storage and security settings

### Option 4: Published Images
```bash
./quick_setup.sh  # Create config
docker compose -f docker-compose-release.yml up
```
- Uses pre-built images from GitHub Container Registry
- Faster startup (no build time)
- Good for production deployments

## Configuration Files

### Default Configuration (`default.env`)
Contains sensible defaults:
- Development mode enabled
- Data stored in `./data/` directory
- Default passwords for databases
- Memory limits: 10GB RAM, 0.5 CPU cores

### Custom Configuration (`.env`)
- Created by copying `default.env` or running `setup.py`
- Edit this file to customize your installation
- Takes precedence over `default.env`

## Directory Structure

After setup, you'll have:
```
FirmwareDroid/
├── data/                          # Storage for analysis data
│   ├── 00_file_storage/          # File storage partitions
│   ├── ...
│   ├── 09_file_storage/
│   ├── django_database/          # Web app database
│   └── mongo_database/           # MongoDB data
├── env/                          # Service configurations
│   ├── nginx/                    # Web server config & SSL
│   ├── redis/                    # Redis configuration
│   └── mongo/                    # MongoDB setup scripts
├── .env                          # Your configuration (if created)
└── default.env                  # Default configuration
```

## Upgrading from Previous Versions

If you were using the old setup method:

1. **Backup your data**:
   ```bash
   cp -r blob_storage/ blob_storage.backup/
   cp .env .env.backup
   ```

2. **Use new structure** (optional):
   ```bash
   rm -rf .env  # Remove old config
   ./quick_setup.sh  # Create new config
   # Manually copy any custom settings from .env.backup to .env
   ```

3. **Keep old structure**:
   - Your existing setup will continue to work
   - The new auto-setup is only used when `.env` doesn't exist

## Troubleshooting

### "Permission denied" errors
```bash
sudo chown -R $USER:$USER data/ env/
chmod -R 755 data/ env/
```

### "Cannot find .env file"
```bash
cp default.env .env
```

### Services fail to start
1. Check if ports are available: `docker compose ps`
2. View logs: `docker compose logs <service-name>`
3. Reset environment: `rm -rf data/ env/ .env && ./quick_setup.sh`

### Want to start fresh
```bash
docker compose down -v  # Stop and remove volumes
rm -rf data/ env/ .env  # Remove all generated files
docker compose up       # Start with fresh defaults
```

## Security Notes

- **Change default passwords** in production
- **Use HTTPS** with proper certificates (not self-signed)
- **Limit network access** to required services only
- **Regular backups** of the `data/` directory

For production deployments, always run `python setup.py -p` for production-specific configuration.