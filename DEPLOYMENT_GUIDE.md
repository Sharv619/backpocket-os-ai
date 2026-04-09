# BackPocket OS - Mini-PC Deployment Guide

## Overview
This guide explains how to set up BackPocket OS on a mini-PC for 24/7 operation.

## Option 1: Cloud Sync (Recommended for Easy Updates)

### Setup on Desktop (Development Machine)
1. Install OneDrive, Dropbox, or Google Drive on your desktop
2. Create a folder called `BackPocket` in your cloud sync folder
3. Copy the entire `BackPocket_MVP` folder into it

### Setup on Mini-PC
1. Install the same cloud sync client
2. Sign in with the same account
3. The `BackPocket` folder will automatically sync
4. Run `SETUP_AUTOSTART.bat` to enable auto-start

### Updates
Simply make changes in the desktop version - they'll automatically sync to the mini-PC. Restart the server to apply changes.

---

## Option 2: Git Deployment

### Initial Setup
1. On desktop: Initialize git if not already
   ```bash
   cd BackPocket_MVP
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. On mini-PC:
   ```bash
   git clone <your-repo-url> BackPocket_MVP
   ```

### Updates
On mini-PC:
```bash
cd BackPocket_MVP
git pull
```

---

## Setting Up Auto-Start (24/7)

### Step 1: Copy Folder to Mini-PC
Copy the `BackPocket_MVP` folder to a fixed location, e.g.:
```
C:\BackPocket_MVP
```

### Step 2: Run Auto-Start Setup
1. Open Command Prompt as Administrator
2. Navigate to the folder:
   ```bash
   cd C:\BackPocket_MVP
   ```
3. Run:
   ```bash
   SETUP_AUTOSTART.bat
   ```

### Step 3: Verify
- Restart the mini-PC
- The server should start automatically
- Access dashboard at: `http://localhost:8000/dashboard`

---

## Costs

| Component | Cost |
|-----------|------|
| Server Hosting | FREE (local) |
| Gemini AI | ~$0.01-0.05/email |
| WhatsApp (Whapi) | ~$0.005/message |
| Gmail API | FREE |
| Google Sheets API | FREE |
| Ollama (local AI) | FREE |

### To Reduce Costs
- Use Ollama instead of Gemini for AI (already configured as fallback)
- Check `.env` to enable Ollama as primary

---

## Troubleshooting

### Server Not Starting
1. Check if Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check logs in console output

### API Errors
1. Verify `.env` file exists and has correct credentials
2. Run `RUN_DIAGNOSTICS.bat` to check connections

### Dashboard Not Loading
1. Ensure server is running (check console)
2. Try: `http://127.0.0.1:8000/dashboard`

---

## Manual Commands

| Action | Command |
|--------|---------|
| Start Server | `LAUNCH_BACKPOCKET_TWIN.bat` |
| Restart Server | `RESTART_SERVER.bat` |
| Run Diagnostics | `RUN_DIAGNOSTICS.bat` |
| View Logs | `VIEW_LOGS.bat` |

---

## Port Forwarding (For External Access)

If you want to access the dashboard from your phone or outside the network:

1. Go to router settings
2. Port forward 8000 to the mini-PC's local IP
3. Access via: `http://<your-public-ip>:8000/dashboard`

**Note:** For security, consider setting up a password or VPN.
