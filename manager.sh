#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="parkalot-rg"
ACR_NAME="parkalotacr7620"
IMAGE_NAME="parkalot"
TAG="latest"

# Function to deploy (build and push image)
deploy() {
    echo -e "${BLUE}Building and pushing Docker image...${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}Error: Dockerfile not found. Run this from the parkalot-func directory${NC}"
        return 1
    fi
    
    # Login to ACR
    echo -e "${YELLOW}Logging into ACR...${NC}"
    az acr login --name "$ACR_NAME"
    
    # Build image
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t "$IMAGE_NAME:$TAG" .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to build image${NC}"
        return 1
    fi
    
    # Tag for ACR
    echo -e "${YELLOW}Tagging image for ACR...${NC}"
    docker tag "$IMAGE_NAME:$TAG" "$ACR_NAME.azurecr.io/$IMAGE_NAME:$TAG"
    
    # Push to ACR
    echo -e "${YELLOW}Pushing to ACR...${NC}"
    docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME:$TAG"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Image deployed successfully!${NC}"
        echo -e "${GREEN}Logic App will use new image on next run${NC}"
    else
        echo -e "${RED}Failed to push image${NC}"
        return 1
    fi
}

# Function to list all containers
list_containers() {
    echo -e "${BLUE}Listing all Parkalot containers...${NC}"
    az container list --resource-group "$RESOURCE_GROUP" \
        --query "[?starts_with(name, 'parkalot-runner')].{Name:name, Status:instanceView.state, Started:instanceView.state.startTime}" \
        --output table
}

# Function to show latest logs
show_latest_logs() {
    echo -e "${BLUE}Fetching logs from most recent container...${NC}"
    
    LATEST=$(az container list --resource-group "$RESOURCE_GROUP" \
        --query "[?starts_with(name, 'parkalot-runner')].name" -o tsv | sort | tail -1)
    
    if [ -z "$LATEST" ]; then
        echo -e "${RED}No containers found${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Container: $LATEST${NC}"
    echo ""
    az container logs --resource-group "$RESOURCE_GROUP" --name "$LATEST"
}

# Function to clean up old containers
cleanup_old_containers() {
    echo -e "${YELLOW}Finding old containers to clean up...${NC}"
    
    OLD_CONTAINERS=$(az container list --resource-group "$RESOURCE_GROUP" \
        --query "[?starts_with(name, 'parkalot-runner') && instanceView.state=='Succeeded'].name" -o tsv)
    
    if [ -z "$OLD_CONTAINERS" ]; then
        echo -e "${GREEN}No old containers to clean up${NC}"
        return 0
    fi
    
    COUNT=$(echo "$OLD_CONTAINERS" | wc -l)
    echo -e "${YELLOW}Found $COUNT old container(s)${NC}"
    echo "$OLD_CONTAINERS"
    echo ""
    read -p "Delete these containers? (y/n): " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "$OLD_CONTAINERS" | while read container; do
            echo -e "${BLUE}Deleting $container...${NC}"
            az container delete --resource-group "$RESOURCE_GROUP" --name "$container" --yes
        done
        echo -e "${GREEN}✅ Cleanup complete!${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled${NC}"
    fi
}

# Function to check Logic App status
check_logic_app() {
    echo -e "${BLUE}Checking Logic App status...${NC}"
    
    az logic workflow show \
        --resource-group "$RESOURCE_GROUP" \
        --name "parkalot-scheduler-v2" \
        --query "{Name:name, State:state, Location:location, NextRun:'Not available via CLI'}" \
        --output table
    
    echo ""
    echo -e "${YELLOW}To view run history and next run time:${NC}"
    echo "Visit: https://portal.azure.com → parkalot-scheduler-v2 → Overview"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Parkalot Container Manager (v2)      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "1) 🚀 Deploy (Build & Push Image)"
    echo "2) 📋 List All Containers"
    echo "3) 📄 Show Latest Logs"
    echo "4) 🧹 Clean Up Old Containers"
    echo "5) ⚙️  Check Logic App Status"
    echo "6) 🚪 Quit"
    echo ""
    read -p "Enter your choice [1-6]: " choice
}

# Main loop
while true; do
    show_menu
    case $choice in
        1)
            deploy
            ;;
        2)
            list_containers
            ;;
        3)
            show_latest_logs
            ;;
        4)
            cleanup_old_containers
            ;;
        5)
            check_logic_app
            ;;
        6)
            echo -e "${BLUE}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please choose 1-6${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done