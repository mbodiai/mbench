import sys
import os
import subprocess
from mbench.profile import profileme

def stream_subprocess(command):
    # Start the subprocess
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, shell=True)

    # Stream stdout line by line
    for stdout_line in iter(process.stdout.readline, ""):
        yield stdout_line  # Yield the line as it's received

    process.stdout.close()  # Close the stdout pipe

    # Wait for the process to complete and get the exit code
    return_code = process.wait()

    # Stream any remaining stderr lines
    for stderr_line in iter(process.stderr.readline, ""):
        yield stderr_line  # Yield the error line

    process.stderr.close()  # Close the stderr pipe

    if return_code != 0:
        yield f"Process exited with code {return_code}\n"
    

def main(command=None):
    if not command and len(sys.argv) < 2:
        print("Usage: python -m mbench.wrapper <command>")
        print("Setting command to 'python -m pytest tests/'")
        command = "python -m pytest tests/"
    command = command or  " ".join(sys.argv[1:])
    
    # Set up profiling
    profileme()
    
    # Run the command
    for line in stream_subprocess(command):
        print(line, end="")


if __name__ == "__main__":
    main()
