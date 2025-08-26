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
        -h|--help)
            echo "Usage: $0 [--push] [--tag TAG] [--registry REGISTRY] [--image-name IMAGE_NAME]"
            echo "  --push           Push images to registry after building"
            echo "  --tag TAG        Tag to use for images (default: latest)"
            echo "  --registry REG   Registry to push to (default: ghcr.io)"
            echo "  --image-name IMG Image name prefix (default: firmwaredroid/firmwaredroid)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check Docker registry authentication before building images if push is requested
if [ "$PUSH_IMAGES" = true ]; then
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Error: GITHUB_TOKEN environment variable not set. Cannot push images."
        exit 1
    fi
    echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$USER" --password-stdin
    if [ $? -ne 0 ]; then
        echo "Error: Docker login to $REGISTRY failed. Check your token and permissions."
        exit 1
    fi
    echo "Docker login to $REGISTRY succeeded."
fi

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
docker build ./firmware-droid-client/ -f ./firmware-droid-client/Dockerfile -t firmwaredroid-frontend --platform="linux/amd64"
docker tag firmwaredroid-frontend "$FRONTEND_IMAGE"

if [ "$PUSH_IMAGES" = true ]; then
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
    echo "Pushing base image..."
    docker push "$BASE_IMAGE"
fi

#####################################
# Build Nginx Image                #
#####################################
echo "Building nginx image..."
NGINX_IMAGE="${REGISTRY}/${IMAGE_NAME}-nginx:${IMAGE_TAG}"
docker build ./ -f ./Dockerfile_NGINX -t firmwaredroid-nginx --platform="linux/amd64"
docker tag firmwaredroid-nginx "$NGINX_IMAGE"

if [ "$PUSH_IMAGES" = true ]; then
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

    docker build ./docker/base/ -f "./docker/base/Dockerfile_${worker_name}" -t "$local_tag" --platform="linux/amd64"
    docker tag "$local_tag" "$registry_tag"

    worker_names+=("$worker_name")
    worker_tags+=("$registry_tag")

    if [ "$PUSH_IMAGES" = true ]; then
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

echo
echo "Build completed successfully!"
echo
echo "Built images:"
echo "  Frontend: $FRONTEND_IMAGE"
echo "  Base: $BASE_IMAGE"
echo "  Nginx: $NGINX_IMAGE"
for worker_name in "${!worker_images[@]}"; do
    echo "  ${worker_name^} Worker: ${worker_images[$worker_name]}"
done

if [ "$PUSH_IMAGES" = true ]; then
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
$(for worker_name in "${!worker_images[@]}"; do
    echo "    \"${worker_name}\": \"${worker_images[$worker_name]}\","
done | sed '$ s/,$//')
  },
  "description": "FirmwareDroid Docker image bundle for version ${IMAGE_TAG}. All images in this bundle are designed to work together."
}
EOF
    
    echo "Generated image manifest: image-manifest.json"
fi