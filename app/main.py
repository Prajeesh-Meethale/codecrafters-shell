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
    
    # Check for 2>> FIRST (before >>)
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '2>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+3:].strip(), True, True
    
    # Check for 2> (before >)
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '2>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), True, False
    
    # Check for 1>> BEFORE >> (THIS WAS THE BUG)
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '1>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+3:].strip(), False, True
    
    # Check for 1> (before >)
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '1>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), False, False
    
    # Check for >> (after 1>> is already checked)
    for i in range(len(cmd_line) - 1, -1, -1):
        if cmd_line[i:i+2] == '>>' and is_outside_quotes(i, cmd_line):
            return cmd_line[:i].strip(), cmd_line[i+2:].strip(), False, True
    
    # Check for > (last, after all >> variants checked)
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
        
        # Handle stdout redirection (>, >>, 1>, 1>>)
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            # DO NOT print to stdout when redirected
            return b""
        
        # Handle stderr redirection (2>, 2>>) - creates empty file since echo has no stderr
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass  # Just create/truncate the file
        
        # Only print to stdout if NOT redirected
        sys.stdout.write(output)
        sys.stdout.flush()
        return b""
    
    elif command == "type":
        if len(args) < 2:
            return b""
        target = args[1]
        if target in ["exit", "echo", "type", "pwd", "cd"]:
            output = f"{target} is a shell builtin\n"
        else:
            full_path = find_executable(target)
            if full_path:
                output = f"{full_path}\n"
            else:
                output = f"{target}: not found\n"
        
        # Handle stdout redirection (>, >>, 1>, 1>>)
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            # DO NOT print to stdout when redirected
            return b""
        
        # Handle stderr redirection (2>, 2>>) - creates empty file since type has no stderr
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass  # Just create/truncate the file
        
        # Only print to stdout if NOT redirected
        sys.stdout.write(output)
        sys.stdout.flush()
        return b""
    
    elif command == "pwd":
        output = os.getcwd() + '\n'
        
        # Handle stdout redirection (>, >>, 1>, 1>>)
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            # DO NOT print to stdout when redirected
            return b""
        
        # Handle stderr redirection (2>, 2>>) - creates empty file since pwd has no stderr
        if redirect_stderr and redirect_file:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                pass  # Just create/truncate the file
        
        # Only print to stdout if NOT redirected
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
    
    else:
        # EXTERNAL COMMAND - use shell=True for redirection
        full_path = find_executable(command)
        if not full_path:
            print(f"{command}: command not found")
            return b""
        
        # Build command line
        cmd_str = ' '.join([command] + args[1:])
        
        if redirect_file:
            # Add redirection operator
            if redirect_stderr:
                op = '2>>' if redirect_append else '2>'
            else:
                op = '>>' if redirect_append else '>'
            cmd_str = f"{cmd_str} {op} {redirect_file}"
            # Use shell to handle redirection
            subprocess.call(cmd_str, shell=True)
            return b""
        else:
            # No redirection
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


def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            line = input()
            
            if not line.strip():
                continue
            
            # Check for pipes
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
            
            # Split by pipes
            pipe_parts = []
            current = ""
            for i, char in enumerate(line):
                if char == '|' and is_outside_quotes(i, line):
                    pipe_parts.append(current.strip())
                    current = ""
                else:
                    current += char
            pipe_parts.append(current.strip())
            
            # Execute
            if len(pipe_parts) == 1:
                # No pipe
                cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipe_parts[0])
                args = shlex.split(cmd_part)
                if args:
                    execute_command(args[0], args, redirect_file, redirect_stderr, redirect_append)
            else:
                # With pipes
                processes = []
                prev_read_fd = None
                
                for idx, pipe_cmd in enumerate(pipe_parts):
                    is_last = (idx == len(pipe_parts) - 1)
                    cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipe_cmd)
                    args = shlex.split(cmd_part)
                    
                    if not args:
                        continue
                    
                    command = args[0]
                    
                    # Check if it's a built-in command
                    builtins = ["exit", "echo", "type", "pwd", "cd"]
                    if command in builtins:
                        # Handle built-in in pipeline
                        if not is_last:
                            # Not last - capture output to pipe
                            read_fd, write_fd = os.pipe()
                            
                            # Fork to execute built-in
                            pid = os.fork()
                            if pid == 0:
                                # Child process
                                if prev_read_fd is not None:
                                    os.dup2(prev_read_fd, 0)
                                    os.close(prev_read_fd)
                                os.dup2(write_fd, 1)
                                os.close(write_fd)
                                os.close(read_fd)
                                
                                # Execute built-in
                                execute_command(command, args, redirect_file, redirect_stderr, redirect_append)
                                sys.exit(0)
                            else:
                                # Parent process
                                processes.append(pid)
                                os.close(write_fd)
                                if prev_read_fd is not None:
                                    os.close(prev_read_fd)
                                prev_read_fd = read_fd
                        else:
                            # Last command - execute built-in directly
                            if prev_read_fd is not None:
                                # Read and discard stdin for commands like type
                                try:
                                    os.read(prev_read_fd, 1000000)
                                except:
                                    pass
                                os.close(prev_read_fd)
                            execute_command(command, args, redirect_file, redirect_stderr, redirect_append)
                        continue
                    
                    # External command handling
                    full_path = find_executable(command)
                    
                    if not full_path:
                        print(f"{command}: command not found")
                        break
                    
                    if not is_last:
                        # Not last - create pipe for this command's output
                        read_fd, write_fd = os.pipe()
                        
                        proc = subprocess.Popen(
                            [command] + args[1:],
                            executable=full_path,
                            stdin=prev_read_fd,
                            stdout=write_fd,
                            stderr=subprocess.DEVNULL
                        )
                        processes.append(proc)
                        
                        # Close write end in parent (child has its own copy)
                        os.close(write_fd)
                        
                        # Close previous read fd now that we've passed it to the child
                        if prev_read_fd is not None:
                            os.close(prev_read_fd)
                        
                        # Save read end for next command
                        prev_read_fd = read_fd
                    else:
                        # Last command - reads from prev_read_fd, writes to stdout (or file)
                        if redirect_file:
                            # Handle redirection for last command
                            if redirect_stderr:
                                op = '2>>' if redirect_append else '2>'
                            else:
                                op = '>>' if redirect_append else '>'
                            cmd_str = f"{command} {' '.join(args[1:])} {op} {redirect_file}"
                            proc = subprocess.Popen(
                                cmd_str,
                                shell=True,
                                stdin=prev_read_fd,
                                stdout=None,
                                stderr=None
                            )
                        else:
                            # No redirection - output goes to terminal
                            proc = subprocess.Popen(
                                [command] + args[1:],
                                executable=full_path,
                                stdin=prev_read_fd,
                                stdout=None,
                                stderr=subprocess.DEVNULL
                            )
                        processes.append(proc)
                        
                        # Close the read fd after passing to last command
                        if prev_read_fd is not None:
                            os.close(prev_read_fd)
                
                # Wait for all processes
                for proc in processes:
                    if isinstance(proc, int):
                        # It's a PID from fork
                        os.waitpid(proc, 0)
                    else:
                        # It's a Popen object
                        proc.wait()
        
        except EOFError:
            break
        except KeyboardInterrupt:
            continue


if __name__ == "__main__":
    main()
