import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The scope for Gmail modification
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def setup_secondary():
    print("[BackPocket Twin: Secondary Account Setup]")
    print("------------------------------------------")
    print("This script will help you add a new business account for the Twin to patrol.")
    
    account_name = input("Enter a nickname for this account (e.g. 'admin' or 'cleaning'): ").strip().lower()
    if not account_name:
        print("Error: Account name cannot be empty.")
        return
    
    token_filename = f"token_{account_name}.json"
    
    if not os.path.exists('gmail_credentials.json'):
        print("[Error] 'gmail_credentials.json' not found in the root directory.")
        print("Please ensure you have your Google OAuth credentials file ready.")
        return

    try:
        print(f"[*] Launching login flow for '{account_name}'...")
        flow = InstalledAppFlow.from_client_secrets_file('gmail_credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(token_filename, 'w') as token:
            token.write(creds.to_json())
            
        print(f"[SUCCESS] '{token_filename}' has been created.")
        print("The Twin will now automatically patrol this account every 60 seconds.")
    except Exception as e:
        print(f"[FAILED] to setup account: {e}")

if __name__ == "__main__":
    setup_secondary()
