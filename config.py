import os
from typing import List, Dict, Any

# API Configuration
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"
MD_TO_PDF_API_URL = "https://md-to-pdf.fly.dev"

# Supported Programming Languages
SUPPORTED_LANGUAGES = ["python", "cpp", "c"]
DEFAULT_LANGUAGE = "python"

# File Configuration
SUPPORTED_FILE_EXTENSIONS = ["txt", "csv", "dat", "json", "xlsx", "xls"]
MAX_FILE_SIZE_MB = 10
DEFAULT_FILE_EXTENSION = ".txt"

# UI Configuration
PAGE_TITLE = "Assignment Automation Tool"
PAGE_ICON = "🗿"
LAYOUT = "wide"

# Video Tutorial
TUTORIAL_VIDEO_URL = "https://youtu.be/YMB0VlHbGEQ"

# File Naming Conventions
PRIMARY_TEST_FILE_NAME = "data"
SECONDARY_TEST_FILE_PREFIX = "data"

# Working Directory Display
DISPLAY_WORKING_DIR = "C:\\temp\\assignment_work"

# Security Keywords (for prompt injection detection)
SUSPICIOUS_COMMANDS = [
    "rm", "del", "format", "shutdown", "restart", "kill", "taskkill",
    "netstat", "ipconfig", "systeminfo", "whoami", "dir", "ls",
    "cd", "mkdir", "rmdir", "copy", "move", "ren", "attrib"
]

SUSPICIOUS_IMPORTS = [
    "os.system", "subprocess", "exec", "eval", "compile",
    "importlib", "sys.modules", "globals", "locals"
]

# Validation Settings
MAX_PROBLEM_STATEMENT_LENGTH = 10000
MIN_PROBLEM_STATEMENT_LENGTH = 10

# Session State Keys
SESSION_KEYS = {
    "temp_dir": "temp_dir",
    "show_success": "show_success", 
    "processing_complete": "processing_complete",
    "requires_file_handling": "requires_file_handling",
    "uploaded_test_files": "uploaded_test_files",
    "input_method": "input_method",
    "problem_statement": "problem_statement",
    "theory_points": "theory_points",
    "assignment_number": "assignment_number",
    "assignment_type": "assignment_type",
    "manual_input_saved": "manual_input_saved",
    "formatted_writeup": "formatted_writeup",
    "markdown_content": "markdown_content",
    "filename": "filename"
}

# Cookie Keys
COOKIE_KEYS = {
    "student_info": "student_info"
}

# Error Messages
ERROR_MESSAGES = {
    "no_api_key": "GEMINI_API_KEY is not set in the environment",
    "invalid_assignment": "This doesn't appear to be a valid programming assignment",
    "missing_info": "Please provide either a problem statement or theory points",
    "file_upload_required": "Please upload at least one test file for file handling",
    "processing_error": "Error processing assignment"
}

# Success Messages
SUCCESS_MESSAGES = {
    "info_saved": "Information saved to cookies!",
    "assignment_saved": "Assignment details saved successfully!",
    "files_uploaded": "Uploaded {count} test files for code execution.",
    "processing_complete": "Processing complete!"
} 