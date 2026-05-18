import os
import signal
import psutil

current_pid = os.getpid()
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] == 'python.exe':
            # Don't kill ourselves
            if proc.info['pid'] == current_pid:
                continue
            
            # Check if it's the bot
            cmdline = proc.info['cmdline']
            if cmdline and any('main.py' in part for part in cmdline):
                print(f"Killing process {proc.info['pid']}: {cmdline}")
                os.kill(proc.info['pid'], signal.SIGTERM)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
