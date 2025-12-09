#!/usr/bin/env python3
"""Full Automation Orchestrator for CodeCrafters Testing
Uses: GitHub API for code changes + Selenium for test result scraping
"""
import subprocess
import time
import base64
import json
import os
from pathlib import Path

class ShellTestOrchestrator:
    def __init__(self):
        self.repo = "Prajeesh-Meethale/codecrafters-shell"
        self.codecrafters_url = "https://app.codecrafters.io/courses/shell/stages/br6"
        self.iteration = 0
        self.max_iterations = 5
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        
    def log(self, msg, level="[*]"):
        print(f"{level} {msg}")
        
    def commit_and_push(self, message):
        """Commit app/main.py and push to GitHub"""
        self.log(f"Committing: {message}", "[COMMIT]")
        subprocess.run("git add app/main.py", shell=True, capture_output=True)
        subprocess.run(f'git commit -m "{message}"', shell=True, capture_output=True)
        result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            self.log("Push successful", "[+]")
            return True
        else:
            self.log(f"Push failed: {result.stderr}", "[-]")
            return False
    
    def get_current_code(self):
        """Read current app/main.py content"""
        return Path("app/main.py").read_text()
    
    def write_fixed_code(self, code):
        """Write fixed code to app/main.py"""
        Path("app/main.py").write_text(code)
        self.log("Updated app/main.py", "[+]")
        
    def fix_stdout_redirection_v1(self):
        """Fix 1: Proper file descriptor handling"""
        self.log("Attempting Fix #1: stdout redirection", "[FIX]")
        code = self.get_current_code()
        
        # Replace the capture_output logic
        if 'capture_output=not (stdout_file or stderr_file)' in code:
            code = code.replace(
                'capture_output=not (stdout_file or stderr_file)',
                'capture_output=(not stdout_file and not stderr_file)'
            )
            self.write_fixed_code(code)
            return True
        return False
        
    def fix_file_descriptor_management(self):
        """Fix 2: Better file descriptor closing"""
        self.log("Attempting Fix #2: file descriptor management", "[FIX]")
        code = self.get_current_code()
        
        # Ensure files are closed properly
        if 'if stdout_fd:\n                    stdout_fd.close()' in code:
            self.log("File descriptor management already proper", "[OK]")
            return False
        return False
    
    def check_tests_from_codecrafters(self):
        """NOTE: Requires Selenium WebDriver in production
        For now, we'll return placeholder status
        """
        self.log("Waiting for CodeCrafters test execution...", "[WAIT]")
        time.sleep(15)  # Wait for CodeCrafters to run tests
        
        # In production, you'd use Selenium here:
        # driver = webdriver.Chrome()
        # driver.get(self.codecrafters_url)
        # test_status = driver.find_element(...).text
        # logs = driver.find_element(...).text
        
        return {"status": "pending", "logs": "", "passed": False}
    
    def run_full_cycle(self):
        """Main automation loop"""
        self.log("=" * 70, "[START]")
        self.log("Full Automation Orchestrator for CodeCrafters", "[START]")
        self.log("=" * 70, "[START]")
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            self.log(f"\nIteration {self.iteration}/{self.max_iterations}", "[CYCLE]")
            self.log("-" * 70, "[CYCLE]")
            
            # Step 1: Commit and push current code
            if not self.commit_and_push(f"auto-attempt-{self.iteration}"):
                self.log("Failed to push, stopping", "[-]")
                return False
            
            # Step 2: Wait and check test results
            test_result = self.check_tests_from_codecrafters()
            
            # Step 3: Check if tests passed
            if test_result.get("passed"):
                self.log("\n" + "="*70, "[SUCCESS]")
                self.log("ALL TESTS PASSED!", "[SUCCESS]")
                self.log("="*70, "[SUCCESS]")
                return True
            
            # Step 4: Apply fixes
            if self.iteration == 1:
                if self.fix_stdout_redirection_v1():
                    self.log("Fix applied, will test in next iteration", "[+]")
            elif self.iteration == 2:
                if self.fix_file_descriptor_management():
                    self.log("Fix applied, will test in next iteration", "[+]")
            else:
                self.log("No more fixes to attempt", "[!]")
                break
        
        self.log("\nMax iterations reached", "[-]")
        return False

if __name__ == "__main__":
    orchestrator = ShellTestOrchestrator()
    success = orchestrator.run_full_cycle()
    exit(0 if success else 1)
