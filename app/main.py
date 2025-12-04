import sys
import os
import subprocess
def main():
    while True:
        sys.stdout.write('$ ')
        sys.stdout.flush()
        try:
            user_input = input()
        except EOFError:
            break
        if not user_input.strip():
            continue
        args = user_input.split()
        command = args[0]
        if command == 'exit':
            sys.exit(int(args[1]) if len(args) > 1 else 0)
        elif command == 'echo':
            print(' '.join(args[1:]))
        elif command == 'type':
            if len(args) < 2:
                print('type: usage: type command')
                continue
            target = args[1]
            builtins = ['echo', 'exit', 'type', 'pwd', 'cd']
            if target in builtins:
                print(f'{target} is a shell builtin')
            else:
                found = False
                for path_dir in os.environ.get('PATH', '').split(os.pathsep):
                    full_path = os.path.join(path_dir, target)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        print(full_path)
                        found = True
                        break
                if not found:
                    print(f'{target}: not found')
        elif command == 'pwd':
            print(os.getcwd())
        elif command == 'cd':
            if len(args) < 2:
                os.chdir(os.path.expanduser('~'))
            else:
                path = args[1]
                if path.startswith('~'):
                    path = os.path.expanduser(path)
                try:
                    os.chdir(path)
                except FileNotFoundError:
                    print(f'cd: {path}: No such file or directory', file=sys.stderr)
        else:
            found = False
            for path_dir in os.environ.get('PATH', '').split(os.pathsep):
                full_path = os.path.join(path_dir, command)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    try:
                        subprocess.run([full_path] + args[1:])
                        found = True
                        break
                    except Exception:
                        found = True
                        break
            if not found:
                print(f'{command}: command not found')
if __name__ == '__main__':
    main()
