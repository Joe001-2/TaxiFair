import os
import subprocess
import sys

def kill_python_bots():
    try:
        # Use tasklist to find python processes
        output = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'], text=True)
        lines = output.strip().split('\n')
        if len(lines) <= 1:
            print("No python processes found.")
            return

        current_pid = str(os.getpid())
        
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) > 1:
                pid = parts[1].strip('"')
                if pid == current_pid:
                    continue
                
                print(f"Attempting to kill PID {pid}...")
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    kill_python_bots()
