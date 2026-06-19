# 🚀 Deployment Guide — Manim Studio

This guide walks you through pushing your code to GitHub and deploying on Railway.

---

## Step 1: Push Code to GitHub

### 1.1 Create a GitHub Repository

1. Go to **https://github.com/new**
2. Repository name: `manim-studio`
3. Description: `Web-based IDE for creating Manim animations`
4. Keep it **Public** (or Private if you prefer)
5. **Do NOT** initialize with README, .gitignore, or license (we already have files)
6. Click **Create repository**

### 1.2 Push Your Code

Copy and run these commands in your terminal. Replace `YOUR_USERNAME` with your GitHub username:

```bash
# Navigate to the project
cd manim_ide

# Initialize git (if not already done)
git init
git add -A
git commit -m "Initial commit: Manim Studio IDE"

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/manim-studio.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**That's it!** Your code is now on GitHub.

---

## Step 2: Deploy on Railway

### 2.1 Create a Railway Account

1. Go to **https://railway.app**
2. Click **Login** → **Login with GitHub**
3. Authorize Railway to access your GitHub account

### 2.2 Create a New Project

1. On the Railway dashboard, click **New Project**
2. Select **Deploy from GitHub Repo**
3. Find and select your `manim-studio` repository
4. Railway will automatically detect the `Dockerfile` and start building

### 2.3 Wait for Build

- Railway will install all system dependencies (FFmpeg, LaTeX, Cairo, Pango)
- This takes **3-5 minutes** on first build
- You'll see build logs in real-time

### 2.4 Get Your Public URL

1. Once deployed, click on your service
2. Go to **Settings** → **Networking**
3. Click **Generate Domain**
4. You'll get a URL like: `manim-studio.up.railway.app`

**Open that URL — your Manim Studio is live! 🎉**

---

## Step 3: (Optional) Add Persistent Storage

Renders are stored in the container and will be lost on redeploy. To persist them:

1. In Railway dashboard, go to your service
2. Click **Volumes** tab
3. Click **New Volume**
4. Mount Path: `/app/renders`
5. Click **Add**

Now your rendered videos will survive redeployments.

---

## Troubleshooting

### Build fails
- Check the build logs in Railway dashboard
- Common issue: Docker image pull timeout → just retry

### App starts but render fails
- The free tier has limited CPU. Rendering may be slow.
- Upgrade to a paid plan ($5/mo) for better performance

### Health check fails
- Railway expects the app to respond on the configured port
- The `railway.json` configures port 5000 automatically

---

## Quick Reference

| What | Where |
|------|-------|
| GitHub repo | `https://github.com/YOUR_USERNAME/manim-studio` |
| Railway dashboard | `https://railway.app/dashboard` |
| Your live app | `https://manim-studio.up.railway.app` |
| Build logs | Railway dashboard → your service → Deployments |
