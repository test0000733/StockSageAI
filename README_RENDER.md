# Deploying to Render (private repo)

This guide shows two simple ways to deploy the Streamlit app to Render from a private GitHub repo.

Option A — Connect repo directly to Render (recommended, simplest)
1. Go to https://dashboard.render.com and sign in.
2. Click "New+" → "Web Service".
3. Choose "Connect a repository" and grant Render access to your private repo (GitHub authorization).
4. Pick the `main` branch and set the environment to `Docker`.
5. Set the Dockerfile path to `./Dockerfile` (the repo already includes a Dockerfile).
6. Set the start command (if Render asks):

   streamlit run StockSageAI/app.py --server.port $PORT --server.headless true

7. Add any environment variables or secrets (API keys) in Render's dashboard — do NOT commit secrets to the repo.
8. Create the service and deploy. Render will build and run your container.

Option B — Build & publish a Docker image from CI, deploy image to Render
Use this if you prefer CI-built images or want to avoid granting Render repo access.

1. Create a Personal Access Token with `write:packages` and `read:packages` (GitHub) and add it as a repository secret named `GHCR_PAT`.
2. A GitHub Actions workflow is included at `.github/workflows/build-and-publish.yml`. It builds the Docker image and pushes it to `ghcr.io/${{ github.repository }}:latest` on pushes to `main`.
3. In Render create a new Web Service and pick the "Docker Image" option. Use the image URL `ghcr.io/<owner>/<repo>:latest`.
4. Add secrets and set the start command as above. Deploy.

Notes and tips
- Render sets the `PORT` env var automatically; Streamlit needs to listen on that port.
- Use Render's environment variables feature for API keys (no secrets in code).
- If your app uses GPU/large memory, choose appropriate Render plan and instance size.
- If you want the app private behind authentication, configure Render's access controls or put it behind a simple auth proxy.

If you want, I can: connect a ready GitHub Actions workflow to push images, or generate a small `render-ignore` list, or prepare an example `render.cron` or additional env var templates. Tell me which next step you'd like me to perform.
