#!/bin/bash

# Build Docker image for Kubernetes Log Explorer

set -e

IMAGE_NAME="log-explorer"
TAG=${1:-latest}
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "🐳 Building Docker image: ${FULL_IMAGE_NAME}"

# Build the image
docker build -t "${FULL_IMAGE_NAME}" .

echo "✅ Docker image built successfully: ${FULL_IMAGE_NAME}"

# Optional: Tag for different registries
read -p "Tag for Docker registry? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter registry URL (e.g., registry.example.com): " REGISTRY
    if [ ! -z "$REGISTRY" ]; then
        REGISTRY_IMAGE="${REGISTRY}/${FULL_IMAGE_NAME}"
        docker tag "${FULL_IMAGE_NAME}" "${REGISTRY_IMAGE}"
        echo "✅ Tagged for registry: ${REGISTRY_IMAGE}"
        
        read -p "Push to registry? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker push "${REGISTRY_IMAGE}"
            echo "✅ Pushed to registry: ${REGISTRY_IMAGE}"
        fi
    fi
fi

echo "🎉 Docker build completed!"
echo ""
echo "📋 To run locally:"
echo "  docker run -p 5000:5000 -v ~/.kube/config:/home/logexplorer/.kube/config:ro ${FULL_IMAGE_NAME}"
echo ""
echo "📋 To deploy to Kubernetes:"
echo "  Update k8s-deployment.yaml with image name: ${FULL_IMAGE_NAME}"
echo "  kubectl apply -f k8s-deployment.yaml"