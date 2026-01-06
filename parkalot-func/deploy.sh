#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Required variables
: "${ACR:?}"
: "${IMAGE_NAME:?}"
: "${TAG:?}"

# Login to ACR
echo "→ Logging into ACR $ACR..."
az acr login --name "$ACR"

# Build Docker image
echo "→ Building image $IMAGE_NAME:$TAG..."
docker build -t "$IMAGE_NAME:$TAG" .

# Tag and push to ACR
echo "→ Tagging image for ACR..."
docker tag "$IMAGE_NAME:$TAG" "$ACR.azurecr.io/$IMAGE_NAME:$TAG"
echo "→ Pushing to ACR..."
docker push "$ACR.azurecr.io/$IMAGE_NAME:$TAG"

echo "✅ Image pushed to ACR. Logic App will use latest image on next run."