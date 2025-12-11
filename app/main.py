import sys
import shutil
import subprocess
import os
import shlex
import readline

# ------------------------------
# Builtins
# ------------------------------


def builtin_exit(args):
    sys.exit(0)


def builtin_cd(args):
    path = os.path.expanduser(args[0]) if args else os.path.expanduser("~")
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {args[0]}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {args[0]}: Not a directory")
    except PermissionError:
        print(f"cd: {args[0]}: Permission denied")


def builtin_pwd(args):
    print(os.getcwd())


def builtin_echo(args):
    print(" ".join(args))


def builtin_type(args):
    if not args:
        print("")
        return

    target = args[0]
    if target in BUILTINs:
        print(f"{target} is a shell builtin")
        return

    path = shutil.which(target)
    if path:
        print(f"{target} is {path}")
        return

    print(f"{target}: not found")


BUILTINs = {
    "exit": builtin_exit,
    "echo": builtin_echo,
    "type": builtin_type,
    "pwd": builtin_pwd,
    "cd": builtin_cd,
}

# ------------------------------
# Redirection parser
# ------------------------------

COMMAND = ["echo", "exit"]


def completer(text, state):

    options = [cmd for cmd in COMMAND if cmd.startswith(text)]
    if state < len(options):
        return options[state] + " "
    else:
        return None


def parse_redirection(parts):
    """
    Detects:
        cmd args > file, 1> file, >> file, 1>> file, 2> file
    Returns:
        clean_parts, stdout_file, stderr_file, stdout_append
    """
    stdout_file = None
    stderr_file = None
    stdout_append = False
    stderr_append = False
    clean_parts = []

    i = 0
    while i < len(parts):
        tok = parts[i]

        # stdout overwrite
        if tok in [">", "1>"] and i + 1 < len(parts):
            stdout_file = parts[i + 1]
            stdout_append = False
            i += 2
            continue

        # stdout append
        if tok in [">>", "1>>"] and i + 1 < len(parts):
            stdout_file = parts[i + 1]
            stdout_append = True
            i += 2
            continue

        # stderr overwrite
        if tok == "2>" and i + 1 < len(parts):
            stderr_file = parts[i + 1]
            stderr_append = False
            i += 2
            continue

        if tok == "2>>" and i + 1 < len(parts):
            stderr_file = parts[i + 1]
            stderr_append = True
            i += 2
            continue

        # normal token
        clean_parts.append(tok)
        i += 1

    return clean_parts, stdout_file, stderr_file, stdout_append, stderr_append


# ------------------------------
# Main shell loop
# ------------------------------


def main():

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            command = input().strip()
        except EOFError:
            print()
            break

        if not command:
            continue

        parts = shlex.split(command)
        parts, stdout_file, stderr_file, stdout_append, stderr_append = (
            parse_redirection(parts)
        )

        if not parts:
            continue

        cmd = parts[0]
        args = parts[1:]

        # Builtins
        if cmd in BUILTINs:
            save_stdout = sys.stdout
            save_stderr = sys.stderr
            try:
                if stdout_file:
                    sys.stdout = open(stdout_file, "a" if stdout_append else "w")
                if stderr_file:
                    sys.stderr = open(stderr_file, "a" if stderr_append else "w")
                BUILTINs[cmd](args)
            finally:
                if stdout_file:
                    sys.stdout.close()
                if stderr_file:
                    sys.stderr.close()
                sys.stdout = save_stdout
                sys.stderr = save_stderr
            continue

        # External commands
        path = shutil.which(cmd)
        if path:
            stdout_target = (
                open(stdout_file, "a" if stdout_append else "w")
                if stdout_file
                else None
            )
            stderr_target = (
                open(stderr_file, "a" if stderr_append else "w")
                if stderr_file
                else None
            )

            subprocess.run([cmd] + args, stdout=stdout_target, stderr=stderr_target)

            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()
            continue

        # Unknown command
        print(f"{command}: command not found", file=sys.stderr)


if __name__ == "__main__":
    main()
