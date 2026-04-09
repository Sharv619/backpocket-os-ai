import argparse
from services.gmail import search_emails, get_all_account_tokens
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="BackPocket Email Search Tool")
    parser.add_argument("query", type=str, help="Search query (e.g. 'from:example.com' or keywords)")
    parser.add_argument("--account", type=str, help="Specific token file to search. Default is all accounts.")
    
    args = parser.parse_args()
    
    if args.account:
        tokens = [args.account]
    else:
        tokens = get_all_account_tokens()
    
    print(f"🔍 Searching for '{args.query}' across {len(tokens)} accounts...")
    
    found_any = False
    for t in tokens:
        try:
            matches = search_emails(args.query, t)
            if matches:
                found_any = True
                print(f"\n--- 📧 Results from {t} ---")
                for m in matches:
                    print(f"ID: {m['id']}")
                    print(f"FROM: {m['sender']}")
                    print(f"SUBJECT: {m['subject']}")
                    print(f"SNIPPET: {m['snippet'][:100]}...")
                    print("-" * 30)
        except Exception as e:
            print(f"⚠️ Error searching {t}: {e}")
            
    if not found_any:
        print("\n❌ No emails found matches your query.")

if __name__ == "__main__":
    main()
