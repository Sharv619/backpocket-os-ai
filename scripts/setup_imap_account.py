import json
import imaplib
import smtplib

def setup_imap():
    print("[BackPocket Twin: Universal IMAP Setup (Fastmoose/cPanel)]")
    print("----------------------------------------------------------")
    
    username = input("Email Address (e.g. admin@bigbossaccountants.com.au): ").strip()
    if not username:
        print("Username required.")
        return
        
    password = input("Email Password: ").strip()
    
    imap_host = input("IMAP Server Hostname (e.g. imap.bigbossaccountants.com.au): ").strip()
    imap_port = input("IMAP Port (default 993): ").strip() or "993"
    
    smtp_host = input("SMTP Server Hostname (e.g. smtp.bigbossaccountants.com.au): ").strip()
    smtp_port = input("SMTP Port (default 465 for SSL, 587 for TLS): ").strip() or "465"
    
    # Test IMAP Connection
    print(f"\n[*] Testing IMAP connection to {imap_host}:{imap_port}...")
    try:
        mail = imaplib.IMAP4_SSL(imap_host, int(imap_port))
        mail.login(username, password)
        mail.logout()
        print("[SUCCESS] IMAP Connection Verified!")
    except Exception as e:
        print(f"[FAILED] IMAP Connection Error: {e}")
        print("Please check your email, password, and IMAP settings.")
        return
        
    # Test SMTP Connection
    print(f"[*] Testing SMTP connection to {smtp_host}:{smtp_port}...")
    try:
        if str(smtp_port) == "465":
            server = smtplib.SMTP_SSL(smtp_host, int(smtp_port))
        else:
            server = smtplib.SMTP(smtp_host, int(smtp_port))
            server.starttls()
            
        server.login(username, password)
        server.quit()
        print("[SUCCESS] SMTP Connection Verified!")
    except Exception as e:
        print(f"[FAILED] SMTP Connection Error: {e}")
        print("Please check your SMTP settings.")
        return
        
    # Save Config
    safe_name = username.split('@')[0]
    filename = f"token_imap_{safe_name}.json"
    
    config = {
        "username": username,
        "password": password,
        "imap_host": imap_host,
        "imap_port": imap_port,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port
    }
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=4)
        
    print(f"\n[SUCCESS] Saved IMAP configuration to {filename}")
    print("The Twin will automatically detect and patrol this account on the next poll cycle!")

if __name__ == "__main__":
    setup_imap()
