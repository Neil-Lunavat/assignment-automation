import streamlit as st
import os
import tempfile
import base64
import datetime
from dotenv import load_dotenv
import extra_streamlit_components as stx
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import json

# Load local modules
from pdf_parser import PDFParser
from gemini_api import GeminiAPI
from markdown_generator import MarkdownGenerator, WriteupFormatter
from markdown_to_pdf import MarkdownToPDF
import config

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT
)

# Initialize cookie manager
cookie_manager = stx.CookieManager()

# Create a global temporary directory for the session
def get_session_temp_dir():
    """Get or create a temporary directory for the current session."""
    if config.SESSION_KEYS["temp_dir"] not in st.session_state:
        st.session_state[config.SESSION_KEYS["temp_dir"]] = tempfile.mkdtemp()
    return st.session_state[config.SESSION_KEYS["temp_dir"]]

# Initialize session state variables
def init_session_state():
    """Initialize session state variables if they don't exist."""
    for key, value in config.SESSION_KEYS.items():
        if value not in st.session_state:
            if key == "temp_dir":
                st.session_state[value] = tempfile.mkdtemp()
            elif key == "show_success":
                st.session_state[value] = False
            elif key == "processing_complete":
                st.session_state[value] = False
            elif key == "requires_file_handling":
                st.session_state[value] = False
            elif key == "uploaded_test_files":
                st.session_state[value] = []
            elif key == "input_method":
                st.session_state[value] = "pdf"
            elif key == "problem_statement":
                st.session_state[value] = ""
            elif key == "theory_points":
                st.session_state[value] = []
            elif key == "assignment_number":
                st.session_state[value] = ""
            elif key == "assignment_type":
                st.session_state[value] = config.DEFAULT_LANGUAGE
            elif key == "manual_input_saved":
                st.session_state[value] = False
    
    # Initialize tutorial dialog state
    if "show_tutorial" not in st.session_state:
        st.session_state["show_tutorial"] = False

def render_header():
    """Render application header and help button."""
    header_container = st.container()
    title_col, help_col = header_container.columns([5, 1])
    
    with title_col:
        st.title(f"🗿 {config.PAGE_TITLE}")
        st.markdown("Upload an assignment PDF or manually enter details to get code solutions and writeups automatically.")
    with help_col:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("How to use?", key="header_tutorial_button", 
                     type="primary", help="Click to watch the tutorial video",
                     use_container_width=True):
            st.session_state["show_tutorial"] = True

def get_student_info() -> Dict[str, str]:
    """Get student information from cookies or create empty defaults."""
    stored_info = cookie_manager.get(config.COOKIE_KEYS["student_info"])
    if not stored_info:
        stored_info = {
            "name": "",
            "prn": "",
            "batch": ""
        }
    else:
        try:
            # Handle both string and dict formats
            if isinstance(stored_info, str):
                stored_info = json.loads(stored_info)
            elif not isinstance(stored_info, dict):
                stored_info = {
                    "name": "",
                    "prn": "",
                    "batch": ""
                }
        except (json.JSONDecodeError, TypeError):
            stored_info = {
                "name": "",
                "prn": "",
                "batch": ""
            }
    return stored_info

def save_student_info(student_info: Dict[str, str]):
    """Save student information to cookies."""
    try:
        # Set cookie with proper expiration (30 days)
        cookie_manager.set(
            config.COOKIE_KEYS["student_info"], 
            json.dumps(student_info),
            expires_at=datetime.datetime.now() + datetime.timedelta(days=30)
        )
        st.session_state[config.SESSION_KEYS["show_success"]] = True
        st.rerun()  # Force a rerun to update the UI
    except Exception as e:
        st.error(f"Failed to save information: {str(e)}")

def render_student_info_section() -> Dict[str, str]:
    """Render student information section and return the collected info."""
    st.header("Student Information")
    
    stored_info = get_student_info()
    
    # Create three columns with equal width
    col1, col2, col3 = st.columns(3)

    # Place each input field in its own column
    with col1:
        name = st.text_input("Name", stored_info["name"])
    with col2:
        prn = st.text_input("PRN", stored_info["prn"])
    with col3:
        batch = st.text_input("Batch", stored_info["batch"])

    # Save the collected information
    student_info = {
        "name": name,
        "prn": prn,
        "batch": batch
    }

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Save Information", type="primary", use_container_width=True):
            save_student_info(student_info)
    
    if st.session_state[config.SESSION_KEYS["show_success"]]:
        st.success(config.SUCCESS_MESSAGES["info_saved"])
        
    # Display current information
    st.write("Crosscheck current student information:")
    st.write('```\n' + '\n'.join([i.upper() + ": " + student_info[i] for i in student_info.keys()]) + '\n```')
    
    return student_info

def render_input_method_section():
    """Render section for choosing between PDF upload and manual input."""
    st.header("Assignment Details")
    
    # Create radio buttons for input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload PDF", "Manual Input"],
        index=0 if st.session_state[config.SESSION_KEYS["input_method"]] == "pdf" else 1,
        horizontal=True
    )
    
    st.session_state[config.SESSION_KEYS["input_method"]] = "pdf" if input_method == "Upload PDF" else "manual"
    
    return st.session_state[config.SESSION_KEYS["input_method"]]

def handle_pdf_upload(temp_dir):
    """Handle PDF upload and extraction."""
    st.subheader("Upload Assignment PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Save the uploaded file to the session temp directory
        pdf_path = save_uploaded_file(uploaded_file, temp_dir=temp_dir)
        
        # Extract information from PDF
        with st.spinner("Extracting information from PDF..."):
            pdf_parser = PDFParser(pdf_path)
            
            # Store extracted info in session state
            st.session_state[config.SESSION_KEYS["problem_statement"]] = pdf_parser.extract_problem_statement()
            st.session_state[config.SESSION_KEYS["theory_points"]] = pdf_parser.extract_theory_points()
            st.session_state[config.SESSION_KEYS["assignment_number"]] = pdf_parser.extract_assignment_number()
            st.session_state[config.SESSION_KEYS["assignment_type"]] = pdf_parser.assignment_type
            
            # Get file handling requirement directly from the parser
            st.session_state[config.SESSION_KEYS["requires_file_handling"]] = pdf_parser.requires_file_handling()
        
        # Display extracted information
        display_extracted_info()
        
        return True
    return False

def handle_manual_input():
    """Handle manual input of problem statement and theory points."""
    st.subheader("Manual Input")
    
    # Check if we already have valid input in the session state
    has_existing_input = (st.session_state[config.SESSION_KEYS["problem_statement"]] != "" or len(st.session_state[config.SESSION_KEYS["theory_points"]]) > 0)
    
    # Assignment number and type
    col1, col2 = st.columns(2)
    with col1:
        assignment_number = st.text_input(
            "Assignment Number", 
            value=st.session_state[config.SESSION_KEYS["assignment_number"]]
        )
    with col2:
        assignment_type = st.selectbox(
            "Programming Language",
            config.SUPPORTED_LANGUAGES,
            index=config.SUPPORTED_LANGUAGES.index(st.session_state[config.SESSION_KEYS["assignment_type"]])
        )
    
    # Problem statement
    problem_statement = st.text_area(
        "Problem Statement (include objectives and algorithm if available)",
        value=st.session_state[config.SESSION_KEYS["problem_statement"]],
        height=200,
        help="Include the main problem, objectives, and algorithm description if available"
    )
    
    # Theory points
    theory_input = st.text_area(
        "Theory Points (one per line)",
        value="\n".join(st.session_state[config.SESSION_KEYS["theory_points"]]),
        height=200
    )
    
    # Save button for inputs
    if st.button("Save Assignment Details", type="primary"):
        # Update session state with the input values
        st.session_state[config.SESSION_KEYS["assignment_number"]] = assignment_number
        st.session_state[config.SESSION_KEYS["assignment_type"]] = assignment_type
        st.session_state[config.SESSION_KEYS["problem_statement"]] = problem_statement
        st.session_state[config.SESSION_KEYS["theory_points"]] = "\n".join([point.strip() for point in theory_input.split("\n") if point.strip()])
        
        # Check if file handling is required
        if st.session_state[config.SESSION_KEYS["problem_statement"]]:
            st.session_state[config.SESSION_KEYS["requires_file_handling"]] = check_file_handling_required(
                st.session_state[config.SESSION_KEYS["problem_statement"]]
            )
        
        # Show success message
        st.success(config.SUCCESS_MESSAGES["assignment_saved"])
        
        # Display information that has been input
        display_extracted_info()
        
        # Set a flag in session state to remember we've saved
        st.session_state[config.SESSION_KEYS["manual_input_saved"]] = True
        
        return True
    
    # Return True if we've saved input in a previous run
    if has_existing_input and st.session_state.get(config.SESSION_KEYS["manual_input_saved"], False):
        display_extracted_info()
        return True
    
    return False

def display_extracted_info():
    """Display extracted or manually input information."""
    if (st.session_state[config.SESSION_KEYS["assignment_number"]] or 
        st.session_state[config.SESSION_KEYS["problem_statement"]] or 
        st.session_state[config.SESSION_KEYS["theory_points"]]):
        
        st.subheader("Assignment Information")
        st.markdown(f"**Assignment Number:** {st.session_state[config.SESSION_KEYS['assignment_number']]}")
        st.markdown(f"**Language:** {st.session_state[config.SESSION_KEYS['assignment_type']]}")
        
        with st.expander("Problem Statement", expanded=False):
            st.write(st.session_state[config.SESSION_KEYS["problem_statement"]])
        
        with st.expander("Theory Points", expanded=False):
            for point in st.session_state[config.SESSION_KEYS["theory_points"]]:
                st.write(f"- {point}")
        
        st.markdown(f"**Requires File Handling:** {'Yes' if st.session_state[config.SESSION_KEYS['requires_file_handling']] else 'No'}")

def check_file_handling_required(problem_statement):
    """Check if the problem requires file handling."""
    if not problem_statement:
        return False
        
    # Call Gemini API to check if file handling is required
    gemini = GeminiAPI()
    result = gemini.check_file_handling_required(problem_statement)
    return result

def save_uploaded_file(uploaded_file, temp_dir=None, index: Optional[int] = None) -> str:
    """Save an uploaded file to a temporary location and return the path.
    
    Args:
        uploaded_file: The uploaded file from Streamlit's file_uploader
        temp_dir: Optional temporary directory
        index: Optional index for standardized naming of test files
        
    Returns:
        Path to the saved file
    """
    # Use the provided temp_dir or default to session's temp_dir
    if temp_dir is None:
        temp_dir = st.session_state[config.SESSION_KEYS["temp_dir"]]
    
    # For file handling tests, use standardized names (data.txt, data1.txt, etc.)
    if index is not None:
        # Get the file extension from the original file
        _, ext = os.path.splitext(uploaded_file.name)
        # Use default .txt extension if none is provided
        ext = ext if ext else config.DEFAULT_FILE_EXTENSION
        # Create standardized filename (data.txt, data1.txt, etc.)
        if index == 0:
            # For the primary test file, use the exact name "data.txt" as expected in the code
            filename = f"{config.PRIMARY_TEST_FILE_NAME}{ext}"
        else:
            # For additional test files, add index
            filename = f"{config.SECONDARY_TEST_FILE_PREFIX}{index}{ext}"
        
        file_path = os.path.join(temp_dir, filename)
        
        # Write the file content
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        return file_path
    else:
        # For other files like PDFs, save to the temp directory
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        return file_path

def render_file_handling_section():
    """Render the file handling section for test files."""
    if st.session_state[config.SESSION_KEYS["requires_file_handling"]]:
        st.subheader("File Handling")
        st.info("This assignment requires file handling. Please upload test files.")
        
        # Explain the file naming convention for better clarity
        st.markdown(f"""
        **Note:** The first file you upload will be saved as `{config.PRIMARY_TEST_FILE_NAME}.txt` (or with its original extension), 
        which is the expected filename in the generated code. Additional files will be named 
        `{config.SECONDARY_TEST_FILE_PREFIX}1.txt`, `{config.SECONDARY_TEST_FILE_PREFIX}2.txt`, etc.
        """)
        
        uploaded_files = st.file_uploader(
            "Upload test files", 
            accept_multiple_files=True,
            type=config.SUPPORTED_FILE_EXTENSIONS
        )
        
        if uploaded_files:
            st.session_state[config.SESSION_KEYS["uploaded_test_files"]] = uploaded_files
            st.success(config.SUCCESS_MESSAGES["files_uploaded"].format(count=len(uploaded_files)))
            
            # Display file previews
            if len(uploaded_files) > 0:
                for i, file in enumerate(uploaded_files):
                    # Show how each file will be saved
                    _, ext = os.path.splitext(file.name)
                    ext = ext if ext else config.DEFAULT_FILE_EXTENSION
                    mapped_name = f"{config.PRIMARY_TEST_FILE_NAME}{ext}" if i == 0 else f"{config.SECONDARY_TEST_FILE_PREFIX}{i}{ext}"
                    
                    with st.expander(f"Preview: {file.name} → {mapped_name}"):
                        try:
                            # Try to decode as text first
                            content = file.getvalue().decode('utf-8')
                            st.text_area(f"File content", value=content, height=200)
                        except UnicodeDecodeError:
                            # If binary, show file info instead
                            file_size = len(file.getvalue())
                            st.warning(f"Binary file - {file_size} bytes - preview not available")
                            
                            # Check if it's an Excel file
                            if ext.lower() in ['.xlsx', '.xls']:
                                st.info("Excel file detected. The code will use this file for data processing.")
            
            return True, uploaded_files
        else:
            st.warning(config.ERROR_MESSAGES["file_upload_required"])
            return False, []
    else:
        st.session_state[config.SESSION_KEYS["uploaded_test_files"]] = []
        return True, []

def check_valid_assignment():
    """Check if the input is a valid programming assignment."""
    if not st.session_state[config.SESSION_KEYS["problem_statement"]] and not st.session_state[config.SESSION_KEYS["theory_points"]]:
        return False
        
    gemini = GeminiAPI()
    
    # Only check if we have at least some content
    if st.session_state[config.SESSION_KEYS["problem_statement"]]:
        validation_result = gemini.validate_programming_assignment(st.session_state[config.SESSION_KEYS["problem_statement"]])
        if not validation_result["is_valid"]:
            # Display security warnings if any
            security_check = validation_result.get("security_check", {})
            if security_check.get("suspicious_commands") or security_check.get("suspicious_imports") or security_check.get("injection_attempts"):
                st.warning("⚠️ Security concerns detected in the problem statement. Please review the content.")
            return False
    
    return True

def _validate_assignment_input():
    """Validate assignment input and return validation status."""
    if not st.session_state[config.SESSION_KEYS["problem_statement"]] and not st.session_state[config.SESSION_KEYS["theory_points"]]:
        return False, config.ERROR_MESSAGES["missing_info"]
    
    is_valid = check_valid_assignment()
    if not is_valid:
        return False, config.ERROR_MESSAGES["invalid_assignment"]
    
    return True, ""

def _save_test_files(temp_dir):
    """Save test files with standardized names."""
    file_paths = []
    if (st.session_state[config.SESSION_KEYS["requires_file_handling"]] and 
        st.session_state[config.SESSION_KEYS["uploaded_test_files"]]):
        for i, file in enumerate(st.session_state[config.SESSION_KEYS["uploaded_test_files"]]):
            file_path = save_uploaded_file(file, temp_dir=temp_dir, index=i)
            file_paths.append(file_path)
    return file_paths

def _generate_code_solution():
    """Generate code solution using Gemini API."""
    gemini = GeminiAPI()
    code_response = gemini.generate_code_and_outputs(
        st.session_state[config.SESSION_KEYS["problem_statement"]], 
        st.session_state[config.SESSION_KEYS["assignment_type"]],
        st.session_state[config.SESSION_KEYS["requires_file_handling"]]
    )
    return code_response

def _generate_theory_writeup(code_response):
    """Generate theoretical writeup using Gemini API."""
    if not st.session_state[config.SESSION_KEYS["theory_points"]]:
        return ""
    
    gemini = GeminiAPI()
    writeup_response = gemini.generate_writeup(
        st.session_state[config.SESSION_KEYS["theory_points"]], 
        code_response, 
        st.session_state[config.SESSION_KEYS["assignment_number"]], 
        st.session_state[config.SESSION_KEYS["problem_statement"]], 
        st.session_state[config.SESSION_KEYS["assignment_type"]]
    )
    return writeup_response

def _create_final_outputs(student_info, temp_dir, code_response, writeup_response):
    """Create final markdown and PDF outputs."""
    # Generate markdown
    markdown_gen = MarkdownGenerator(
        st.session_state[config.SESSION_KEYS["assignment_number"]],
        st.session_state[config.SESSION_KEYS["assignment_type"]],
        student_info["name"],
        student_info["prn"],
        student_info["batch"],
        st.session_state[config.SESSION_KEYS["problem_statement"]],
        code_response,  # Pass the raw code response
        []  # Empty outputs list since we're not executing code
    )
    
    filename = f"{student_info['prn']}_{student_info['name'].split(' ')[0]}_{student_info['batch']}.pdf"
    
    # Save markdown to temporary file
    markdown_path = os.path.join(temp_dir, "output.md")
    upload_pdf_content = markdown_gen.generate_upload_markdown()
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(upload_pdf_content)
    
    # Read the markdown file content
    with open(markdown_path, "rb") as md_file:
        markdown_content = md_file.read()

    # Convert markdown to PDF using the API
    md_to_pdf = MarkdownToPDF()
    pdf_output_path = os.path.join(temp_dir, filename)
    
    try:
        md_to_pdf.save_pdf(upload_pdf_content, pdf_output_path)
        with open(pdf_output_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
    except Exception as e:
        st.warning(f"PDF generation failed: {str(e)}. Providing markdown only.")
        pdf_content = None
    
    # Format the writeup
    formatted_writeup = ""
    if writeup_response:
        writeup_formatter = WriteupFormatter(writeup_response)
        formatted_writeup = writeup_formatter.format_content()
    
    return markdown_content, pdf_content, formatted_writeup, filename

def process_assignment(student_info, temp_dir):
    """Process the assignment based on the inputs and generate outputs."""
    # Initialize progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Validate assignment input
        status_text.text("Validating assignment...")
        is_valid, error_message = _validate_assignment_input()
        if not is_valid:
            status_text.text("Validation failed")
            st.error(error_message)
            progress_bar.progress(100)
            return False
        progress_bar.progress(10)
        
        # Step 2: Save test files if provided
        status_text.text("Processing test files...")
        file_paths = _save_test_files(temp_dir)
        progress_bar.progress(20)
        
        # Step 3: Generate code solution
        code_response = ""
        if st.session_state[config.SESSION_KEYS["problem_statement"]]:
            status_text.text("Generating code solution using Gemini...")
            code_response = _generate_code_solution()
            progress_bar.progress(50)
        
        # Step 4: Generate theoretical writeup
        status_text.text("Generating theoretical writeup using Gemini...")
        writeup_response = _generate_theory_writeup(code_response)
        progress_bar.progress(70)
        
        # Step 5: Create final outputs
        status_text.text("Generating markdown and PDF...")
        markdown_content, pdf_content, formatted_writeup, filename = _create_final_outputs(
            student_info, temp_dir, code_response, writeup_response
        )
        
        progress_bar.progress(100)
        status_text.text(config.SUCCESS_MESSAGES["processing_complete"])
        
        # Save results to session state
        st.session_state[config.SESSION_KEYS["processing_complete"]] = True
        st.session_state[config.SESSION_KEYS["formatted_writeup"]] = formatted_writeup
        st.session_state[config.SESSION_KEYS["markdown_content"]] = markdown_content
        st.session_state[config.SESSION_KEYS["filename"]] = filename
        st.session_state["pdf_content"] = pdf_content  # Store PDF content separately

        return True
        
    except Exception as e:
        progress_bar.progress(100)
        status_text.text("Error processing assignment")
        st.error(f"{config.ERROR_MESSAGES['processing_error']}: {str(e)}")
        return False

def display_results():
    """Display the processing results in tabs."""
    if not st.session_state[config.SESSION_KEYS["processing_complete"]]:
        return
    
    # Create tabs for results
    tab1, tab2, tab3 = st.tabs(["Theory Writeup", "Upload Code Markdown", "PDF Download"])
    
    # Display content in tabs based on session state
    with tab1:
        if st.session_state[config.SESSION_KEYS["formatted_writeup"]]:
            # Download button for writeup
            st.download_button(
                label="Download Writeup as Text",
                data=st.session_state[config.SESSION_KEYS["formatted_writeup"]],
                file_name=f"Assignment_{st.session_state[config.SESSION_KEYS['assignment_number']]}_Writeup.txt",
                mime="text/plain"
            )
            
            # Display the writeup
            st.markdown(st.session_state[config.SESSION_KEYS["formatted_writeup"]])
        else:
            st.info("No theory writeup was generated for this assignment.")
    
    with tab2:
        # Download button for Markdown
        st.download_button(
            label="Download Markdown",
            data=st.session_state[config.SESSION_KEYS["markdown_content"]],
            file_name=st.session_state[config.SESSION_KEYS["filename"]].replace('.pdf', '.md'),
            mime="text/markdown"
        )
        # Display the markdown content
        st.markdown(st.session_state[config.SESSION_KEYS["markdown_content"]].decode('utf-8'), unsafe_allow_html=False)
    
    with tab3:
        if st.session_state.get("pdf_content"):
            # Download button for PDF
            st.download_button(
                label="Download PDF",
                data=st.session_state["pdf_content"],
                file_name=st.session_state[config.SESSION_KEYS["filename"]],
                mime="application/pdf"
            )
            st.success("PDF generated successfully! Click the button above to download.")
        else:
            st.info("PDF generation was not available. Please download the markdown file instead.")

def render_footer():
    """Render the application footer with QR code dialog."""
    st.markdown("---")
    st.markdown("© 2025 Assignment Automation Tool | Made by [Neil](https://www.linkedin.com/in/neil-lunavat) with ❤️")
    
    @st.dialog("Support the Project")
    def show_qr_code():
        st.image("./assets/upi_qr.png", caption="Scan to contribute")
        st.markdown("Thank you for supporting this project! 🙏")
    
    # Create a container with right-aligned button
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; margin-top: 20px;">
        <div id="support-button-container"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Place the button in the right-aligned container
    button_container = st.container()
    with button_container:
        if st.button("Buy me a Predator 🐺", key="support_button", 
                     type="primary", use_container_width=False):
            show_qr_code()

def main():
    """Main function to run the Streamlit application."""
    # Initialize session state
    init_session_state()
    
    # Create a common temporary directory for this session
    temp_dir = get_session_temp_dir()
    
    # Render header
    render_header()
    
    # Show tutorial dialog if triggered
    if st.session_state.get("show_tutorial", False):
        @st.dialog("How to Use - Tutorial")
        def show_tutorial():
            st.video(config.TUTORIAL_VIDEO_URL)
            st.markdown("Watch this tutorial to learn how to use the Assignment Automation Tool effectively!")
        show_tutorial()
        st.session_state["show_tutorial"] = False  # Reset the flag
    
    # Get student information (unchanged)
    student_info = render_student_info_section()
    
    # Provide option to upload PDF or input manually
    input_method = render_input_method_section()
    
    has_input = False
    
    # Handle input based on selected method
    if input_method == "pdf":
        has_input = handle_pdf_upload(temp_dir)
    else:
        has_input = handle_manual_input()
    
    # Render file handling section if required
    file_handling_ready, test_files = True, []
    if has_input and st.session_state[config.SESSION_KEYS["requires_file_handling"]]:
        file_handling_ready, test_files = render_file_handling_section()
    
    # Process button
    if has_input and file_handling_ready:
        if st.button("Process Assignment", type="primary"):
            process_assignment(student_info, temp_dir)
    
    # Display results if processing is complete
    display_results()
    
    # Render footer (unchanged)
    render_footer()

if __name__ == "__main__":
    main()