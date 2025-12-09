#!/usr/bin/env python3
import subprocess
import time
import sys
from pathlib import Path

REPO_PATH = Path.cwd()
MAIN_PY = REPO_PATH / "app" / "main.py"

def run_cmd(cmd):
    """Execute git/shell command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def commit_and_push():
    """Push changes to GitHub to trigger tests"""
    print("[*] Committing and pushing...")
    run_cmd("git add app/main.py")
    run_cmd('git commit -m "auto-fix attempt"')
    run_cmd("git push origin main")
    print("[+] Pushed to GitHub")
    time.sleep(10)

def fix_issue_1():
    """Fix stdout redirection (1>> should append to file)"""
    print("[*] Attempting fix for stdout redirection...")
    code = MAIN_PY.read_text()
    
    # The issue is subprocess.run must pass file descriptor directly
    if 'capture_output=not (stdout_file or stderr_file)' in code:
        code = code.replace(
            'capture_output=not (stdout_file or stderr_file)',
            'capture_output=(not stdout_file and not stderr_file)'
        )
        MAIN_PY.write_text(code)
        print("[+] Fix applied")
        return True
    return False

print("="*60)
print("AUTO TEST LOOP - Shell Challenge")
print("="*60)

# Attempt 1: Try the current code
print("\n[ATTEMPT 1] Testing current implementation...")
commit_and_push()
print("[!] Tests are running on CodeCrafters")
print("[*] Check CodeCrafters web interface for results")
print("[*] Next iteration will auto-fix based on errors")

# If we could fetch logs, we'd do:
# time.sleep(20)
# logs = fetch_codecrafters_logs()
# if "Expected prompt" in logs and "Hello Maria" in logs:
#     fix_issue_1()
#     commit_and_push()
#     print("[ATTEMPT 2] Retesting with fix...")
