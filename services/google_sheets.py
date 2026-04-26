import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Builds and returns the Google Sheets API service object."""
    # This path is usually set in GOOGLE_APPLICATION_CREDENTIALS
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
    
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(
            creds_path, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service
    return None

def test_sheets_connection():
    """Tests the connection to the Google Sheet."""
    try:
        service = get_sheets_service()
        if not service:
            return {"status": "error", "message": "Credentials file not found"}
            
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        if not spreadsheet_id or spreadsheet_id == 'your_google_sheet_id_here':
            return {"status": "error", "message": "Invalid SPREADSHEET_ID"}
            
        sheet = service.spreadsheets()
        result = sheet.get(spreadsheetId=spreadsheet_id).execute()
        return {"status": "success", "sheet_title": result.get('properties', {}).get('title')}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ensure_sheets_exist():
    """Checks for required sheets and creates them with headers if missing."""
    try:
        service = get_sheets_service()
        if not service:
            return
            
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_sheets = [s.get('properties', {}).get('title') for s in spreadsheet.get('sheets', [])]
        
        # Standard Schemas (Aligned with Steve's Diagram)
        # ---- Steve's System Map (v2.2) ----
        REQUIRED_SHEETS = {
            "Clients_Master": ["First Name", "Last Name", "Primary Email", "Client Status", "Estimator/Site Manager", "Mobile", "Birthdate", "Background Info", "Date Registered"],
            "Leads_Capture": ["First Name", "Last Name", "Primary Email", "Status", "Subject", "Snippet", "Actionable Items", "Date", "Decision"],
            "Action_Log": ["Name", "From Email", "To Email", "Subject", "Body Snippet", "Actionable Items", "Date Lodged", "Status", "Tier"],
            "Portal_Updates": ["Name", "Email", "Subject", "Activity Summary", "Tier", "Status", "Date"],
            "Govt_Assoc_Log": ["Date Logged", "Sender", "Subject", "Body Snippet"],
            "Supplier_Expenses": ["Vendor", "Amount", "Due Date", "Subject", "Date Logged", "Status", "Email Body"],
            "Spam_Archive": ["Name", "Email", "To (Brand)", "Subject", "Body Snippet", "Date Logged"],
            "Existing_Emails": ["Date Logged", "Sender", "Subject", "Body Snippet"],
            "Priority_List": ["Email/Domain", "Tier (1 or 2)", "Notes"]
        }
        
        for sheet_name, headers in REQUIRED_SHEETS.items():
            if sheet_name not in existing_sheets:
                logger.info(f"Creating sheet: {sheet_name}")
                body = {'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
                service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
            
            # Always ensure headers are correct (even if sheet existed)
            try:
                header_body = {'values': [headers]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1",
                    valueInputOption="USER_ENTERED", body=header_body
                ).execute()
            except Exception as e:
                logger.warning(f"Could not update headers for {sheet_name}: {e}")
                
    except Exception as e:
        logger.error(f"Error in ensure_sheets_exist: {e}")

def log_activity(data, sheet_name="Action_Log"):
    """Logs a system action with standardized columns."""
    try:
        service = get_sheets_service()
        if not service: return
        
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        email_addr = data.get('email_address', '')
        subject = data.get('subject', '')
        
        if email_addr and subject and sheet_name == "Action_Log":
            try:
                existing = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, 
                    range=f"{sheet_name}!A:Z"
                ).execute()
                rows = existing.get('values', [])
                for i, row in enumerate(rows):
                    if row and len(row) > 3 and row[1].lower() == email_addr.lower() and row[3] == subject:
                        logger.info(f"DUPLICATE SKIP: {email_addr} - {subject[:30]} already logged")
                        return
            except Exception as check_err:
                logger.warning(f"Could not check duplicates: {check_err}")
        
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. LOG TO SPECIFIC TIER SHEET (If applicable)
        tier_sheet_map = {
            "Tier 1": "Existing_Emails",
            "Tier 2": "Govt_Assoc_Log",
            "Tier 3": "Govt_Assoc_Log", # As requested, Tier 3 consolidated here
            "Tier 4": "Portal_Updates" 
        }
        
        target_tier = data.get('tier_verbose', data.get('tier', 'Unknown'))
        if str(target_tier).replace('Tier ', '') in ['1', '2', '3', '4']:
            key = f"Tier {str(target_tier).replace('Tier ', '')}"
            if key in tier_sheet_map:
                tier_sheet = tier_sheet_map[key]
                tier_values = [[now, data.get('email_address', ''), data.get('subject', ''), data.get('body', '')[:1000]]]
                service.spreadsheets().values().append(
                    spreadsheetId=os.getenv("SPREADSHEET_ID"),
                    range=f"{tier_sheet}!A:D",
                    valueInputOption="USER_ENTERED", body={'values': tier_values}
                ).execute()
        
        # 2. CHERRY'S SPECIFIC SCHEMAS (A to I mappings)
        if sheet_name == "Action_Log":
            # [Name, From Email, To Address, Subject, Body Snippet, Actionable Items, Date Logged, Status, Tier]
            values = [[
                data.get('from_name', ''),
                data.get('email_address', ''),
                data.get('to_email', ''),
                data.get('subject', ''),
                data.get('body', '')[:500],
                data.get('actionable_items', ''),
                now,
                data.get('status', 'Processed'),
                target_tier
            ]]
            range_name = "A:I"
        elif sheet_name == "Leads_Capture":
            # [First Name, Last Name, Primary Email, Client Status, Subject, Body Snippet, Actionable Items, Date Lodged, Decision]
            name_parts = data.get('from_name', '').split(' ')
            values = [[
                name_parts[0] if name_parts else '',
                " ".join(name_parts[1:]) if len(name_parts) > 1 else '',
                data.get('email_address', ''),
                'New Lead/Prospect',
                data.get('subject', ''),
                data.get('body', '')[:500],
                data.get('actionable_items', ''),
                now,
                'Pending Review'
            ]]
            range_name = "A:I"
        elif sheet_name == "Portal_Updates":
             values = [[
                data.get('from_name', ''),
                data.get('email_address', ''),
                data.get('subject', ''),
                data.get('body', '')[:1000],
                data.get('tier', 'Tier 4'),
                data.get('status', 'Logged'),
                now
            ]]
             range_name = "A:G"
        else: # Spam_Archive, etc.
             values = [[
                data.get('from_name', ''),
                data.get('email_address', ''),
                data.get('to_email', ''),
                data.get('subject', ''),
                data.get('body', '')[:500],
                now
            ]]
             range_name = "A:F"
        
        service.spreadsheets().values().append(
            spreadsheetId=os.getenv("SPREADSHEET_ID"),
            range=f"{sheet_name}!{range_name}",
            valueInputOption="USER_ENTERED",
            body={'values': values}
        ).execute()
    except Exception as e:
        logger.error(f"Error logging to {sheet_name}: {e}")

def check_client_identity(email):
    """Checks if the given email exists in the Clients_Master sheet and returns full context."""
    try:
        service = get_sheets_service()
        if not service: return None
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range='Clients_Master!C2:C').execute()
        
        values = result.get('values', [])
        if not values: return None
            
        for i, row in enumerate(values):
            if row and row[0].lower() == email.lower():
                # New Mapping: A: First, B: Last, C: Email, D: Status, E: Acct/Aud, F: Mobile, G: Bday, H: BG Info, I: Date
                full_row_range = f'Clients_Master!A{i+2}:I{i+2}'
                full_row_result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=full_row_range).execute()
                full_row = full_row_result.get('values', [])[0]
                
                return {
                    "first_name": full_row[0] if len(full_row) > 0 else '',
                    "last_name": full_row[1] if len(full_row) > 1 else '',
                    "email": full_row[2] if len(full_row) > 2 else '',
                    "status": full_row[3] if len(full_row) > 3 else '',
                    "estimator_site_manager": full_row[4] if len(full_row) > 4 else '',
                    "mobile": full_row[5] if len(full_row) > 5 else '',
                    "birthdate": full_row[6] if len(full_row) > 6 else '',
                    "background_info": full_row[7] if len(full_row) > 7 else 'No background info.',
                    "date_added": full_row[8] if len(full_row) > 8 else ''
                }
        return None
    except Exception as e:
        logger.error(f"Error checking client identity: {e}")
        return None

def get_client_emails() -> list:
    """Returns a flat list of all email addresses in the Clients_Master sheet (column C).
    Used by the whitelist cache in Layer 0 pre-triage to guarantee no client is ever spam."""
    try:
        service = get_sheets_service()
        if not service:
            return []
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range='Clients_Master!C2:C').execute()
        values = result.get('values', [])
        return [row[0].strip() for row in values if row and row[0].strip()]
    except Exception as e:
        logger.error(f"Error fetching client emails for whitelist: {e}")
        return []

def add_new_client_to_master(data):
    """Auto-Onboarding Action: Adds to BPS_Client_Master + Leads_Capture + Action_Log."""
    try:
        service = get_sheets_service()
        if not service: return
        
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract all fields from data
        name_parts = data.get('from_name', 'New Client').split(' ')
        first = name_parts[0]
        last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Get all available fields (with defaults)
        email = data.get('email_address', '')
        mobile = data.get('mobile', '')
        client_status = data.get('client_status', 'Active')
        estimator_or_site_manager = data.get('estimator_or_site_manager', '')
        birthdate = data.get('birthdate', '')
        background = data.get('background_info', '')
        
        # 1. 📂 CLIENTS MASTER (The House)
        # [First, Last, Email, Status, Site Manager, Mobile, Bday, BG, Date]
        values_master = [[first, last, email, client_status, estimator_or_site_manager, mobile, birthdate, background, now]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range="Clients_Master!A:I",
            valueInputOption="USER_ENTERED", body={'values': values_master}
        ).execute()

        # 2. 📋 ACTION LOG (The History)
        log_activity(data, sheet_name="Action_Log")

        # 3. 🎯 LEADS CAPTURE (The Source)
        log_activity(data, sheet_name="Leads_Capture")
        
        logger.info(f"✨ AUTO-ONBOARDED: {first} {last} added and logged.")
    except Exception as e:
        logger.error(f"Error triple-plotting client onboarding: {e}")

def add_new_lead(data):
    return log_activity(data, sheet_name="Leads_Capture")

def log_expense(data):
    return log_activity(data, sheet_name="Supplier_Expenses")

def log_portal_update(data):
    return log_activity(data, sheet_name="Portal_Updates")

def process_lead_conversions():
    """Scans Leads_Capture for rows marked 'Onboarded' and moves them to Clients_Master."""
    try:
        service = get_sheets_service()
        if not service: return
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'Leads_Capture!A2:I'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        rows = result.get('values', [])
        if not rows: return

        for i, row in enumerate(rows):
            if len(row) >= 9 and row[8].strip().lower() == 'onboarded':
                new_client_data = {'from_name': f"{row[0]} {row[1]}", 'email_address': row[2]}
                add_new_client_to_master(new_client_data)
                
                # Mark as converted
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id, range=f'Leads_Capture!I{i+2}',
                    valueInputOption="USER_ENTERED", body={'values': [['Converted']]}
                ).execute()
    except Exception as e:
        logger.error(f"Error converting leads: {e}")

def get_todays_portal_updates():
    try:
        service = get_sheets_service()
        if not service: return 0
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="Portal_Updates!E2:E").execute()
        dates = result.get('values', [])
        return sum(1 for d in dates if d and d[0].startswith(today_str))
    except Exception as e:
        logger.error(f"Error getting portal updates: {e}")
        return 0
def get_priority_list():
    """Fetches the dynamic Tier 1/2 list from the Priority_List tab."""
    service = get_sheets_service()
    sid = os.getenv('SPREADSHEET_ID')
    if not service: return {}
    
    try:
        res = service.spreadsheets().values().get(spreadsheetId=sid, range='Priority_List!A2:B').execute()
        rows = res.get('values', [])
        priority_map = {}
        for row in rows:
            if len(row) >= 2:
                priority_map[row[0].lower().strip()] = int(row[1])
        return priority_map
    except Exception as e:
        if "Unable to parse range" in str(e):
            logger.warning("Priority_List tab not found. Using empty priority map.")
        else:
            logger.error(f"Error fetching priority list: {e}")
        return {}

def sync_instructions_to_sheets(instructions):
    """Sync sender instructions to Google Sheets (Twin_Instructions tab)."""
    try:
        service = get_sheets_service()
        if not service: 
            logger.error("Sheets service not available for sync")
            return
        
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        if not spreadsheet_id:
            logger.error("SPREADSHEET_ID not set")
            return
        
        logger.info(f"Syncing {len(instructions)} instructions to {spreadsheet_id}")
        
        # Build new values
        new_values = []
        for inst in instructions:
            new_values.append([
                inst.get('sender_email', ''),
                inst.get('category', ''),
                inst.get('instructions', ''),
                inst.get('created_at', ''),
                inst.get('updated_at', now),
                '',  # Notes - for Steve to add context
                'Active',  # Status - Active/Inactive
                'Twin'  # Last_Updated_By - Twin/Steve
            ])
        
        if not new_values:
            logger.info("No instructions to sync")
            return
        
        # Try to create sheet first using batchUpdate
        try:
            # Check if sheet exists by trying to get data
            service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Twin_Instructions!A1').execute()
            sheet_exists = True
        except:
            sheet_exists = False
            # Create the sheet
            try:
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {'title': 'Twin_Instructions'}
                        }
                    }]
                }
                service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
                logger.info("Created Twin_Instructions sheet")
            except Exception as create_err:
                logger.error(f"Could not create sheet: {create_err}")
        
        # Now write data
        try:
            # Clear existing data
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range='Twin_Instructions!A:E'
            ).execute()
            
            # Write headers and data
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Twin_Instructions!A1',
                valueInputOption="USER_ENTERED",
                body={'values': [['Sender Email', 'Category', 'Instructions', 'Created', 'Updated', 'Notes', 'Status', 'Last_Updated_By']] + new_values}
            ).execute()
            logger.info(f"Synced {len(instructions)} instructions to Twin_Instructions")
        except Exception as write_err:
            logger.error(f"Failed to write to Twin_Instructions: {write_err}")
            
    except Exception as e:
        logger.error(f"Error syncing instructions to Sheets: {e}")
