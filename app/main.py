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
                        pass
            else:
                full_path = find_executable(command)
                if full_path:
                    # argv[0] will be the executable name, path used only to locate
                    subprocess.run([full_path] + args[1:])
                else:
                    print(f"{command}: command not found")
        except EOFError:
            break

if __name__ == "__main__":
    main()
