import os
import importlib.util
import sys

def check_file_imports(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Basic check for syntax errors
        compile(content, file_path, 'exec')
        return None
    except Exception as e:
        return f"Syntax Error: {e}"

def main():
    py_files = []
    for root, dirs, files in os.walk('.'):
        if 'venv' in dirs:
            dirs.remove('venv')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))

    issues = []
    for file in py_files:
        issue = check_file_imports(file)
        if issue:
            issues.append((file, issue))

    print(f"Found {len(py_files)} Python files.")
    print(f"Found {len(issues)} files with syntax errors.")
    for file, issue in issues:
        print(f"{file}: {issue}")

    # Now try to import key modules to find missing dependencies
    modules_to_check = [
        'fastapi', 'uvicorn', 'dotenv', 'requests', 'google.auth',
        'googleapiclient', 'httpx', 'jwt', 'bcrypt', 'passlib',
        'sqlalchemy', 'databases', 'pydantic', 'multipart',
        'jinja2', 'itsdangerous', 'pyhumps', 'ollama', 'bs4'
    ]
    
    print("\nChecking dependencies:")
    for mod in modules_to_check:
        try:
            __import__(mod)
            print(f"  [OK] {mod}")
        except ImportError as e:
            print(f"  [MISSING] {mod}: {e}")

if __name__ == "__main__":
    main()
