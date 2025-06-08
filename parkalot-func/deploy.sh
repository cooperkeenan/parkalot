#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env
if [ -f .env ]; then
  set -a
  source .env
  set +a
else
  echo ".env file not found! Aborting."
  exit 1
fi

# Required variables
: "${RG:?}"               # Resource group
: "${ACR:?}"              # Azure Container Registry name
: "${ACR_USER:?}"         # ACR admin username
: "${ACR_PASS:?}"         # ACR admin password
: "${IMAGE_NAME:?}"       # Docker image name (local)
: "${TAG:?}"              # Docker image tag
: "${CONTAINER_NAME:=parkalot-cron}"  # Azure Container Instance name

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

# Delete existing container instance if present
echo "→ Checking for existing container group $CONTAINER_NAME..."
if az container show --resource-group "$RG" --name "$CONTAINER_NAME" &>/dev/null; then
  echo "  → Found existing, deleting..."
  az container delete --resource-group "$RG" --name "$CONTAINER_NAME" --yes
fi

# Create or recreate container instance
echo "→ Creating container group $CONTAINER_NAME..."
az container create \
  --resource-group "$RG" \
  --name "$CONTAINER_NAME" \
  --image "$ACR.azurecr.io/$IMAGE_NAME:$TAG" \
  --registry-login-server "$ACR.azurecr.io" \
  --registry-username "$ACR_USER" \
  --registry-password "$ACR_PASS" \
  --cpu 0.5 --memory 1 \
  --os-type Linux \
  --restart-policy OnFailure \
  --environment-variables \
      PARKALOT_USER="$PARKALOT_USER" \
      PARKALOT_PASS="$PARKALOT_PASS"

echo " "
echo " Deployment complete."

