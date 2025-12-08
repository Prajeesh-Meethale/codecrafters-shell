import sys
import os
import subprocess
import shlex

def find_executable(command):
    for path in os.environ.get('PATH', '').split(os.pathsep):
        full_path = os.path.join(path, command)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            line = input()
            if not line.strip():
                continue
            
            # Handle redirection
            redirect_file = None
            if '>' in line:
                parts = line.split('>', 1)
                if len(parts) == 2:
                    line = parts[0].strip()
                    redirect_file = parts[1].strip()
                    # Remove quotes if present
                    if redirect_file.startswith('"') and redirect_file.endswith('"'):
                        redirect_file = redirect_file[1:-1]
                    elif redirect_file.startswith("'") and redirect_file.endswith("'"):
                        redirect_file = redirect_file[1:-1]
            
            args = shlex.split(line)
            if not args:
                continue
            command = args[0]

            if command == "exit":
                sys.exit(0)
            elif command == "echo":
                output = " ".join(args[1:])
                if redirect_file:
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    with open(redirect_file, 'w') as f:
                        f.write(output + '\n')
                else:
                    print(output)
            elif command == "type":
                if len(args) < 2:
                    continue
                target = args[1]
                # Check if it's a builtin first
                builtins = ["echo", "exit", "type", "pwd", "cd"]
                if target in builtins:
                    output = f"{target} is a shell builtin"
                else:
                    full_path = find_executable(target)
                    if full_path:
                        output = full_path
                    else:
                        output = f"{target}: not found"
                
                if redirect_file:
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    with open(redirect_file, 'w') as f:
                        f.write(output + '\n')
                else:
                    print(output)
            elif command == "pwd":
                output = os.getcwd()
                if redirect_file:
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    with open(redirect_file, 'w') as f:
                        f.write(output + '\n')
                else:
                    print(output)
            elif command == "cd":
                if len(args) > 1:
                    path = os.path.expanduser(args[1])
                    try:
                        os.chdir(path)
                    except OSError:
                        print(f"cd: {args[1]}: No such file or directory")
                else:
                    # cd without arguments goes to home directory
                    home = os.path.expanduser("~")
                    try:
                        os.chdir(home)
                    except OSError:
                        pass
            else:
                full_path = find_executable(command)
                if full_path:
                    # Use full_path to locate executable, but pass command name as argv[0]
                    if redirect_file:
                        dir_path = os.path.dirname(redirect_file)
                        if dir_path:
                            os.makedirs(dir_path, exist_ok=True)
                        with open(redirect_file, 'w') as f:
                            subprocess.run([command] + args[1:], executable=full_path, stdout=f)
                    else:
                        subprocess.run([command] + args[1:], executable=full_path)
                else:
                    print(f"{command}: command not found")
        except EOFError:
            break

if __name__ == "__main__":
    main()
