#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Container details
RESOURCE_GROUP="parkalot-rg"
CONTAINER_NAME="parkalot-cron"

# Function to check if container exists
container_exists() {
    az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" &> /dev/null
    return $?
}

# Function to show container status
show_status() {
    echo -e "${BLUE}Checking container status...${NC}"
    if container_exists; then
        az container show \
            --resource-group "$RESOURCE_GROUP" \
            --name "$CONTAINER_NAME" \
            --query "{Name:name, State:instanceView.state, ProvisioningState:provisioningState, RestartCount:instanceView.restartCount, StartTime:instanceView.events[0].lastTimestamp, CPU:containers[0].resources.requests.cpu, Memory:containers[0].resources.requests.memoryInGb}" \
            --output table
    else
        echo -e "${RED}Container '$CONTAINER_NAME' does not exist${NC}"
    fi
}

# Function to show container logs
show_logs() {
    echo -e "${BLUE}Fetching container logs...${NC}"
    if container_exists; then
        az container logs \
            --resource-group "$RESOURCE_GROUP" \
            --name "$CONTAINER_NAME"
    else
        echo -e "${RED}Container '$CONTAINER_NAME' does not exist${NC}"
    fi
}

# Function to stream logs
stream_logs() {
    echo -e "${BLUE}Streaming container logs (Ctrl+C to stop)...${NC}"
    if container_exists; then
        az container logs \
            --resource-group "$RESOURCE_GROUP" \
            --name "$CONTAINER_NAME" \
            --follow
    else
        echo -e "${RED}Container '$CONTAINER_NAME' does not exist${NC}"
    fi
}

# Function to start container
start_container() {
    echo -e "${BLUE}Starting container...${NC}"
    
    # Get ACR password
    ACR_PASSWORD=$(az acr credential show --name parkalotacr7620 --query "passwords[0].value" -o tsv)
    
    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --image parkalotacr7620.azurecr.io/parkalot:latest \
        --cpu 0.5 \
        --memory 1 \
	--os-type Linux \
        --registry-login-server parkalotacr7620.azurecr.io \
        --registry-username parkalotacr7620 \
        --registry-password "$ACR_PASSWORD" \
        --environment-variables \
            PARKALOT_USER="${PARKALOT_USER:-ckeenan@craneware.com}" \
            PARKALOT_PASS="${PARKALOT_PASS:-ApolloTheGreat!0}" \
        --restart-policy Never \
        --location uksouth
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Container started successfully!${NC}"
    else
        echo -e "${RED}Failed to start container${NC}"
    fi
}

# Function to kill container
kill_container() {
    echo -e "${BLUE}Deleting container...${NC}"
    if container_exists; then
        az container delete \
            --resource-group "$RESOURCE_GROUP" \
            --name "$CONTAINER_NAME" \
            --yes
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Container deleted successfully!${NC}"
        else
            echo -e "${RED}Failed to delete container${NC}"
        fi
    else
        echo -e "${RED}Container '$CONTAINER_NAME' does not exist${NC}"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo -e "${GREEN}=== Parkalot Container Manager ===${NC}"
    echo ""
    echo "What would you like to do:"
    echo "1.) Container Status"
    echo "2.) Container Logs"
    echo "3.) Stream Logs"
    echo "4.) Start Container"
    echo "5.) Kill Container"
    echo "6.) Quit"
    echo ""
    read -p "Enter your choice [1-6]: " choice
}

# Main loop
while true; do
    show_menu
    case $choice in
        1)
            show_status
            ;;
        2)
            show_logs
            ;;
        3)
            stream_logs
            ;;
        4)
            start_container
            ;;
        5)
            kill_container
            ;;
        6)
            echo -e "${BLUE}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please choose 1-6${NC}"
            ;;
    esac
    
    # Wait for user to press enter before showing menu again
    echo ""
    read -p "Press Enter to continue..."
done
