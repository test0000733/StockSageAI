# Deployment Guide for StockSageAI

## Overview

StockSageAI is a Streamlit-based stock forecasting and advisory application. This guide provides instructions for deploying to various platforms.

---

## Deployment Options

### 1. **Streamlit Cloud (Recommended - Easiest)**

#### Prerequisites
- GitHub account with repository
- Streamlit Cloud account (free tier available)

#### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/StockSageAI.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your GitHub repo, branch, and main file: `StockSageAI/app.py`
   - Set environment variables in "Advanced settings"
   - Click "Deploy"

3. **Set Secrets**
   - In Streamlit Cloud dashboard, go to your app settings
   - Add secrets from `StockSageAI/.streamlit/secrets_template.toml`

---

### 2. **Docker Deployment (Local or VPS)**

#### Prerequisites
- Docker installed
- Docker Compose (optional but recommended)

#### Local Testing with Docker

```bash
# Build image
docker build -t stocksageai:latest .

# Run container
docker run -p 8501:8501 stocksageai:latest

# Access app at http://localhost:8501
```

#### Using Docker Compose

```bash
docker-compose up --build
```

#### Deploy to Production VPS

1. **Connect to your VPS** (AWS EC2, DigitalOcean, Linode, etc.)

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

3. **Clone repository**
   ```bash
   git clone YOUR_REPO_URL
   cd StockSageAI
   ```

4. **Build and run**
   ```bash
   docker build -t stocksageai .
   docker run -d -p 80:8501 --restart always stocksageai
   ```

5. **Setup reverse proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

### 3. **Heroku / Railway Deployment**

#### Using Railway (Easier)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to [railwayapp.com](https://railway.app)**
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Choose your StockSageAI repository

3. **Configure environment**
   - Add PORT variable
   - Add any secrets from `secrets_template.toml`
   - Deploy

#### Using Heroku CLI

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create your-app-name

# Deploy
git push heroku main

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
```

---

### 4. **AWS Deployment (ECS/Fargate)**

#### Using AWS Elastic Container Service

1. **Create ECR repository**
   ```bash
   aws ecr create-repository --repository-name stocksageai
   ```

2. **Build and push image**
   ```bash
   docker build -t stocksageai:latest .
   docker tag stocksageai:latest YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/stocksageai:latest
   docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/stocksageai:latest
   ```

3. **Create ECS task and service** (via AWS Console)

---

### 5. **Google Cloud Run**

```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/stocksageai .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/stocksageai

# Deploy to Cloud Run
gcloud run deploy stocksageai \
  --image gcr.io/YOUR_PROJECT_ID/stocksageai \
  --platform managed \
  --region us-central1 \
  --port 8501 \
  --allow-unauthenticated
```

---

## Environment Variables

Create a `.env` file or set these variables in your deployment platform:

```env
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
PYTHONUNBUFFERED=1
DATABASE_URL=sqlite:///stocksageai.db
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
```

---

## Pre-Deployment Checklist

- [ ] All files compile without errors
- [ ] requirements.txt updated with correct versions
- [ ] `.streamlit/secrets.toml` configured (not committed)
- [ ] `.env` file created (not committed)
- [ ] `.gitignore` configured
- [ ] Database initialized and migrated
- [ ] Static files (CSV data) included
- [ ] Tests pass locally
- [ ] Docker image builds successfully

---

## Post-Deployment

1. **Health Check**
   ```bash
   curl https://your-domain.com/_stcore/health
   ```

2. **Monitor Logs**
   ```bash
   # For Docker
   docker logs -f CONTAINER_ID

   # For Railway/Heroku
   heroku logs --tail
   ```

3. **Scale if needed**
   - Heroku: `heroku ps:scale web=2`
   - Docker: Add load balancer (nginx, HAProxy)

---

## Troubleshooting

### Port conflicts
```bash
# Find process on port 8501
lsof -i :8501

# Kill process
kill -9 PID
```

### Docker build fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker build --no-cache -t stocksageai .
```

### Module import errors
```bash
# Check requirements.txt
pip install -r requirements.txt

# Verify imports
python -c "import streamlit; print(streamlit.__version__)"
```

---

## Performance Optimization

1. **Enable caching**
   ```python
   @st.cache_data
   def fetch_data():
       return data_fetcher.get_stock_data()
   ```

2. **Use CDN for static assets**
3. **Enable Gzip compression in Nginx**
4. **Add Redis for session caching**

---

## Security Checklist

- [ ] Never commit `.streamlit/secrets.toml`
- [ ] Use HTTPS/SSL certificates
- [ ] Enable CORS only for trusted domains
- [ ] Rotate secret keys periodically
- [ ] Use strong database passwords
- [ ] Keep dependencies updated
- [ ] Run security scans: `pip-audit`, `bandit`

---

## Support & Documentation

- [Streamlit Documentation](https://docs.streamlit.io)
- [Docker Documentation](https://docs.docker.com)
- [Railway Documentation](https://docs.railway.app)
- [Heroku Documentation](https://devcenter.heroku.com)

