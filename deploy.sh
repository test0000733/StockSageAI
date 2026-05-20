#!/bin/bash
# StockSageAI Quick Deployment Script
# Usage: ./deploy.sh [platform] [app-name]
# Platforms: docker, heroku, railway, gcloud

set -e

PLATFORM=${1:-docker}
APP_NAME=${2:-stocksageai}

echo "==================================="
echo "StockSageAI Deployment Script"
echo "==================================="
echo "Platform: $PLATFORM"
echo "App Name: $APP_NAME"
echo ""

case $PLATFORM in

  docker)
    echo "Building Docker image..."
    docker build -t $APP_NAME:latest .
    
    echo "Starting Docker container..."
    docker run -d -p 8501:8501 \
      --name $APP_NAME \
      --restart unless-stopped \
      $APP_NAME:latest
    
    echo "✓ Docker deployment complete!"
    echo "Access your app at: http://localhost:8501"
    ;;

  heroku)
    echo "Logging into Heroku..."
    # heroku login  # Uncomment to prompt for login
    
    echo "Creating Heroku app..."
    heroku create $APP_NAME || echo "App may already exist"
    
    echo "Deploying to Heroku..."
    git push heroku main || git push heroku master
    
    echo "✓ Heroku deployment complete!"
    echo "Access your app at: https://$APP_NAME.herokuapp.com"
    ;;

  railway)
    echo "Deploying to Railway..."
    echo "Note: Railway deployment works with GitHub integration"
    echo ""
    echo "1. Commit your changes:"
    echo "   git add ."
    echo "   git commit -m 'Ready for deployment'"
    echo ""
    echo "2. Push to GitHub:"
    echo "   git push origin main"
    echo ""
    echo "3. Go to https://railway.app"
    echo "4. Create new project from GitHub"
    echo "5. Select this repository"
    echo "6. Railway will auto-deploy!"
    ;;

  gcloud)
    echo "Deploying to Google Cloud Run..."
    
    PROJECT_ID=$(gcloud config get-value project)
    REGION=${3:-us-central1}
    
    echo "Building image..."
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$APP_NAME
    
    echo "Deploying to Cloud Run..."
    gcloud run deploy $APP_NAME \
      --image gcr.io/$PROJECT_ID/$APP_NAME:latest \
      --platform managed \
      --region $REGION \
      --port 8501 \
      --allow-unauthenticated
    
    echo "✓ Google Cloud Run deployment complete!"
    ;;

  local)
    echo "Running locally with Streamlit..."
    streamlit run StockSageAI/app.py
    ;;

  *)
    echo "Unknown platform: $PLATFORM"
    echo ""
    echo "Supported platforms:"
    echo "  - docker        : Deploy using Docker"
    echo "  - heroku        : Deploy to Heroku"
    echo "  - railway       : Deploy to Railway"
    echo "  - gcloud        : Deploy to Google Cloud Run"
    echo "  - local         : Run locally"
    echo ""
    echo "Usage: $0 [platform] [app-name]"
    exit 1
    ;;

esac

echo ""
echo "==================================="
echo "Deployment Guide:"
echo "See DEPLOYMENT.md for detailed instructions"
echo "See DEPLOYMENT_ALTERNATIVES.md for platform comparison"
echo "==================================="
