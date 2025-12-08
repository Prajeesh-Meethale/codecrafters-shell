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
            redirect_stderr = False  # True for 2> or 2>>, False for 1>, 1>>, >, or >>
            redirect_append = False  # True for >>, 1>>, or 2>>, False for >, 1>, or 2>
            # Find redirection operator from right to left, checking if it's outside quotes
            redirect_pos = -1
            redirect_op = None
            
            # Helper function to check if position is outside quotes
            def is_outside_quotes(pos):
                before = line[:pos]
                in_single = False
                in_double = False
                j = 0
                while j < len(before):
                    if before[j] == '\\' and j + 1 < len(before):
                        j += 2
                        continue
                    if before[j] == "'" and not in_double:
                        in_single = not in_single
                    elif before[j] == '"' and not in_single:
                        in_double = not in_double
                    j += 1
                return not in_single and not in_double
            
            # Check for append operators first (2>>, 1>>, >>)
            # Check for 2>> (append stderr)
            for i in range(len(line) - 2, -1, -1):
                if line[i:i+3] == '2>>' and is_outside_quotes(i):
                    redirect_pos = i
                    redirect_op = '2>>'
                    redirect_stderr = True
                    redirect_append = True
                    break
            
            # Check for 1>> (append stdout with explicit fd)
            if redirect_pos == -1:
                for i in range(len(line) - 2, -1, -1):
                    if line[i:i+3] == '1>>' and is_outside_quotes(i):
                        redirect_pos = i
                        redirect_op = '1>>'
                        redirect_stderr = False
                        redirect_append = True
                        break
            
            # Check for >> (append stdout)
            if redirect_pos == -1:
                for i in range(len(line) - 1, -1, -1):
                    if line[i:i+2] == '>>' and is_outside_quotes(i):
                        redirect_pos = i
                        redirect_op = '>>'
                        redirect_stderr = False
                        redirect_append = True
                        break
            
            # Check for redirect operators (2>, 1>, >)
            # Check for 2> (stderr redirection)
            if redirect_pos == -1:
                for i in range(len(line) - 1, -1, -1):
                    if line[i:i+2] == '2>' and is_outside_quotes(i):
                        redirect_pos = i
                        redirect_op = '2>'
                        redirect_stderr = True
                        redirect_append = False
                        break
            
            # Check for 1> (stdout redirection with explicit fd)
            if redirect_pos == -1:
                for i in range(len(line) - 1, -1, -1):
                    if line[i:i+2] == '1>' and is_outside_quotes(i):
                        redirect_pos = i
                        redirect_op = '1>'
                        redirect_stderr = False
                        redirect_append = False
                        break
            
            # Check for > (stdout redirection)
            if redirect_pos == -1:
                for i in range(len(line) - 1, -1, -1):
                    if line[i] == '>' and is_outside_quotes(i):
                        # Make sure it's not part of >>
                        if i + 1 < len(line) and line[i+1] == '>':
                            continue
                        redirect_pos = i
                        redirect_op = '>'
                        redirect_stderr = False
                        redirect_append = False
                        break
            
            if redirect_pos != -1:
                line_part = line[:redirect_pos].strip()
                redirect_file = line[redirect_pos + len(redirect_op):].strip()
                line = line_part
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
                # Only redirect if it's stdout redirection (not stderr)
                if redirect_file and not redirect_stderr:
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    mode = 'a' if redirect_append else 'w'
                    with open(redirect_file, mode) as f:
                        f.write(output + '\n')
                elif redirect_file and redirect_stderr:
                    # Create the file for stderr redirection, but output goes to stdout
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    if not redirect_append:
                        open(redirect_file, 'w').close()  # Create empty file
                    print(output)
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
                
                # Only redirect if it's stdout redirection (not stderr)
                if redirect_file and not redirect_stderr:
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    mode = 'a' if redirect_append else 'w'
                    with open(redirect_file, mode) as f:
                        f.write(output + '\n')
                elif redirect_file and redirect_stderr:
                    # Create the file for stderr redirection, but output goes to stdout
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    if not redirect_append:
                        open(redirect_file, 'w').close()  # Create empty file
                    print(output)
                else:
                    print(output)
            elif command == "pwd":
                output = os.getcwd()
                # Only redirect if it's stdout redirection (not stderr)
                if redirect_file and not redirect_stderr:
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    mode = 'a' if redirect_append else 'w'
                    with open(redirect_file, mode) as f:
                        f.write(output + '\n')
                elif redirect_file and redirect_stderr:
                    # Create the file for stderr redirection, but output goes to stdout
                    dir_path = os.path.dirname(redirect_file)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    if not redirect_append:
                        open(redirect_file, 'w').close()  # Create empty file
                    print(output)
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
                        mode = 'a' if redirect_append else 'w'
                        with open(redirect_file, mode) as f:
                            if redirect_stderr:
                                subprocess.run([command] + args[1:], executable=full_path, stderr=f)
                            else:
                                subprocess.run([command] + args[1:], executable=full_path, stdout=f)
                    else:
                        subprocess.run([command] + args[1:], executable=full_path)
                else:
                    print(f"{command}: command not found")
        except EOFError:
            break

if __name__ == "__main__":
    main()
