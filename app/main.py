# Shell implementation - Final Fixed Version
import os
import subprocess
import sys
import re

def collect_executables():
    executables = {}
    for directory in os.getenv('PATH', '').split(':'):
        if os.path.isdir(directory):
            try:
                for entry in os.listdir(directory):
                    full_path = os.path.join(directory, entry)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        if entry not in executables:
                            executables[entry] = full_path
            except OSError:
                pass
    return executables

def execute_pipeline(commands):
    """Execute a pipeline of commands."""
    processes = []
    
    for i, (cmd, args) in enumerate(commands):
        # Set up stdin
        if i > 0:
            stdin = processes[i-1].stdout
        else:
            stdin = None
        
        # Set up stdout
        if i < len(commands) - 1:
            stdout = subprocess.PIPE
        else:
            stdout = None
        
        try:
            p = subprocess.Popen(
                [cmd] + args,
                stdin=stdin,
                stdout=stdout,
                stderr=None
            )
            processes.append(p)
        except Exception as e:
            print(f"Error executing {cmd}: {e}", file=sys.stderr)
            return
    
    # Wait for all processes
    for p in processes:
        p.wait()

def parse_redirection(line):
    """Parse command line and extract redirections."""
    stdout_file = None
    stdout_mode = 'w'
    stderr_file = None
    stderr_mode = 'w'
    
    # Check for 2>> (append stderr) - check first
    if '2>>' in line:
        parts = line.split('2>>')
        line = parts[0].strip()
        stderr_file = parts[1].strip()
        stderr_mode = 'a'
    elif '2>' in line:
        parts = line.split('2>')
        line = parts[0].strip()
        stderr_file = parts[1].strip()
        stderr_mode = 'w'
    
    # Check for 1>> (append stdout)
    elif '1>>' in line:
        parts = line.split('1>>')
        line = parts[0].strip()
        stdout_file = parts[1].strip()
        stdout_mode = 'a'
    elif '1>' in line:
        parts = line.split('1>')
        line = parts[0].strip()
        stdout_file = parts[1].strip()
        stdout_mode = 'w'
    elif '>>' in line:
            parts = line.split('>>', 1)
    line = parts[0].strip()
    stdout_file = parts[1].strip()
    stdout_mode = 'a'
    else:
        parts = line.split('>')
        line = parts[0].strip()
        stdout_file = parts[1].strip()
        stdout_mode = 'w'
    
    return line, stdout_file, stdout_mode, stderr_file, stderr_mode

def main() -> None:
    executables = collect_executables()

    while True:
        try:
            line = input('$ ')
        except EOFError:
            break

        if not line.strip():
            continue
        
        # Handle pipelines first
        if '|' in line:
            pipe_parts = line.split('|')
            commands = []
            for pipe_part in pipe_parts:
                tokens = pipe_part.strip().split()
                if tokens:
                    cmd = tokens[0]
                    args = tokens[1:]
                    
                    # Resolve command path
                    if cmd in executables:
                        commands.append((executables[cmd], args))
                    else:
                        commands.append((cmd, args))
            
            execute_pipeline(commands)
            continue
        
        # Parse redirection
        cmd_line, stdout_file, stdout_mode, stderr_file, stderr_mode = parse_redirection(line)
        
        # Parse command and arguments
        parts = cmd_line.split()
        if not parts:
            continue
        
        command = parts[0]
        arguments = parts[1:]
        
        # Handle built-in commands
        if command == 'exit':
            exit_code = int(arguments[0]) if arguments else 0
            sys.exit(exit_code)
        elif command == 'echo':
            output = ' '.join(arguments)
            if stdout_file:
                with open(stdout_file, stdout_mode) as f:
                    f.write(output + '\n')
            else:
                print(output)
        elif command == 'type':
            target = arguments[0] if arguments else None
            if target in ('exit', 'echo', 'type', 'pwd', 'cd'):
                output = f'{target} is a shell builtin'
            elif target in executables:
                output = f'{target} is {executables.get(target)}'
            else:
                output = f'{target} not found'
            
            if stdout_file:
                with open(stdout_file, stdout_mode) as f:
                    f.write(output + '\n')
            else:
                print(output)
        elif command == 'pwd':
            output = os.getcwd()
            if stdout_file:
                with open(stdout_file, stdout_mode) as f:
                    f.write(output + '\n')
            else:
                print(output)
        elif command == 'cd':
            directory = arguments[0] if arguments else os.path.expanduser('~')
            try:
                os.chdir(os.path.expanduser(directory))
            except OSError:
                error_msg = f'cd: {directory}: No such file or directory'
                if stderr_file:
                    with open(stderr_file, stderr_mode) as f:
                        f.write(error_msg + '\n')
                else:
                    print(error_msg, file=sys.stderr)
        elif command in executables:
            # Execute external command
            try:
                stdout_fd = None
                stderr_fd = None
                
                if stdout_file:
                    stdout_fd = open(stdout_file, stdout_mode)
                
                if stderr_file:
                    stderr_fd = open(stderr_file, stderr_mode)
                
                result = subprocess.run(
                    [executables[command]] + arguments,
                    stdout=stdout_fd if stdout_file else None,
                    stderr=stderr_fd if stderr_file else None,
                            capture_output=(not stdout_file and not stderr_file)                )
                
                if stdout_fd:
                    stdout_fd.close()
                if stderr_fd:
                    stderr_fd.close()
                
                if not stdout_file and result.stdout:
                    print(result.stdout.decode('utf-8', errors='replace'), end='')
                if not stderr_file and result.stderr:
                    print(result.stderr.decode('utf-8', errors='replace'), file=sys.stderr, end='')
            except Exception as e:
                error_msg = f'Error executing {command}: {e}'
                if stderr_file:
                    with open(stderr_file, stderr_mode) as f:
                        f.write(error_msg + '\n')
                else:
                    print(error_msg, file=sys.stderr)
        else:
            error_msg = f'{command}: not found'
            if stderr_file:
                with open(stderr_file, stderr_mode) as f:
                    f.write(error_msg + '\n')
            else:
                print(error_msg, file=sys.stderr)

if __name__ == '__main__':
    main()
