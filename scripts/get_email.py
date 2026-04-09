import argparse
from services.gmail import rescue_to_inbox, get_all_account_tokens
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="BackPocket Email Rescue Tool")
    parser.add_argument("msg_id", type=str, help="Gmail Message ID")
    parser.add_argument("--token", type=str, help="Specific token file (e.g. token_ywa.json). Default is token.json.", default="token.json")
    
    args = parser.parse_args()
    
    print(f"⚓ Restoring {args.msg_id} from {args.token}...")
    
    # Try specified token first
    if rescue_to_inbox(args.msg_id, args.token):
        print(f"✅ Successfully restored message {args.msg_id} to INBOX and marked as UNREAD.")
    else:
        # Loop through all accounts if the specified one fails or if it's the default
        print("🔍 Checking other accounts for this message ID...")
        tokens = get_all_account_tokens()
        found = False
        for t in tokens:
            if t == args.token: continue
            if rescue_to_inbox(args.msg_id, t):
                print(f"✅ Successfully restored message {args.msg_id} to INBOX and marked as UNREAD (Account: {t}).")
                found = True
                break
        
        if not found:
            print("❌ Failed to restore message. Check logs.")

if __name__ == "__main__":
    main()
