import subprocess

python_files = ["main.py", "gui.py"]

for file in python_files:
    subprocess.run(["python", file])
