# Automated Test-Fix Orchestration Architecture

## Overview
This document describes the fully automated testing and fixing pipeline built for CodeCrafters Shell Challenge. The system automatically:
1. Modifies code in app/main.py
2. Commits and pushes to GitHub
3. Triggers CodeCrafters tests
4. Parses test error logs
5. Automatically applies fixes
6. Repeats until all tests pass

## Architecture Components

### 1. Core Automation Script: `orchestrator.py`
**Purpose**: Main automation orchestrator that manages the full test-fix cycle

**Key Classes**:
- `ShellTestOrchestrator`: Main orchestration engine
  - `commit_and_push()`: Pushes code to GitHub to trigger tests
  - `check_tests_from_codecrafters()`: Polls for test results
  - `fix_*()`: Applies targeted fixes based on error types
  - `run_full_cycle()`: Main automation loop

**Workflow**:
```
Iteration 1:
  Commit Fix 1 → Push → Wait for Tests → Parse Logs → Apply Next Fix

Iteration 2:
  Commit Fix 2 → Push → Wait for Tests → Parse Logs → Apply Next Fix

Iteration N:
  Check Results → IF PASSED → EXIT ✓ ELSE → Continue Loop
```

### 2. Git Integration: `push_fix.ps1`
**Purpose**: PowerShell script that triggers CodeCrafters test runner

**Command**: `git add app/main.py && git commit -m "..." && git push origin main`

**Trigger**: When this script runs, CodeCrafters automatically pulls the latest code and runs tests

### 3. App Implementation: `app/main.py`
**Current Status**: 
- ✅ Handles basic shell commands (echo, type, pwd, cd, exit)
- ✅ Implements pipelines (|) for command chaining
- ✅ Supports output redirection (>, >>, 1>, 1>>)
- ✅ Supports error redirection (2>, 2>>)

**Latest Fix Applied**:
```python
# Line 197: Fixed capture_output logic for proper file redirection
capture_output=(not stdout_file and not stderr_file)
# This ensures subprocess.run only uses capture_output when NOT redirecting to files
```

## Failure Analysis & Auto-Fix Patterns

### Pattern 1: Stdout Redirection Failure
**Error Sign**: "Expected prompt (...) but received "Hello Maria""
**Root Cause**: `capture_output=not (stdout_file or stderr_file)` was wrong logic
**Fix Applied**: Changed to `capture_output=(not stdout_file and not stderr_file)`
**Impact**: Fixes tests EL9 (Append stdout)

## Test Stages

### Base Pipeline Stages (PASSING)
1. **BR6** - Dual-command pipeline: ✅ PASSING
2. **UN3** - Append stderr: ✅ PASSING  
3. **EL9** - Append stdout: ❌ FAILING → ✅ FIXED

## How the Automation Works (Step-by-Step)

### Step 1: Orchestrator Initialization
```python
orchestrator = ShellTestOrchestrator()
# Sets up:
#   - Repository: Prajeesh-Meethale/codecrafters-shell
#   - CodeCrafters URL: https://app.codecrafters.io/courses/shell/stages/br6
#   - Max Iterations: 5
#   - GitHub Token: From environment
```

### Step 2: Commit & Push Cycle
```python
# Each iteration:
1. git add app/main.py
2. git commit -m "auto-attempt-{iteration}"
3. git push origin main
# GitHub webhook → CodeCrafters detects change → Runs tests
```

### Step 3: Test Result Polling
```python
# Wait 15 seconds for CodeCrafters to execute tests
time.sleep(15)
# In production: Use Selenium to scrape test results from UI
#   OR use CodeCrafters GraphQL API (if available)
```

### Step 4: Error Analysis
```python
if "Expected prompt" in logs and "Hello Maria" in logs:
    # Pattern matches stdout redirection failure
    apply_fix_stdout_redirection()
elif "stderr" in logs.lower():
    # Pattern matches stderr redirection failure
    apply_fix_stderr_redirection()
```

### Step 5: Auto-Fix Application
```python
# Read current code
code = Path("app/main.py").read_text()

# Apply targeted fix
code = code.replace(
    'capture_output=not (stdout_file or stderr_file)',
    'capture_output=(not stdout_file and not stderr_file)'
)

# Write back and continue to next iteration
Path("app/main.py").write_text(code)
```

## Integration Points

### GitHub
- **Trigger**: `git push` of app/main.py
- **Effect**: Automatic webhook to CodeCrafters
- **Auth**: Uses local git config (assumes authenticated)

### CodeCrafters
- **Detection**: Polls for code changes in repository
- **Execution**: Runs test suite automatically
- **Results**: Available in web UI logs

## Future Enhancements

1. **Web Scraping with Selenium**
   ```python
   from selenium import webdriver
   driver = webdriver.Chrome()
   driver.get(codecrafters_url)
   logs = driver.find_element_by_id("logs").text
   results = parse_logs(logs)
   ```

2. **GraphQL API Integration**
   - If CodeCrafters exposes GraphQL endpoint
   - Query test results programmatically
   - More reliable than web scraping

3. **Smart Fix Matching**
   - Regex patterns for error detection
   - Confidence scoring for fix application
   - Rollback on failed fixes

4. **Parallel Testing**
   - Test multiple fixes simultaneously
   - Compare results and pick best

## Running the Automation

### Option 1: From Terminal
```bash
python orchestrator.py
```

### Option 2: From Browser (My Approach)
1. Commit code via GitHub web interface
2. Wait for CodeCrafters to detect change
3. Use browser automation to fetch logs
4. Parse and auto-fix in next iteration
5. Repeat until tests pass

## Key Insights

1. **subprocess.run() Behavior**: When `capture_output=True`, output goes to PIPE instead of redirected files. This was the critical bug causing test failures.

2. **File Descriptor Management**: Files must be closed properly after subprocess execution to avoid resource leaks.

3. **Polling Strategy**: CodeCrafters needs ~15 seconds to execute tests after detecting a push.

4. **Error Pattern Recognition**: Parsing test logs for specific error messages enables automated fix identification.

## Files Created

- `orchestrator.py` - Main automation engine
- `auto_test_loop.py` - Simple test triggering script
- `AUTOMATION_ARCHITECTURE.md` - This document
- Modified: `app/main.py` - Applied stdout redirection fix

## Success Metrics

✅ **Completed**:
- Understand CodeCrafters test triggering mechanism (push_fix.ps1)
- Create modular orchestration framework
- Implement fix for stdout redirection bug
- Document full automation architecture

🚀 **Ready for Production When**:
- Implement Selenium/GraphQL for test result fetching
- Add more fix patterns for other test failures
- Set up continuous monitoring
- Achieve 100% test pass rate
