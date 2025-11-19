import os
import subprocess
import sys
import shutil

# -----------------------------
# CONFIG
# -----------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")
ENV_EXAMPLE_FILE = os.path.join(PROJECT_ROOT, ".env.example")

# -----------------------------
# 1. Create virtual environment
# -----------------------------
venv_dir = os.path.join(PROJECT_ROOT, "venv")

if not os.path.exists(venv_dir):
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"])
else:
    print("Virtual environment already exists.")

# -----------------------------
# 2. Activate & install dependencies
# -----------------------------
if os.name == "nt":
    pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
else:
    pip_executable = os.path.join(venv_dir, "bin", "pip")

print("Installing dependencies...")
subprocess.run([pip_executable, "install", "-r", "requirements.txt"])

# -----------------------------
# 3. Create .env if missing
# -----------------------------
if not os.path.exists(ENV_FILE):
    print("Creating .env file from .env.example")
    shutil.copyfile(ENV_EXAMPLE_FILE, ENV_FILE)
    print("Please open .env and fill in CLIENT_ID and CLIENT_SECRET before continuing.")
    sys.exit(0)
else:
    print(".env file exists, using it.")

# -----------------------------
# 4. Run ETL to populate database
# -----------------------------
print("Running ETL process to fetch games and screenshots...")
if os.name == "nt":
    python_exec = os.path.join(venv_dir, "Scripts", "python.exe")
else:
    python_exec = os.path.join(venv_dir, "bin", "python")

subprocess.run([python_exec, "-m", "src.etl_fetch"])

# -----------------------------
# 5. Launch Streamlit dashboard
# -----------------------------
print("Launching Streamlit dashboard...")
subprocess.r
