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

def execute_command(command, args, redirect_file=None, redirect_stderr=False, redirect_append=False, stdin_data=None, should_print=True):
    """Execute a single command with optional redirection and stdin.
    should_print: if True, print output for last command; if False, just return bytes for pipeline."""
    if command == "exit":
        sys.exit(0)
    elif command == "echo":
        output = " ".join(args[1:]) + '\n'
        output_bytes = output.encode()
        # Only redirect if it's stdout redirection (not stderr)
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        elif redirect_file and redirect_stderr:
            # Write to stderr file, never print to stdout
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode, encoding='utf-8') as f:
                f.write(output)
            return b""  # No output to terminal or pipeline
        else:
            if should_print:
                sys.stdout.buffer.write(output_bytes)
                sys.stdout.buffer.flush()
            return output_bytes
    elif command == "type":
        if len(args) < 2:
            return b""
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
        
        output += '\n'
        output_bytes = output.encode()
        # Only redirect if it's stdout redirection (not stderr)
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        elif redirect_file and redirect_stderr:
            # Write to stderr file, never print to stdout
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode, encoding='utf-8') as f:
                f.write(output)
            return b""  # No output to terminal or pipeline
        else:
            if should_print:
                sys.stdout.buffer.write(output_bytes)
                sys.stdout.buffer.flush()
            return output_bytes
    elif command == "pwd":
        output = os.getcwd() + '\n'
        output_bytes = output.encode()
        # Only redirect if it's stdout redirection (not stderr)
        if redirect_file and not redirect_stderr:
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode) as f:
                f.write(output)
            return b""
        elif redirect_file and redirect_stderr:
            # Write to stderr file, never print to stdout
            dir_path = os.path.dirname(redirect_file)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = 'a' if redirect_append else 'w'
            with open(redirect_file, mode, encoding='utf-8') as f:
                f.write(output)
            return b""  # No output to terminal or pipeline
        else:
            if should_print:
                sys.stdout.buffer.write(output_bytes)
                sys.stdout.buffer.flush()
            return output_bytes
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
        return b""
    else:
        full_path = find_executable(command)
        if full_path:
            # Use full_path to locate executable, but pass command name as argv[0]
            stdout_target = None
            stderr_target = None
            
            if redirect_file:
                dir_path = os.path.dirname(redirect_file)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                if redirect_stderr:
                    mode = 'ab' if redirect_append else 'wb'
                    stderr_target = open(redirect_file, mode, buffering=0)
                else:
                    mode = 'ab' if redirect_append else 'wb'
                    stdout_target = open(redirect_file, mode, buffering=0)
            
            # Determine stdout handling
            if stdout_target:
                stdout_param = stdout_target
            elif redirect_file and not redirect_stderr:
                stdout_param = None  # Will be redirected to file
            elif redirect_stderr:
                stdout_param = None  # Go to terminal when stderr is redirected
            else:
                stdout_param = subprocess.PIPE  # Capture for pipeline or display
            
            # Build subprocess arguments
            subprocess_args = {
                'args': [command] + args[1:],
                'executable': full_path,
                'stdout': stdout_param,
                'stderr': stderr_target.fileno() if stderr_target else None
            }

            # Ensure stderr is redirected to file when requested
            if redirect_stderr and redirect_file and stderr_target is None:
                mode = 'ab' if redirect_append else 'wb'
                stderr_target = open(redirect_file, mode)
                subprocess_args['stderr'] = stderr_target.fileno()

            # Use input parameter if stdin_data is provided, otherwise don't set stdin
            if stdin_data is not None:
                subprocess_args['input'] = stdin_data
            # Don't set stdin parameter when using input

            result = subprocess.run(**subprocess_args)

            # Close files after subprocess completes
            if stdout_target:
                try:
                    stdout_target.flush()
                    os.fsync(stdout_target.fileno())
                except:
                    pass
                stdout_target.close()
            if stderr_target:
                try:
                    stderr_target.flush()
                    os.fsync(stderr_target.fileno())
                except:
                    pass
                stderr_target.close()

            # Return output for pipeline or print if no redirection
            if stdout_param == subprocess.PIPE:
                output = result.stdout if result.stdout else b""
                return output
            return b""
        else:
            print(f"{command}: command not found")
            return b""

def parse_redirection(cmd_line):
    """Parse redirection from a command line and return (command_part, redirect_file, redirect_stderr, redirect_append)."""
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
    
    redirect_pos = -1
    redirect_op = None
    
    # Check for append operators first (2>>, 1>>, >>)
    for i in range(len(cmd_line) - 2, -1, -1):
        if cmd_line[i:i+3] == '2>>' and is_outside_quotes(i, cmd_line):
            redirect_pos = i
            redirect_op = '2>>'
            redirect_stderr = True
            redirect_append = True
            break
    
    if redirect_pos == -1:
        for i in range(len(cmd_line) - 2, -1, -1):
            if cmd_line[i:i+3] == '1>>' and is_outside_quotes(i, cmd_line):
                redirect_pos = i
                redirect_op = '1>>'
                redirect_stderr = False
                redirect_append = True
                break
    
    if redirect_pos == -1:
        for i in range(len(cmd_line) - 1, -1, -1):
            if cmd_line[i:i+2] == '>>' and is_outside_quotes(i, cmd_line):
                redirect_pos = i
                redirect_op = '>>'
                redirect_stderr = False
                redirect_append = True
                break
    
    # Check for redirect operators (2>, 1>, >)
    if redirect_pos == -1:
        for i in range(len(cmd_line) - 1, -1, -1):
            if cmd_line[i:i+2] == '2>' and is_outside_quotes(i, cmd_line):
                redirect_pos = i
                redirect_op = '2>'
                redirect_stderr = True
                redirect_append = False
                break
    
    if redirect_pos == -1:
        for i in range(len(cmd_line) - 1, -1, -1):
            if cmd_line[i:i+2] == '1>' and is_outside_quotes(i, cmd_line):
                redirect_pos = i
                redirect_op = '1>'
                redirect_stderr = False
                redirect_append = False
                break
    
    if redirect_pos == -1:
        for i in range(len(cmd_line) - 1, -1, -1):
            if cmd_line[i] == '>' and is_outside_quotes(i, cmd_line):
                if i + 1 < len(cmd_line) and cmd_line[i+1] == '>':
                    continue
                redirect_pos = i
                redirect_op = '>'
                redirect_stderr = False
                redirect_append = False
                break
    
    if redirect_pos != -1:
        cmd_part = cmd_line[:redirect_pos].strip()
        redirect_file = cmd_line[redirect_pos + len(redirect_op):].strip()
        if redirect_file.startswith('"') and redirect_file.endswith('"'):
            redirect_file = redirect_file[1:-1]
        elif redirect_file.startswith("'") and redirect_file.endswith("'"):
            redirect_file = redirect_file[1:-1]
        return cmd_part, redirect_file, redirect_stderr, redirect_append
    
    return cmd_line, None, False, False

def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            line = input()
            if not line.strip():
                continue
            
            # Helper function to check if position is outside quotes
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
            
            # Parse pipelines first
            pipeline_commands = []
            current_pos = 0
            while current_pos < len(line):
                pipe_pos = -1
                for i in range(current_pos, len(line)):
                    if line[i] == '|' and is_outside_quotes(i, line):
                        pipe_pos = i
                        break
                
                if pipe_pos == -1:
                    pipeline_commands.append(line[current_pos:].strip())
                    break
                else:
                    pipeline_commands.append(line[current_pos:pipe_pos].strip())
                    current_pos = pipe_pos + 1
            
            # Execute pipeline
            if len(pipeline_commands) == 1:
                # Single command - no pipeline
                cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(pipeline_commands[0])
                args = shlex.split(cmd_part)
                if args:
                    command = args[0]
                    execute_command(command, args, redirect_file, redirect_stderr, redirect_append, None, should_print=True)
            else:
                # Pipeline - execute commands with real pipes
                processes = []
                prev_read_fd = None

                for idx, cmd_line in enumerate(pipeline_commands):
                    is_last = (idx == len(pipeline_commands) - 1)

                    # Parse redirection (only on last command)
                    if is_last:
                        cmd_part, redirect_file, redirect_stderr, redirect_append = parse_redirection(cmd_line)
                    else:
                        cmd_part, redirect_file, redirect_stderr, redirect_append = cmd_line, None, False, False

                    args = shlex.split(cmd_part)
                    if not args:
                        continue
                    command = args[0]

                    # Create pipe for next command (if not last)
                    if not is_last:
                        read_fd, write_fd = os.pipe()
                    else:
                        read_fd, write_fd = None, None

                    # Setup stdout
                    stdout_target = None
                    stderr_target = None
                    if redirect_file:
                        dir_path = os.path.dirname(redirect_file)
                        if dir_path:
                            os.makedirs(dir_path, exist_ok=True)
                        if redirect_stderr:
                            mode = 'ab' if redirect_append else 'wb'
                            stderr_target = open(redirect_file, mode, buffering=0)
                        else:
                            mode = 'ab' if redirect_append else 'wb'
                            stdout_target = open(redirect_file, mode, buffering=0)

                    # Determine stdout
                    if stdout_target:
                        stdout_param = stdout_target
                    elif write_fd:
                        stdout_param = write_fd
                    elif is_last:
                        stdout_param = None  # Go to terminal
                    else:
                        stdout_param = subprocess.PIPE

                    # Handle builtin commands in pipeline
                    if command in ["echo", "type", "pwd", "cd", "exit"]:
                        # Execute builtin synchronously and write output to pipe
                        output = execute_command(command, args, None, False, False, None, should_print=False)
                        if output:
                            if write_fd:
                                os.write(write_fd, output)
                                os.close(write_fd)
                            elif is_last:
                                # Last builtin in pipeline - print output
                                execute_command(command, args, redirect_file, redirect_stderr, redirect_append, None, should_print=True)
                        if prev_read_fd:
                            os.close(prev_read_fd)
                        prev_read_fd = read_fd
                        continue

                    # External command
                    full_path = find_executable(command)
                    if not full_path:
                        print(f"{command}: command not found")
                        if prev_read_fd:
                            os.close(prev_read_fd)
                        if write_fd:
                            os.close(write_fd)
                        break

                    # Start process
                    proc = subprocess.Popen(
                        [command] + args[1:],
                        executable=full_path,
                        stdin=prev_read_fd,
                        stdout=stdout_param if not hasattr(stdout_param, 'fileno') else stdout_param.fileno(),
                        stderr=stderr_target.fileno() if stderr_target else None
                    )

                    processes.append((proc, stdout_target, stderr_target, prev_read_fd, write_fd))

                    # Close pipe ends in parent (child has its own copy)
                    if prev_read_fd:
                        os.close(prev_read_fd)
                    if write_fd:
                        os.close(write_fd)

                    prev_read_fd = read_fd

                # Wait for all processes and handle cleanup
                for proc, stdout_target, stderr_target, stdin_fd, stdout_fd in processes:
                    try:
                        proc.wait()  # This will return when process exits or gets SIGPIPE
                    except Exception:
                        pass  # Process may have already exited

                    if stdout_target:
                        try:
                            stdout_target.flush()
                            stdout_target.close()
                        except Exception:
                            pass
                    if stderr_target:
                        try:
                            stderr_target.flush()
                            stderr_target.close()
                        except Exception:
                            pass
        except EOFError:
            break

if __name__ == "__main__":
    main()
