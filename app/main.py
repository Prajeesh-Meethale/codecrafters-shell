import os
import subprocess
import sys
from pathlib import Path

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

def execute_pipeline(commands, stdin=None, stdout_file=None, stdout_mode='w', stderr_file=None, stderr_mode='w'):
    processes = []
    
    for i, (cmd, args) in enumerate(commands):
        stdin_pipe = subprocess.PIPE if i > 0 else (open(stdin, 'r') if stdin else None)
        stdout_pipe = subprocess.PIPE if i < len(commands) - 1 else None
        
        # Handle output redirection for the last command
        if i == len(commands) - 1:
            if stdout_file:
                stdout_pipe = open(stdout_file, stdout_mode)
            if stderr_file:
                stderr_pipe = open(stderr_file, stderr_mode)
            else:
                stderr_pipe = None
        else:
            stderr_pipe = None
        
        try:
            p = subprocess.Popen(
                [cmd] + args,
                stdin=stdin_pipe,
                stdout=stdout_pipe,
                stderr=stderr_pipe
            )
            processes.append(p)
            if i > 0 and processes[i-1].stdout:
                processes[i-1].stdout.close()
        except Exception as e:
            print(f"Error executing {cmd}: {e}")
            return
    
    # Close the input file if we opened it
    if stdin and processes[0].stdin and hasattr(processes[0].stdin, 'close'):
        try:
            processes[0].stdin.close()
        except:
            pass
    
    # Wait for all processes to complete
    for i, p in enumerate(processes):
        try:
            p.wait()
            # Close stdout if it's a file
            if hasattr(p.stdout, 'close'):
                p.stdout.close()
        except:
            pass

def exec(command: str, arguments: list[str]) -> None:
    call(
        f"{} {}".format(
            command,
            " ".join(arguments),
        ),
        shell=True
    )

def main() -> None:
    executables = collect_executables()

    while True:
        try:
            line = input('$ ')
        except EOFError:
            break

        if not line:
            continue

        # Parse the command line
        parts = line.split()
        if not parts:
            continue
        
        command = parts[0]
        arguments = parts[1:]
        
        # Handle pipelines
        if '|' in line:
            pipe_parts = line.split('|')
            commands = []
            for pipe_part in pipe_parts:
                tokens = pipe_part.strip().split()
                if tokens:
                    cmd = tokens[0]
                    args = tokens[1:]
                    
                    # Check if command is an executable
                    if cmd in executables:
                        commands.append((executables[cmd], args))
                    else:
                        commands.append((cmd, args))
            
            execute_pipeline(commands)
            continue
        
        # Handle output redirection
        stdout_file = None
        stdout_mode = 'w'
        stderr_file = None
        stderr_mode = 'w'
        
        # Check for output redirection (1>> or >>)
        if '1>>' in line:
            parts = line.split('1>>')
            line = parts[0].strip()
            stdout_file = parts[1].strip()
            stdout_mode = 'a'
            parts = line.split()
            command = parts[0]
            arguments = parts[1:]
        elif '>>' in line:
            parts = line.split('>>')
            line = parts[0].strip()
            stdout_file = parts[1].strip()
            stdout_mode = 'a'
            parts = line.split()
            command = parts[0]
            arguments = parts[1:]
        elif '1>' in line:
            parts = line.split('1>')
            line = parts[0].strip()
            stdout_file = parts[1].strip()
            parts = line.split()
            command = parts[0]
            arguments = parts[1:]
        elif '>' in line and '2>' not in line:
            parts = line.split('>')
            line = parts[0].strip()
            stdout_file = parts[1].strip()
            parts = line.split()
            command = parts[0]
            arguments = parts[1:]
        
        # Check for stderr redirection
        if '2>>' in line:
            parts = line.split('2>>')
            line = parts[0].strip()
            stderr_file = parts[1].strip()
            stderr_mode = 'a'
            parts = line.split()
            command = parts[0]
            arguments = parts[1:]
        elif '2>' in line:
            parts = line.split('2>')
            line = parts[0].strip()
            stderr_file = parts[1].strip()
            parts = line.split()
            command = parts[0]
            arguments = parts[1:]
        
        if command == 'exit':
            exit(int(arguments[0]) if arguments else 0)
        elif command == 'echo':
            print(' '.join(arguments))
        elif command == 'type':
            target = arguments[0] if arguments else None
            if target in ('exit', 'echo', 'type', 'pwd', 'cd'):
                print(f'{target} is a shell builtin')
            elif target in executables:
                print(f'{target} is {executables.get(target)}')
            else:
                print(f'{target} not found')
        elif command == 'pwd':
            print(os.getcwd())
        elif command == 'cd':
            directory = arguments[0] if arguments else os.path.expanduser('~')
            try:
                os.chdir(os.path.expanduser(directory))
            except OSError:
                print(f'cd: {directory}: No such file or directory')
        elif command in executables:
            try:
                if stdout_file:
                    with open(stdout_file, stdout_mode) as f:
                        subprocess.run(
                            [executables[command]] + arguments,
                            stdout=f,
                            stderr=subprocess.PIPE if not stderr_file else open(stderr_file, stderr_mode),
                            text=True
                        )
                else:
                    result = subprocess.run(
                        [executables[command]] + arguments,
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        print(result.stdout, end='')
                    if result.stderr:
                        print(result.stderr, file=sys.stderr, end='')
            except Exception as e:
                print(f'Error executing {command}: {e}')
        else:
            print(f'{command}: not found')

if __name__ == '__main__':
    main()
