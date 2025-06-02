# utils/constant.py

import os

# Default values for regressor
DEFAULT_EPOCHS = 200
DEFAULT_LR = 0.01

# Constant for dirs
LOG_DIR = "logs"
RESULT_DIR = "results"
UPLOAD_DIR = "uploads"
MODEL_DIR = "models"
STATIC_DIR = "static"

# All directories that need to be created
ALL_DIRS = [LOG_DIR, RESULT_DIR, UPLOAD_DIR, MODEL_DIR, STATIC_DIR]

def ensure_all_directories_exist():
    """Ensure all required directories exist."""
    for directory in ALL_DIRS:
        os.makedirs(directory, exist_ok=True)