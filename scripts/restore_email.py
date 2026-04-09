import argparse
from services.gmail import search_emails, mark_unread_and_inbox, get_all_account_tokens

def main():
    parser = argparse.ArgumentParser(description="BackPocket Email Rescue Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # FIND command
    find_parser = subparsers.add_parser("find", help="Search for emails across all accounts")
    find_parser.add_argument("query", type=str, help="Search query (name, email, or keywords)")

    # GET command
    get_parser = subparsers.add_parser("get", help="Restore an email to Inbox and mark Unread")
    get_parser.add_argument("msg_id", type=str, help="Gmail Message ID")
    get_parser.add_argument("token", type=str, help="Token file (e.g. token_ywa.json)", default="token.json", nargs="?")

    args = parser.parse_args()

    if args.command == "find":
        tokens = get_all_account_tokens()
        print(f"🔍 Searching for '{args.query}' across {len(tokens)} accounts...")
        for t in tokens:
            matches = search_emails(args.query, t)
            if matches:
                print(f"\n--- Results from {t} ---")
                for m in matches:
                    print(f"ID: {m['id']}")
                    print(f"FROM: {m['sender']}")
                    print(f"SUBJECT: {m['subject']}")
                    print(f"SNIPPET: {m['snippet'][:100]}...")
                    print("-" * 20)

    elif args.command == "get":
        print(f"⚓ Restoring {args.msg_id} from {args.token}...")
        if mark_unread_and_inbox(args.msg_id, args.token):
            print("✅ Successfully restored to Inbox and marked as UNREAD.")
        else:
            print("❌ Failed to restore middle. Check logs.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
