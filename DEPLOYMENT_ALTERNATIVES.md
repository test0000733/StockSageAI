# StockSageAI - Deployment Alternatives

## Why Vercel/Netlify Don't Work Directly

Vercel and Netlify are optimized for static sites and JavaScript-based applications. StockSageAI is a Python/Streamlit app that requires:
- Python runtime (3.11.7)
- Long-running processes
- WebSocket connections
- Dynamic content generation

**Solution**: Use Docker containers or Python-specific deployment platforms.

---

## Recommended Deployment Platforms (in order)

### 1. **Streamlit Cloud** ⭐ BEST FOR THIS PROJECT
- **Pros**: Free, native Streamlit support, one-click deploy from GitHub
- **Cons**: Limited customization, Streamlit-only limitations
- **Cost**: Free tier available
- **Setup Time**: 5 minutes

**Deploy Now**:
```bash
git push origin main
# Then visit share.streamlit.io and connect GitHub repo
```

---

### 2. **Railway.app** ⭐ BEST FOR DOCKER
- **Pros**: Docker native, simple GitHub integration, reasonable pricing
- **Cons**: Small community compared to Heroku
- **Cost**: Pay-as-you-go, ~$5/mo for starter
- **Setup Time**: 10 minutes

**Deploy**:
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Add environment variables
5. Railway auto-deploys on git push

---

### 3. **Heroku** (with paid dyno)
- **Pros**: Industry standard, good documentation, easy deployment
- **Cons**: Paid only now, Procfile-based
- **Cost**: $7+/mo (eco dyno)
- **Setup Time**: 15 minutes

**Deploy**:
```bash
heroku create your-app
git push heroku main
heroku config:set SECRET_KEY="your-key"
```

---

### 4. **AWS Elastic Container Service (ECS)**
- **Pros**: Scalable, production-ready, AWS ecosystem
- **Cons**: Complex, steep learning curve
- **Cost**: ~$15-100+/mo
- **Setup Time**: 1-2 hours

**Deploy with CloudFormation or console**

---

### 5. **Google Cloud Run**
- **Pros**: Serverless, pay-per-use, excellent scaling
- **Cons**: Requires container image
- **Cost**: $0.0000024/vCPU-second (~$5-10/mo)
- **Setup Time**: 20 minutes

**Deploy**:
```bash
gcloud run deploy stocksageai --source .
```

---

### 6. **DigitalOcean App Platform**
- **Pros**: Simple, integrated Docker support, good pricing
- **Cons**: Less feature-rich than AWS/GCP
- **Cost**: $12+/mo
- **Setup Time**: 15 minutes

**Deploy**:
1. Connect GitHub repo
2. Select Dockerfile
3. Configure environment
4. Deploy

---

### 7. **Self-Hosted (VPS)**
- **Pros**: Full control, lowest cost, no vendor lock-in
- **Cons**: You manage everything, requires DevOps knowledge
- **Cost**: $5-20/mo (DigitalOcean, Linode, Vultr)
- **Setup Time**: 1-3 hours

**Providers**: DigitalOcean, Linode, Vultr, AWS EC2, Azure

---

## Quick Comparison Table

| Platform | Cost | Setup | Native Support | Docker | Auto-Deploy |
|----------|------|-------|-----------------|--------|-------------|
| Streamlit Cloud | Free | 5min | ✓ Excellent | ✗ No | ✓ Yes |
| Railway | $5+ | 10min | ✓ Good | ✓ Yes | ✓ Yes |
| Heroku | $7+ | 15min | ✓ Good | ✓ Yes | ✓ Yes |
| Google Cloud Run | Pay/use | 20min | ✓ Good | ✓ Yes | ✓ Yes |
| AWS ECS | $15+ | 2hrs | ✓ Excellent | ✓ Yes | ~ Manual |
| DigitalOcean | $12+ | 15min | ~ Fair | ✓ Yes | ✓ Yes |
| Self-Hosted VPS | $5+ | 2+hrs | ✓ Any | ✓ Yes | ~ Manual |

---

## STEP-BY-STEP: Deploy to Railway (Recommended)

### 1. Ensure Git repo is ready
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/StockSageAI.git
git push -u origin main
```

### 2. Go to [railway.app](https://railway.app)

### 3. Sign in with GitHub
- Click "Start a New Project"
- Select "Deploy from GitHub"

### 4. Select Repository
- Choose `StockSageAI` repo
- Authorize Railway to access it

### 5. Configure Project
- Railway auto-detects Dockerfile
- Click "Deploy Now"

### 6. Add Environment Variables
- Click your project
- Go to "Variables"
- Add from `StockSageAI/.streamlit/secrets_template.toml`:
  ```
  DATABASE_URL=sqlite:///stocksageai.db
  SECRET_KEY=your-randomly-generated-secret
  ```

### 7. Domain
- Railway auto-generates a domain: `your-app.up.railway.app`
- Optionally add custom domain in settings

### Done! 🎉
Your app is live and auto-deploys on every `git push`.

---

## STEP-BY-STEP: Deploy to Streamlit Cloud (Fastest)

### 1. Push to GitHub
```bash
git push origin main
```

### 2. Visit [share.streamlit.io](https://share.streamlit.io)

### 3. Click "Create App"
- Select your GitHub repo
- Select branch: `main`
- Select file: `StockSageAI/app.py`

### 4. Deploy
- Click "Deploy"
- Streamlit handles the rest

### 5. Add Secrets
- In Streamlit dashboard, go to your app
- Click "Settings" → "Secrets"
- Copy contents from `secrets_template.toml`

### Done! 🎉
Your app is live at: `https://[username]-stocksageai.streamlit.app`

---

## Health Check

After deployment, verify with:
```bash
curl https://your-deployed-app.com/_stcore/health
```

Expected response: `200 OK`

---

## Monitoring & Logs

### Railway
```bash
railway logs
```

### Streamlit Cloud
- Dashboard shows logs in real-time

### Self-Hosted
```bash
docker logs -f container_id
tail -f /var/log/stocksageai/app.log
```

---

## Scale Your App

### Horizontal Scaling (Multiple Instances)
- **Railway**: "Add Services" button
- **Heroku**: `heroku ps:scale web=3`
- **AWS ECS**: Increase task count

### Database Optimization
- Switch from SQLite to PostgreSQL
- Add Redis caching layer
- Implement database connection pooling

### CDN for Static Assets
- Use Cloudflare for global distribution
- Compress static files
- Cache aggressively

---

## Troubleshooting

### Port binding error
```bash
# Check if port 8501 is in use
lsof -i :8501

# Or set custom port in env
export STREAMLIT_SERVER_PORT=8502
```

### Module not found
```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Verify all imports
python -c "import streamlit; import yfinance; print('OK')"
```

### Slow startup
- Reduce cache usage
- Lazy-load heavy modules
- Use `@st.cache_data` for expensive operations

### Memory issues
- Monitor with `docker stats`
- Limit data processing
- Use streaming for large datasets

---

## Security Checklist for Production

- [ ] Change all default secrets
- [ ] Enable HTTPS/SSL
- [ ] Set `showErrorDetails = false` in config
- [ ] Use environment variables for sensitive data
- [ ] Enable authentication
- [ ] Rate limit API endpoints
- [ ] Regular security updates: `pip-audit`
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity
- [ ] Use strong passwords for database

---

## Cost Optimization

| Platform | Monthly Cost | Optimization |
|----------|------------|--------------|
| Streamlit Cloud | Free | Best for side projects |
| Railway | $5-10 | Share VM with other services |
| Heroku | $50+ (eco dyno) | ⚠️ Expensive, consider alternatives |
| Google Cloud Run | $5-15 | Good for variable load |
| DigitalOcean | $24/yr (special) | Best value for compute |
| Self-hosted | $5-15 | Cheapest but needs maintenance |

---

## Next Steps

1. **Choose platform** based on requirements above
2. **Follow deployment guide** for your chosen platform
3. **Configure secrets** from `secrets_template.toml`
4. **Test thoroughly** on staging before production
5. **Monitor performance** and logs
6. **Scale as needed** based on usage

---

## Support

- **Streamlit Cloud Issues**: Check Streamlit Community Forum
- **Railway Issues**: Railway Docs & Twitter support
- **Docker Issues**: Docker Docs, Stack Overflow
- **General**: GitHub Issues, Stack Overflow

---

**Your app is now ready for production deployment!** 🚀
