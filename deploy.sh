#!/bin/bash

# Variables
PROJECT_ID="vertione"
REGION="us-central1"
REPO="artifact-registry-vertione"
IMAGE_NAME="api"
SERVICE_NAME="vertione-backend"

# Construir y subir imagen
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_NAME

# Desplegar en Cloud Run usando Secret Manager para DATABASE_URL
gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000 \
  --set-secrets DATABASE_URL=database-url-vertione:latest \
  --set-env-vars SECRET_KEY="your-secret-key-change-in-prod",ALGORITHM="HS256",ACCESS_TOKEN_EXPIRE_MINUTES="30",ENVIRONMENT="production"
