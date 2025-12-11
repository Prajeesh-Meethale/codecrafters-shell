import sys
import os
import subprocess
import shlex
import readline
import glob


def find_executable(command):
    for path in os.environ.get('PATH', '').split(os.pathsep):
        full_path = os.path.join(path, command)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None


def get_all_executables():
    """Get all executable files from PATH - using glob like their example."""
    matches = []
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    
    for dir_path in path_dirs:
        if not dir_path:
            continue
        try:
            for file_path in glob.glob(os.path.join(dir_path, "*")):
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    cmd_name = os.path.basename(file_path)
                    if cmd_name not in matches:
                        matches.append(cmd_name)
        except Exception:
            pass
    
    return matches


def parse_redirection(cmd_line):
    """Parse redirection from command line."""
    redirect_file = None
    redirect_stderr = False
    redirect_append = False
    
    def is_outside_quotes(pos, text):
        before = text[:pos]
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
    
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '2>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+3:].strip(), True, True
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '2>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), True, False
    
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '1>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+3:].strip(), False, True
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '1>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), False, False
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), False, True
    
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i] == '>' and is_outside_quotes(i, cmd_line):
            if i + 1 < len(cmd_line) and cmd_line[i+1] == '>':
                continue
            return cmd_line[:i].strip(), cmd_line[i+1:].strip(), False, False
    
    return cmd_line, None, False, False


def execute_command(command, args, redirect_file=None, redirect_stderr=False, redirect_append=False, stdin_data=None, should_print=True):
    """Execute a single command."""
    
    if command == "exit":
        sys.exit(0 if not args or len(args) < 2 else int(args[1]))
    
    elif command == "echo":
        output = " ".join(args[1:]) + '\n'
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass
        
        sys.stdout.write(output)
        sys.stdout.flush()
        return b""
    
    elif command == "type":
        if len(args) < 2:
            return b""
        target = args[1]
        if target in ["exit", "echo", "type", "pwd", "cd", "history"]:
            output = f"{target} is a shell builtin\n"
        else:
            full_path = find_executable(target)
            if full_path:
                output = f"{full_path}\n"
            else:
                output = f"{target}: not found\n"
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass
        
        sys.stdout.write(output)
        sys.stdout.flush()
        return b""
    
    elif command == "pwd":
        output = os.getcwd() + '\n'
        
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass
        
        sys.stdout.write(output)
        sys.stdout.flush()
        return b""
    
    elif command == "cd":
        if len(args) > 1:
            path = os.path.expanduser(args[1])
            try:
                os.chdir(path)
            except OSError:
                print(f"cd: {args[1]}: No such file or directory")
        else:
            home = os.path.expanduser("~")
            os.chdir(home)
        return b""
    
    elif command == "history":
        # Placeholder for history command
        # Will be implemented in later stages
        return b""
    
    else:
        full_path = find_executable(command)
        if not full_path:
            print(f"{command}: command not found")
            return b""
        
        cmd_str = ' '.join([command] + args[1:])
        
        if redirect_file:
            if redirect_stderr:
                op = '2>>' if redirect_append else '2>'
            else:
                op = '>>' if redirect_append else '>'
            cmd_str = f"{cmd_str} {op} {redirect_file}"
            subprocess.call(cmd_str, shell=True)
            return b""
        else:
            result = subprocess.run(
                [command] + args[1:],
                executable=full_path,
                stdout=subprocess.PIPE,
                stderr=None
            )
            output = result.stdout if result.stdout else b""
            if output and should_print:
                sys.stdout.buffer.write(output)
                sys.stdout.buffer.flush()
            return output


# Global variables for tab completion
last_tab_text = ""
last_tab_matches = []
last_tab_count = 0


def get_executable_matches(text):
    """Find all executables in PATH that match the given prefix."""
    matches = []
    
    # First, check builtins
    builtins = ["exit", "echo", "type", "pwd", "cd", "history"]
    for cmd in builtins:
        if cmd.startswith(text):
            matches.append(cmd)
    
    # Then check executables in PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for dir_path in path_dirs:
        if not dir_path:
            continue
        
        try:
            for file_path in glob.glob(os.path.join(dir_path, "*")):
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    cmd_name = os.path.basename(file_path)
                    if cmd_name.startswith(text) and cmd_name not in matches:
                        matches.append(cmd_name)
        except Exception:
            pass
    
    return sorted(matches)


def get_longest_common_prefix(strings):
    """Get the longest common prefix of a list of strings."""
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]
        
    prefix = strings[0]
    for string in strings[1:]:
        # Find the length of common prefix
        length = 0
        for i, (c1, c2) in enumerate(zip(prefix, string)):
            if c1 != c2:
                break
            length = i + 1
        
        # Update prefix to common part
        prefix = prefix[:length]
        if not prefix:
            break
            
    return prefix


def complete(text, state):
    """Custom tab completion function for readline."""
    global last_tab_text, last_tab_matches, last_tab_count
    
    # Split the line to get the current command/args
    line = readline.get_line_buffer()
    
    # First word (command) completion
    if not line.strip() or " " not in line.lstrip():
        # New completion attempt or different text
        if text != last_tab_text:
            last_tab_text = text
            last_tab_matches = get_executable_matches(text)
            last_tab_count = 0
        
        # No matches
        if not last_tab_matches:
            if state == 0:
                sys.stdout.write('\a')  # Ring bell
                sys.stdout.flush()
            return None
            
        # Single match - add space
        if len(last_tab_matches) == 1:
            if state == 0:
                return last_tab_matches[0] + " "
            return None
            
        # Multiple matches
        # Try to complete to longest common prefix
        lcp = get_longest_common_prefix(last_tab_matches)
        if lcp and len(lcp) > len(text):
            # There's a longer common prefix - complete to it
            if state == 0:
                return lcp
            return None
        
        # No progress possible with LCP
        if last_tab_count == 0:
            # First tab press - increment counter, ring bell, return the text
            last_tab_count += 1
            if state == 0:
                sys.stdout.write('\a')  # Ring bell
                sys.stdout.flush()
                return text
            return None
        else:
            # Second tab press - display all matches
            if state == 0:
                print()  # New line
                print("  ".join(last_tab_matches))
                sys.stdout.write(f"$ {text}")
                sys.stdout.flush()
                return text
            return None
    
    # Multiple word completion (not implemented yet)
    if state == 0:
        return text
    return None


def main():
    global last_tab_count, last_tab_text
    
    # Setup readline
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)
    readline.set_completer_delims(" \t\n")
    
    while True:
        # Reset for new line
        last_tab_count = 0
        last_tab_text = ""
        
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            line = input()
        except EOFError:
            break
        
        if not line.strip():
            continue
        
        # Parse pipes FIRST
        def is_outside_quotes(pos, text):
            before = text[:pos]
            in_single = False
            in_double = False
            i = 0
            while i < len(before):
                if before[i] == '\\' and i + 1 < len(before):
                    i += 2
                    continue
                if before[i] == "'" and not in_double:
                    in_single = not in_single
                elif before[i] == '"' and not in_single:
                    in_double = not in_double
                i += 1
            return not in_single and not in_double
        
        # Find pipe positions
        pipe_parts = []
        current = ""
        for i, char in enumerate(line):
            if char == '|' and is_outside_quotes(i, line):
                pipe_parts.append(current.strip())
                current = ""
            else:
                current += char
        pipe_parts.append(current.strip())
        
        if len(pipe_parts) == 1:
            # No pipes
            cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipe_parts[0])
            args = shlex.split(cmd_part)
            if args:
                execute_command(args[0], args, redirect_file, redirect_stderr, redirect_append)
        else:
            # Has pipes
            processes = []
            prev_read_fd = None
            
            for idx, pipe_cmd in enumerate(pipe_parts):
                is_last = (idx == len(pipe_parts) - 1)
                cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipe_cmd)
                args = shlex.split(cmd_part)
                
                if not args:
                    continue
                
                command_name = args[0]
                
                builtins = ["exit", "echo", "type", "pwd", "cd", "history"]
                if command_name in builtins:
                    if not is_last:
                        read_fd, write_fd = os.pipe()
                        pid = os.fork()
                        if pid == 0:
                            if prev_read_fd is not None:
                                os.dup2(prev_read_fd, 0)
                                os.close(prev_read_fd)
                            os.dup2(write_fd, 1)
                            os.close(write_fd)
                            os.close(read_fd)
                            execute_command(command_name, args, redirect_file, redirect_stderr, redirect_append)
                            sys.exit(0)
                        else:
                            processes.append(pid)
                            os.close(write_fd)
                            if prev_read_fd is not None:
                                os.close(prev_read_fd)
                            prev_read_fd = read_fd
                    else:
                        if prev_read_fd is not None:
                            try:
                                os.read(prev_read_fd, 1000000)
                            except:
                                pass
                            os.close(prev_read_fd)
                        execute_command(command_name, args, redirect_file, redirect_stderr, redirect_append)
                    continue
                
                full_path = find_executable(command_name)
                if not full_path:
                    print(f"{command_name}: command not found")
                    break
                
                if not is_last:
                    read_fd, write_fd = os.pipe()
                    proc = subprocess.Popen(
                        [command_name] + args[1:],
                        executable=full_path,
                        stdin=prev_read_fd,
                        stdout=write_fd,
                        stderr=subprocess.DEVNULL
                    )
                    processes.append(proc)
                    os.close(write_fd)
                    if prev_read_fd is not None:
                        os.close(prev_read_fd)
                    prev_read_fd = read_fd
                else:
                    if redirect_file:
                        if redirect_stderr:
                            op = '2>>' if redirect_append else '2>'
                        else:
                            op = '>>' if redirect_append else '>'
                        cmd_str = f"{command_name} {' '.join(args[1:])} {op} {redirect_file}"
                        proc = subprocess.Popen(cmd_str, shell=True, stdin=prev_read_fd, stdout=None, stderr=None)
                    else:
                        proc = subprocess.Popen(
                            [command_name] + args[1:],
                            executable=full_path,
                            stdin=prev_read_fd,
                            stdout=None,
                            stderr=subprocess.DEVNULL
                        )
                    processes.append(proc)
                    if prev_read_fd is not None:
                        os.close(prev_read_fd)
            
            for proc in processes:
                if isinstance(proc, int):
                    os.waitpid(proc, 0)
                else:
                    proc.wait()


if __name__ == "__main__":
    main()
