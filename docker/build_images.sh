#!/bin/bash

# Script that builds and optionally pushes all docker images for FirmwareDroid
# Usage: 
#   Local build: ./docker/build_and_push_images.sh
#   Release build: ./docker/build_and_push_images.sh --push --tag v1.0.0

set -e

# Default values
PUSH_IMAGES=false
IMAGE_TAG="latest"
REGISTRY="ghcr.io"
IMAGE_NAME="firmwaredroid/firmwaredroid"
SEC_TEST=false
NO_LOGIN=false
DOCKER_USERNAME=""
DOCKER_PASSWORD=""
SKIP_SECURITY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH_IMAGES=true
            shift
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --sec-test)
            SEC_TEST=true
            shift
            ;;
        --no-login)
            NO_LOGIN=true
            shift
            ;;
        --username)
            DOCKER_USERNAME="$2"
            shift 2
            ;;
        --password)
            DOCKER_PASSWORD="$2"
            shift 2
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--push] [--tag TAG] [--registry REGISTRY] [--image-name IMAGE_NAME] [--no-login] [--username USER --password PASS]"
            echo "  --push           Push images to registry after building"
            echo "  --tag TAG        Tag to use for images (default: latest)"
            echo "  --registry REG   Registry to push to (default: ghcr.io)"
            echo "  --image-name IMG Image name prefix (default: firmwaredroid/firmwaredroid)"
            echo "  --no-login       Do not perform docker login (assume user already authenticated)"
            echo "  --username USER  Docker registry username (can also be provided via DOCKER_USERNAME env var)"
            echo "  --password PASS  Docker registry password (can also be provided via DOCKER_PASSWORD env var)"
            echo "  --skip-security  Skip all Trivy security scans (do not run sec-test or push-time scans)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Decide whether to actually push images. If --dry-run is set, do not push even if --push was used.
DO_PUSH=false
if [ "$PUSH_IMAGES" = true ]; then
    DO_PUSH=true
fi

# Check Docker registry authentication before building images if an actual push is requested
if [ "$DO_PUSH" = true ]; then
    if [ "$NO_LOGIN" = true ]; then
        echo "Skipping docker login as requested (--no-login). Ensure you are already authenticated with $REGISTRY."
    else
        # Prefer explicit username/password if provided, then GITHUB_TOKEN, otherwise fail.
        if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
            echo "Logging in to $REGISTRY with provided username..."
            echo "$DOCKER_PASSWORD" | docker login "$REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
        elif [ -n "$DOCKER_USERNAME" ] && [ -z "$DOCKER_PASSWORD" ]; then
            echo "Error: --username provided without --password."
            exit 1
        elif [ -n "$GITHUB_TOKEN" ]; then
            echo "Logging in to $REGISTRY with GITHUB_TOKEN..."
            echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$USER" --password-stdin
        else
            echo "Error: No credentials provided. Provide DOCKER_USERNAME/DOCKER_PASSWORD, GITHUB_TOKEN, or use --no-login if already authenticated."
            exit 1
        fi
        if [ $? -ne 0 ]; then
            echo "Error: Docker login to $REGISTRY failed. Check your credentials and permissions."
            exit 1
        fi
        echo "Docker login to $REGISTRY succeeded."
    fi
fi

# Trivy configuration (used when pushing images)
# Set TRIVY_SEVERITY to control which severities should block pushes (default: HIGH,CRITICAL)
# Trivy configuration (used when pushing images)
# Set TRIVY_SEVERITY to control which severities should block pushes (default: HIGH,CRITICAL)
: "${TRIVY_SEVERITY:=HIGH,CRITICAL}"
# Pin a recommended Trivy image.
: "${TRIVY_IMAGE:=aquasec/trivy:0.69.3}"

# Helper: ensure the Trivy image exists locally. If not, print a clear
# install instruction and abort. We intentionally print the exact message
# the user requested when the image is missing.
ensure_trivy_present() {
    if ! docker image inspect "$TRIVY_IMAGE" >/dev/null 2>&1; then
        echo "ERROR: Trivy image $TRIVY_IMAGE not found locally."
        echo "Install Image with: docker pull aquasec/trivy:0.69.3"
        exit 1
    fi
}


# Function: scan_image IMAGE
# Runs Trivy in a docker container to scan the given image. If vulnerabilities of the
# configured severities are found, Trivy will exit with code 1 (we treat that as blocking).
scan_image() {
    local image="$1"
    echo "Scanning image $image with Trivy (severity: $TRIVY_SEVERITY)..."

    # Run Trivy via Docker to avoid requiring a local installation.
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "$HOME/.cache/trivy":/root/.cache/ "$TRIVY_IMAGE" image \
        --severity "$TRIVY_SEVERITY" --exit-code 1 --no-progress "$image"
    local rc=$?
    if [ $rc -eq 0 ]; then
        echo "Trivy: no $TRIVY_SEVERITY vulnerabilities found in $image"
        return 0
    elif [ $rc -eq 1 ]; then
        echo "Trivy: vulnerabilities of severity $TRIVY_SEVERITY found in $image. Push aborted."
        return 1
    else
        echo "Trivy: scanner error (exit code $rc) while scanning $image. Aborting push."
        return 2
    fi
}

# Run a scan and, if vulnerabilities are found, interactively ask the user whether
# to continue with the push. In non-interactive environments the behavior can be
# overridden with ALLOW_PUSH_ON_VULNS=true.
scan_and_confirm_push() {
    local image="$1"
    ensure_trivy_present
    echo "Scanning image $image with Trivy (severity: $TRIVY_SEVERITY)..."
    scan_image "$image"
    local rc=$?
    if [ $rc -eq 0 ]; then
        return 0
    fi
    if [ $rc -eq 1 ]; then
        # Vulnerabilities found
        if [ -t 0 ]; then
            # Interactive terminal: ask the user
            while true; do
                read -r -p "Vulnerabilities found in $image. Push anyway? [y/N] " ans
                case "$ans" in
                    [yY]|[yY][eE][sS])
                        echo "User accepted pushing despite vulnerabilities."
                        return 0
                        ;;
                    [nN]|"" )
                        echo "Aborting push for $image due to vulnerabilities."
                        exit 1
                        ;;
                    *) echo "Please answer 'y' or 'n'." ;;
                esac
            done
        else
            # Non-interactive: respect ALLOW_PUSH_ON_VULNS env var
            if [ "${ALLOW_PUSH_ON_VULNS:-false}" = "true" ]; then
                echo "Non-interactive: ALLOW_PUSH_ON_VULNS=true, continuing push despite vulnerabilities."
                return 0
            else
                echo "Non-interactive environment and vulnerabilities found; aborting push."
                echo "Set ALLOW_PUSH_ON_VULNS=true to override."
                exit 1
            fi
        fi
    else
        # rc == 2 or other: scanner error
        echo "Scanner error (exit code $rc) while scanning $image. Aborting push."
        exit 1
    fi
}

echo "Building FirmwareDroid Docker images..."
echo "Registry: $REGISTRY"
echo "Image name: $IMAGE_NAME"
echo "Tag: $IMAGE_TAG"
echo "Push images: $PUSH_IMAGES"
echo

#####################################
# Build Frontend                    #
#####################################
echo "Building frontend image..."
FRONTEND_IMAGE="${REGISTRY}/${IMAGE_NAME}-frontend:${IMAGE_TAG}"
# Use repository root as build context so the root .dockerignore is respected
docker build ./firmware-droid-client -f ./firmware-droid-client/Dockerfile -t firmwaredroid-frontend --platform="linux/amd64"
docker tag firmwaredroid-frontend "$FRONTEND_IMAGE"

if [ "$PUSH_IMAGES" = true ]; then
    if [ "$SKIP_SECURITY" = true ]; then
        echo "Skipping security scan for frontend image (requested via --skip-security)."
    else
        scan_and_confirm_push "$FRONTEND_IMAGE"
    fi
fi

if [ "$DO_PUSH" = true ]; then
    echo "Pushing frontend image..."
    docker push "$FRONTEND_IMAGE"
fi

#####################################
# Build Base Image                 #
#####################################
echo "Building base image..."
BASE_IMAGE="${REGISTRY}/${IMAGE_NAME}-base:${IMAGE_TAG}"
docker build ./ -f ./Dockerfile_BASE -t firmwaredroid-base --platform="linux/amd64"
docker tag firmwaredroid-base "$BASE_IMAGE"

if [ "$PUSH_IMAGES" = true ]; then
    if [ "$SKIP_SECURITY" = true ]; then
        echo "Skipping security scan for base image (requested via --skip-security)."
    else
        scan_and_confirm_push "$BASE_IMAGE"
    fi
fi

if [ "$DO_PUSH" = true ]; then
    echo "Pushing base image..."
    docker push "$BASE_IMAGE"
fi

#####################################
# Build Nginx Image                #
#####################################
echo "Building nginx image..."
NGINX_IMAGE="${REGISTRY}/${IMAGE_NAME}-nginx:${IMAGE_TAG}"
# Pass the built/pushed frontend image as a build-arg so the nginx Dockerfile
# can COPY files from that image. FRONTEND_IMAGE was defined earlier.
docker build ./ -f ./Dockerfile_NGINX -t firmwaredroid-nginx --platform="linux/amd64" \
    --build-arg FRONTEND_IMAGE="${FRONTEND_IMAGE}"
docker tag firmwaredroid-nginx "$NGINX_IMAGE"

if [ "$PUSH_IMAGES" = true ]; then
    if [ "$SKIP_SECURITY" = true ]; then
        echo "Skipping security scan for nginx image (requested via --skip-security)."
    else
        scan_and_confirm_push "$NGINX_IMAGE"
    fi
fi

if [ "$DO_PUSH" = true ]; then
    echo "Pushing nginx image..."
    docker push "$NGINX_IMAGE"
fi

#####################################
# Build Worker Images              #
#####################################
workers=(./docker/base/Dockerfile_*)
echo "Building worker images. This may take some time..."

# Instead of declare -A worker_images
worker_names=()
worker_tags=()

for dockerfile in "${workers[@]}"; do
    worker_name=$(basename "$dockerfile" | sed 's/Dockerfile_//')
    local_tag="${worker_name}-worker"
    registry_tag="${REGISTRY}/${IMAGE_NAME}-${worker_name}:${IMAGE_TAG}"

    # Use repository root as build context so root .dockerignore is applied
    docker build . -f "./docker/base/Dockerfile_${worker_name}" -t "$local_tag" --platform="linux/amd64"
    docker tag "$local_tag" "$registry_tag"

    worker_names+=("$worker_name")
    worker_tags+=("$registry_tag")

    if [ "$PUSH_IMAGES" = true ]; then
        if [ "$SKIP_SECURITY" = true ]; then
            echo "Skipping security scan for $worker_name worker image (requested via --skip-security)."
        else
            scan_and_confirm_push "$registry_tag"
        fi
    fi

    if [ "$DO_PUSH" = true ]; then
        echo "Pushing $worker_name worker image..."
        docker push "$registry_tag"
    fi
done

# When printing built images:
for i in "${!worker_names[@]}"; do
    echo "  ${worker_names[$i]^} Worker: ${worker_tags[$i]}"
done

# When generating manifest:
for i in "${!worker_names[@]}"; do
    echo "    \"${worker_names[$i]}\": \"${worker_tags[$i]}\","
done | sed '$ s/,$//'

#####################################
# Build docker-compose images      #
#####################################
echo "Building docker-compose images..."
docker compose build

if [ "$SEC_TEST" = true ]; then
    if [ "$SKIP_SECURITY" = true ]; then
        echo "SEC_TEST requested but skipping security tests because --skip-security was set."
    else
        # Run security tests against all built images
        ensure_trivy_present
        echo "Running security tests (sec-test) against all built images..."
        failed=0
        scan_image "$FRONTEND_IMAGE" || failed=1
        scan_image "$BASE_IMAGE" || failed=1
        scan_image "$NGINX_IMAGE" || failed=1
        for tag in "${worker_tags[@]}"; do
            scan_image "$tag" || failed=1
        done
        if [ $failed -ne 0 ]; then
            echo "One or more images failed the security scan."
            exit 1
        else
            echo "All images passed the security scan."
        fi
    fi
fi

echo
echo "Build completed successfully!"
echo
echo "Built images:"
echo "  Frontend: $FRONTEND_IMAGE"
echo "  Base: $BASE_IMAGE"
echo "  Nginx: $NGINX_IMAGE"
for i in "${!worker_names[@]}"; do
    echo "  ${worker_names[$i]^} Worker: ${worker_tags[$i]}"
done

if [ "$DO_PUSH" = true ]; then
    echo
    echo "All images have been pushed to the registry."
    
    # Generate image manifest
    cat << EOF > image-manifest.json
{
  "version": "${IMAGE_TAG}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "images": {
    "base": "${BASE_IMAGE}",
    "frontend": "${FRONTEND_IMAGE}",
    "nginx": "${NGINX_IMAGE}",
$(for i in "${!worker_names[@]}"; do
    echo "    \"${worker_names[$i]}\": \"${worker_tags[$i]}\","
done | sed '$ s/,$//')
  },
  "description": "FirmwareDroid Docker image bundle for version ${IMAGE_TAG}. All images in this bundle are designed to work together."
}
EOF
    
    echo "Generated image manifest: image-manifest.json"
fi
if [ "$DRY_RUN" = true ] && [ "$DO_PUSH" = false ]; then
    echo
    echo "Dry-run complete: images were built and scanned but NOT pushed to the registry."
fi
