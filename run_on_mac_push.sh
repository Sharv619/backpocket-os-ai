#!/bin/bash
echo "[SYNC] Adding all changes..."
git add .
echo "[SYNC] Committing changes..."
git commit -m "Auto-sync: $(date)"
echo "[SYNC] Pushing to GitHub..."
git push
echo "[DONE] You are ready to switch stations!"
