# Transitioning BackPocket System.io Setup to Mac Air

This guide contains the instructions for picking up where you left off on your Windows machine, so you can continue building the MVP on your Mac Air.

---

## Part 1: How to Transfer the Project

Since we are using standard Python tools, the code runs exactly the same on a Mac as it does on Windows. 

**Steps:**
1. Copy this entire `BackPocket_MVP` folder from your Windows computer (e.g., via USB drive, Google Drive, Dropbox, or a `.zip` file over email).
2. Download/move the folder onto your Mac Air (e.g., to your Desktop or Documents folder).
3. Open your code editor (Cursor/VS Code) on your Mac, and open this `BackPocket_MVP` folder.

---

## Part 2: Re-installing the Required Tools on Mac

Macs handle Python slightly differently. Once you open the project on your Mac, you need to re-install the background packages.

**Steps:**
1. Open the Terminal inside your code editor on the Mac.
2. Run this exact command:
   ```bash
   pip install -r requirements.txt
   ```
   *(If your Mac gives an error, try running `pip3 install -r requirements.txt` instead).*
3. To test if the server starts, run:
   ```bash
   uvicorn main:app --port 8000
   ```

---

## Part 3: Setting Up Google Cloud Credentials (If not already done)

If you haven't finished setting up the `credentials.json` file on Windows, you will need to do it on the Mac. Here is the idiot-proof, step-by-step guide to generating your Service Account Key:

### A. Create the Project and Enable APIs
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and log in with your Google account.
2. Click the **Select a project** dropdown in the top left.
3. Click the **NEW PROJECT** button in the top right.
4. Name your project `BackPocket MVP` and click **CREATE**.
5. Make sure the new `BackPocket MVP` project is selected in the top dropdown.
6. In the top search bar, type exactly **Google Sheets API**. Click it, and click the blue **ENABLE** button.
7. Go back to the top search bar, type exactly **Gmail API**, click it, and click **ENABLE**.

### B. Create the Service Account
1. On the left-hand menu, hover over **IAM & Admin**, then click on **Service Accounts**.
2. Click the **+ CREATE SERVICE ACCOUNT** button at the top.
3. **Service account name**: Type `backpocket-bot`.
4. Copy the long auto-generated email address under "Service account ID" (e.g. `backpocket-bot@...gserviceaccount.com`). **Save this—you will share your Google Sheet with this email!**
5. Click **CREATE AND CONTINUE**.
6. **Role**: Select **Editor** (under the "Basic" category).
7. Click **CONTINUE**, then **DONE**.

### C. Download `credentials.json`
1. On the "Service Accounts" page, click the **Three Dots (⋮)** next to `backpocket-bot` and select **Manage keys**.
2. Click **ADD KEY** -> **Create new key**.
3. Select **JSON** and click **CREATE**.
4. The file will download to your Mac (usually in the Downloads folder).

### D. Put It In the Project Folder
1. Find the downloaded file.
2. Move it into this `BackPocket_MVP` project folder.
3. Rename the file to exactly **`credentials.json`**.

### E. Share Your Google Sheet
1. Open up your Google Sheet containing the Client List.
2. Click the green **Share** button in the top right.
3. Paste the Service Account email address you copied in Step B-4.
4. Set them as an **Editor**, uncheck "Notify people", and click **Share**.

---

## Part 4: Filling out the `.env` File
Make sure your `.env` file transferred over. If it's empty or missing on the Mac (Macs sometimes hide files that start with a dot):
1. Rename `.env.example` to `.env`.
2. Open `.env` and fill in:
   - `SPREADSHEET_ID=` (The long string of letters/numbers in your Google Sheet URL)
   - `GEMINI_API_KEY=` (Your Gemini API key)
   - `WHAPI_TOKEN=` (Your WhatsApp API token)

## Next Steps:
Once you have done all this on your Mac and tested the server (`http://127.0.0.1:8000/test-sheets`), you are ready to tell the AI to start **Task 2: Inbox Monitoring & Identity Matching**!

---

## Part 5: the Daily Sync Routine
Since you are bouncing between your Windows Desktop and Mac Air, you need to use GitHub to pass the code back and forth natively.

### 1. When you are DONE working for the day
Before you close your laptop or leave the desktop, you must **Push** your work to the "cloud bucket" (GitHub).
Run these exact three commands in the terminal (press enter after each one):
```bash
git add .
git commit -m "End of day progress"
git push
```

### 2. When you START working on the other computer
When you get to the office (or open the laptop at WSTI), you must **Pull** the newest changes down from the "cloud bucket" before you start writing any new code.
Run this one command in the terminal:
```bash
git pull
```

**That's it! If you always Push when you leave, and Pull when you start, your codebase will stay perfectly in sync across both of your computers!**
