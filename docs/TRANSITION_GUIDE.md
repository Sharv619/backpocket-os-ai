# Work Transition Guide: Desktop ↔ MacAir

To make it feel like "we just took a break" when you switch computers, you need to sync **three things**: your Code, your Secrets, and your AI Context.

## 1. Syncing Code (Git)
We use GitHub to move your scripts and markdown files.

### Leaving the Station (Push)
Before you leave your current computer, run:
- **Windows**: Double-click `RUN_ON_PC_PUSH.bat`
- **Mac**: Run `./run_on_mac_push.sh`

### Arriving at the Station (Pull)
When you sit down at the other computer, run:
- **Windows**: Double-click `RUN_ON_PC_PULL.bat`
- **Mac**: Run `./run_on_mac_pull.sh`

---

## 2. Syncing "Secrets" (Manual)
Git **ignores** these files for security. If you change a setting in `.env` or update your database, you must move these manually via AirDrop or USB:
*   `.env`
*   `backpocket.db`
*   `credentials.json` / `token.json`

---

## 3. Syncing AI Context (Antigravity)
Since Antigravity conversations are local to each device, you need to "refresh" its memory when you switch:

1.  Open the new station.
2.  Open the file `MaterialDNA/MATERIALDNA_HACKATHON_PLAN.md`.
3.  **Prompt Antigravity**:
    > "I just switched stations. Read `MaterialDNA/MATERIALDNA_HACKATHON_PLAN.md` to refresh your context on our current plan and research. What were we about to do next?"

---

## ⚠️ Important Mac Notes
*   **ngrok.exe**: This will not run on Mac. You must install the Mac version of ngrok or use the Mac-specific tunnel commands.
*   **Python Path**: Use `python3` on Mac instead of `python`.
*   **Execution Bits**: The first time you use the scripts on Mac, you must run: `chmod +x sync_push.sh sync_pull.sh`.
