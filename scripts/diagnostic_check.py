#!/usr/bin/env python3
"""
diagnostic_check.py — BackPocket OS Pipeline Diagnostic

Checks:
  1. Dependencies installed
  2. Database integrity
  3. Configuration files
  4. Key API endpoints (requires running server)
  5. Sample data integrity

Usage:
    python3 scripts/diagnostic_check.py
    python3 scripts/diagnostic_check.py --full  # Includes API tests
"""

import sys
import os
import sqlite3
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_ok(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_fail(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warn(text):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def check_dependencies():
    print_header("1. Dependency Check")

    required = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'google.auth',
        'google.oauth2',
        'google.generativeai',  # or google.genai
        'requests',
        'PIL',
        'dotenv',
    ]

    all_ok = True
    for module_name in required:
        try:
            __import__(module_name.split('.')[0])
            print_ok(f"{module_name}")
        except ImportError:
            print_fail(f"{module_name} — NOT INSTALLED")
            all_ok = False

    return all_ok

def check_database():
    print_header("2. Database Check")

    db_path = "backpocket.db"
    if not os.path.exists(db_path):
        print_fail(f"Database not found: {db_path}")
        return False

    print_ok(f"Database exists: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check critical tables
        critical_tables = [
            'pending_approvals',
            'instructions',
            'sender_instructions',
            'documents',
            'workflow_stages',
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {row[0] for row in cursor.fetchall()}

        for table in critical_tables:
            if table in existing:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print_ok(f"Table '{table}' exists ({count} rows)")
            else:
                print_fail(f"Table '{table}' MISSING")

        # Check pending approvals sample data
        cursor.execute("SELECT COUNT(*) FROM pending_approvals")
        pending_count = cursor.fetchone()[0]
        if pending_count > 0:
            print_ok(f"Sample data: {pending_count} pending approvals")
        else:
            print_warn(f"No pending approvals found (run demo_seed.py to populate)")

        conn.close()
        return True
    except Exception as e:
        print_fail(f"Database error: {e}")
        return False

def check_config():
    print_header("3. Configuration Check")

    # Check .env exists
    env_file = ".env"
    config_ok = True

    if os.path.exists(env_file):
        print_ok(f"{env_file} exists")

        # Parse and check key variables
        env_vars = {}
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, val = line.strip().split('=', 1)
                        env_vars[key] = val
        except Exception as e:
            print_warn(f"Could not parse .env: {e}")

        # Check important keys
        important_keys = [
            'GEMINI_API_KEY',
            'GOOGLE_APPLICATION_CREDENTIALS',
            'OLLAMA_BASE_URL',
        ]

        for key in important_keys:
            if key in env_vars:
                val = env_vars[key]
                if val and val != 'your_key_here':
                    print_ok(f"{key} is set")
                else:
                    print_warn(f"{key} is placeholder (will need real value for Gmail/Gemini)")
            else:
                print_warn(f"{key} not found in .env")
    else:
        print_warn(f".env not found — copy from .env.example and fill in API keys")
        config_ok = False

    # Check credentials (optional)
    if os.path.exists("gmail_credentials.json"):
        print_ok("gmail_credentials.json exists")
    else:
        print_warn("gmail_credentials.json not found — Gmail OAuth will prompt on first use (optional)")

    return config_ok

def check_main_import():
    print_header("4. Application Import Check")

    try:
        import main
        print_ok("main.py imports successfully")

        # Check for key functions
        if hasattr(main, 'app'):
            print_ok("FastAPI app object found")
        else:
            print_fail("FastAPI app object not found")

        return True
    except Exception as e:
        print_fail(f"main.py import failed: {e}")
        return False

def check_api_endpoints():
    print_header("5. API Endpoint Check (Requires Running Server)")

    print_warn("This check requires the server to be running on http://127.0.0.1:8000")
    print("Run in another terminal: python3 -m uvicorn main:app --host 127.0.0.1 --port 8000")

    try:
        import requests

        # Health check
        try:
            resp = requests.get("http://127.0.0.1:8000/health", timeout=2)
            if resp.status_code == 200:
                print_ok("GET /health → 200 OK")
            else:
                print_warn(f"GET /health → {resp.status_code}")
        except requests.ConnectionError:
            print_fail("Server not responding on http://127.0.0.1:8000 — is it running?")
            return False

        # Pending approvals endpoint
        try:
            resp = requests.get("http://127.0.0.1:8000/api/pending", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print_ok(f"GET /api/pending → 200 OK ({len(data)} approvals)")
                else:
                    print_warn(f"GET /api/pending returned unexpected format")
            else:
                print_warn(f"GET /api/pending → {resp.status_code}")
        except Exception as e:
            print_fail(f"GET /api/pending error: {e}")

        return True
    except ImportError:
        print_warn("requests library not found — skipping API tests")
        return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='BackPocket OS Diagnostic Check')
    parser.add_argument('--full', action='store_true', help='Include API endpoint tests')
    args = parser.parse_args()

    print(f"{Colors.BLUE}")
    print("╔" + "─"*58 + "╗")
    print("║" + "  BackPocket OS - Pipeline Diagnostic".center(58) + "║")
    print("╚" + "─"*58 + "╝")
    print(f"{Colors.END}")

    results = []

    # Run checks
    results.append(("Dependencies", check_dependencies()))
    results.append(("Database", check_database()))
    results.append(("Configuration", check_config()))
    results.append(("Main Import", check_main_import()))

    if args.full:
        results.append(("API Endpoints", check_api_endpoints()))

    # Summary
    print_header("Summary")

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if ok else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {name:.<40} {status}")

    print()
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print_ok("All checks passed! Ready to test pipelines.")
        print("\nNext steps:")
        print("  1. Start server: python3 -m uvicorn main:app --host 127.0.0.1 --port 8000")
        print("  2. Open dashboard: http://127.0.0.1:8000/static/index.html")
        print("  3. Review TEST_PIPELINES.md for detailed testing guide")
    else:
        print_warn(f"{total - passed} check(s) failed — see above for details")

    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
