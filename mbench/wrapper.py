import sys
import os
import subprocess
from mbench.profile import FunctionProfiler, profileme

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m mbench.wrapper <command>")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    
    # Set up profiling
    profileme()
    
    # Run the command
    process = subprocess.Popen(command, shell=True)
    process.wait()

if __name__ == "__main__":
    main()
