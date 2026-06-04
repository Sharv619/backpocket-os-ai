import os
from google_auth_oauthlib.flow import InstalledAppFlow
from services.gmail import (
    SCOPES,
    get_gmail_token_storage_path,
    load_gmail_oauth_client_config,
)

def setup_secondary():
    print("[BackPocket Twin: Secondary Account Setup]")
    print("------------------------------------------")
    print("This script will help you add a new business account for the Twin to patrol.")
    
    account_name = input("Enter a nickname for this account (e.g. 'admin' or 'cleaning'): ").strip().lower()
    if not account_name:
        print("Error: Account name cannot be empty.")
        return
    
    token_filename = f"token_{account_name}.json"
    persist_path = get_gmail_token_storage_path(token_filename)
    oauth_config, oauth_source = load_gmail_oauth_client_config()

    if not oauth_config:
        print("[Error] Gmail OAuth client config not found.")
        print("Set GMAIL_OAUTH_JSON, GMAIL_CREDENTIALS_JSON, or GOOGLE_APPLICATION_CREDENTIALS in .env,")
        print("or add gmail_credentials.json to the project root.")
        return

    try:
        print(f"[*] Launching login flow for '{account_name}' using {oauth_source}...")
        flow = InstalledAppFlow.from_client_config(oauth_config, SCOPES)
        creds = flow.run_local_server(port=0)

        persist_dir = os.path.dirname(persist_path)
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
        with open(persist_path, 'w') as token:
            token.write(creds.to_json())

        print(f"[SUCCESS] '{token_filename}' has been created.")
        if persist_path != token_filename:
            print(f"         Stored at fallback path: {persist_path}")
        print("The Twin will now automatically patrol this account every 60 seconds.")
    except Exception as e:
        print(f"[FAILED] to setup account: {e}")

if __name__ == "__main__":
    setup_secondary()
