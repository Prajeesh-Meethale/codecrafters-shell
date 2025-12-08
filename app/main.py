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
            args = shlex.split(line)
            command = args[0]

            if command == "exit":
                sys.exit(0)
            elif command == "echo":
                print(" ".join(args[1:]))
            elif command == "type":
                if len(args) < 2:
                    continue
                target = args[1]
                # Check if it's a builtin first
                builtins = ["echo", "exit", "type", "pwd", "cd"]
                if target in builtins:
                    print(f"{target} is a shell builtin")
                else:
                    full_path = find_executable(target)
                    if full_path:
                        print(full_path)
                    else:
                        print(f"{target}: not found")
            elif command == "pwd":
                print(os.getcwd())
            elif command == "cd":
                if len(args) > 1:
                    try:
                        os.chdir(args[1])
                    except OSError:
                        print(f"cd: {args[1]}: No such file or directory")
            else:
                full_path = find_executable(command)
                if full_path:
                    # Use full_path to locate executable, but pass command name as argv[0]
                    subprocess.run([command] + args[1:], executable=full_path)
                else:
                    print(f"{command}: command not found")
        except EOFError:
            break

if __name__ == "__main__":
    main()
