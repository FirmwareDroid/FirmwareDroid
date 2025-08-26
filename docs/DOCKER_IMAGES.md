# FirmwareDroid Docker Images

This document describes how to use the published FirmwareDroid Docker images from GitHub Container Registry.

## Available Images

All FirmwareDroid Docker images are published to GitHub Container Registry and are logically bundled together. They are designed to work as a complete system and should be used together.

### Image Registry

All images are available at: `ghcr.io/firmwaredroid/firmwaredroid-*`

### Image Components

| Component | Image Name | Description |
|-----------|------------|-------------|
| Base | `ghcr.io/firmwaredroid/firmwaredroid-base` | Base image with common dependencies |
| Frontend | `ghcr.io/firmwaredroid/firmwaredroid-frontend` | Web frontend (nginx-based) |
| Backend | `ghcr.io/firmwaredroid/firmwaredroid-backend` | Main web application backend |
| Nginx | `ghcr.io/firmwaredroid/firmwaredroid-nginx` | Reverse proxy and static file server |
| Extractor | `ghcr.io/firmwaredroid/firmwaredroid-extractor` | Firmware extraction worker |
| APK Scanner | `ghcr.io/firmwaredroid/firmwaredroid-apk-scanner` | APK analysis worker |

## Usage

### Quick Start with Release Images

1. **Copy the release docker-compose configuration:**
   ```bash
   cp docker-compose-release.yml docker-compose.yml
   ```

2. **Set up your environment:**
   ```bash
   python setup.py
   ```

3. **Start the services:**
   ```bash
   docker compose up -d
   ```

### Using Specific Versions

Images are tagged with release versions. To use a specific version, update the image tags in your `docker-compose.yml`:

```yaml
services:
  web:
    image: ghcr.io/firmwaredroid/firmwaredroid-backend:v1.0.0
  nginx:
    image: ghcr.io/firmwaredroid/firmwaredroid-nginx:v1.0.0
  extractor-worker-high-1:
    image: ghcr.io/firmwaredroid/firmwaredroid-extractor:v1.0.0
  apk_scanner-worker-1:
    image: ghcr.io/firmwaredroid/firmwaredroid-apk-scanner:v1.0.0
```

### Available Tags

- `latest` - Latest build from the main branch
- `v*.*.*` - Specific release versions (e.g., `v1.0.0`, `v1.1.0`)

## Image Manifest

Each release includes an `image-manifest.json` file that provides metadata about the image bundle:

```json
{
  "version": "v1.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "images": {
    "base": "ghcr.io/firmwaredroid/firmwaredroid-base:v1.0.0",
    "frontend": "ghcr.io/firmwaredroid/firmwaredroid-frontend:v1.0.0",
    "nginx": "ghcr.io/firmwaredroid/firmwaredroid-nginx:v1.0.0",
    "backend": "ghcr.io/firmwaredroid/firmwaredroid-backend:v1.0.0",
    "extractor": "ghcr.io/firmwaredroid/firmwaredroid-extractor:v1.0.0",
    "apk-scanner": "ghcr.io/firmwaredroid/firmwaredroid-apk-scanner:v1.0.0"
  },
  "description": "FirmwareDroid Docker image bundle for version v1.0.0. All images in this bundle are designed to work together."
}
```

## Building Your Own Images

If you prefer to build images locally, you can use the provided build script:

```bash
# Build locally
./docker/build_and_push_images.sh

# Build and push to your own registry
./docker/build_and_push_images.sh --push --tag my-version --registry my-registry.com --image-name my-org/firmwaredroid
```

## Migration from Local Build

To migrate from a local build setup to using published images:

1. **Backup your current configuration:**
   ```bash
   cp docker-compose.yml docker-compose-local.yml.bak
   ```

2. **Update to use published images:**
   ```bash
   cp docker-compose-release.yml docker-compose.yml
   ```

3. **Verify your environment configuration:**
   - Ensure your `.env` file is properly configured
   - Check that all volume mounts and paths are correct

4. **Test the deployment:**
   ```bash
   docker compose down
   docker compose pull  # Pull latest published images
   docker compose up -d
   ```

## Troubleshooting

### Image Pull Issues

If you encounter issues pulling images, ensure you have the proper permissions:

```bash
# For public images, no authentication is needed
docker pull ghcr.io/firmwaredroid/firmwaredroid-backend:latest

# For private repositories, authenticate first
echo $GITHUB_TOKEN | docker login ghcr.io -u username --password-stdin
```

### Version Compatibility

Always use images from the same version bundle. Mixing different versions may cause compatibility issues.

### Storage and Volumes

The published images expect the same volume mounts and storage configuration as the local build. Ensure your `.env` file and volume paths are properly configured.

## Support

For issues related to the Docker images or deployment:

1. Check the [GitHub Issues](https://github.com/FirmwareDroid/FirmwareDroid/issues)
2. Refer to the main [FirmwareDroid documentation](https://github.com/FirmwareDroid/FirmwareDroid)
3. Review the image manifest for version compatibility information