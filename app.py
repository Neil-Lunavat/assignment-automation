import streamlit as st
import os
import tempfile
import base64
from dotenv import load_dotenv
import extra_streamlit_components as stx
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import json

# Load local modules
from pdf_parser import PDFParser
from gemini_api import GeminiAPI
from code_executor import CodeExecutor
from markdown_generator import MarkdownGenerator, WriteupFormatter
from markdown_to_pdf import MarkdownToPDF

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Assignment Automation Tool",
    page_icon="🗿",
    layout="wide"
)

cookie_manager = stx.CookieManager()

# Create a global temporary directory for the session
def get_session_temp_dir():
    """Get or create a temporary directory for the current session."""
    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = tempfile.mkdtemp()
    return st.session_state.temp_dir

# Initialize session state variables
def init_session_state():
    """Initialize session state variables if they don't exist."""
    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = tempfile.mkdtemp()
    
    if "show_success" not in st.session_state:
        st.session_state.show_success = False
    
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False
    
    if "requires_file_handling" not in st.session_state:
        st.session_state.requires_file_handling = False
    
    if "uploaded_test_files" not in st.session_state:
        st.session_state.uploaded_test_files = []
        
    if "input_method" not in st.session_state:
        st.session_state.input_method = "pdf"
        
    if "problem_statement" not in st.session_state:
        st.session_state.problem_statement = ""
        
    if "theory_points" not in st.session_state:
        st.session_state.theory_points = []
        
    if "assignment_number" not in st.session_state:
        st.session_state.assignment_number = ""
        
    if "assignment_type" not in st.session_state:
        st.session_state.assignment_type = "python"
        
    if "manual_input_saved" not in st.session_state:
        st.session_state.manual_input_saved = False

def render_header():
    """Render application header and help button."""
    header_container = st.container()
    title_col, help_col = header_container.columns([5, 1])
    
    with title_col:
        st.title("🗿 Assignment Automation Tool")
        st.markdown("Upload an assignment PDF or manually enter details to get code solutions and writeups automatically.")

    with help_col:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("""
                    <div style="display: flex; justify-content: flex-end; margin-top: 20px;">
                        <a href="" target="_blank">
                            <button style="background-color: #f63366; color: #000000; border: none; border-radius: 5px; padding: 10px 15px; cursor: pointer; font-weight: bold;">
                                How to use?
                            </button>
                        </a>
                    </div>
        """, unsafe_allow_html=True)

def get_student_info() -> Dict[str, str]:
    """Get student information from cookies or create empty defaults."""
    stored_info = cookie_manager.get("student_info")
    if not stored_info:
        stored_info = {
            "name": "",
            "prn": "",
            "batch": ""
        }
    return stored_info

def save_student_info(student_info: Dict[str, str]):
    """Save student information to cookies."""
    cookie_manager.set("student_info", student_info)
    st.session_state.show_success = True

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
    
    if st.session_state.show_success:
        st.success("Information saved to cookies!")
        
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
        index=0 if st.session_state.input_method == "pdf" else 1,
        horizontal=True
    )
    
    st.session_state.input_method = "pdf" if input_method == "Upload PDF" else "manual"
    
    return st.session_state.input_method

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
            st.session_state.problem_statement = pdf_parser.extract_problem_statement()
            st.session_state.theory_points = pdf_parser.extract_theory_points()
            st.session_state.assignment_number = pdf_parser.extract_assignment_number()
            st.session_state.assignment_type = pdf_parser.assignment_type
            
            # Get file handling requirement directly from the parser
            st.session_state.requires_file_handling = pdf_parser.requires_file_handling()
        
        # Display extracted information
        display_extracted_info()
        
        return True
    return False

def handle_manual_input():
    """Handle manual input of problem statement and theory points."""
    st.subheader("Manual Input")
    
    # Check if we already have valid input in the session state
    has_existing_input = (st.session_state.problem_statement != "" or len(st.session_state.theory_points) > 0)
    
    # Assignment number and type
    col1, col2 = st.columns(2)
    with col1:
        assignment_number = st.text_input(
            "Assignment Number", 
            value=st.session_state.assignment_number
        )
    with col2:
        assignment_type = st.selectbox(
            "Programming Language",
            ["python", "cpp", "c"],
            index=["python", "cpp", "c"].index(st.session_state.assignment_type)
        )
    
    # Problem statement
    problem_statement = st.text_area(
        "Problem Statement (include objectives and algorithm if available)",
        value=st.session_state.problem_statement,
        height=200,
        help="Include the main problem, objectives, and algorithm description if available"
    )
    
    # Theory points
    theory_input = st.text_area(
        "Theory Points (one per line)",
        value="\n".join(st.session_state.theory_points),
        height=200
    )
    
    # Save button for inputs
    if st.button("Save Assignment Details", type="primary"):
        # Update session state with the input values
        st.session_state.assignment_number = assignment_number
        st.session_state.assignment_type = assignment_type
        st.session_state.problem_statement = problem_statement
        st.session_state.theory_points = "\n".join([point.strip() for point in theory_input.split("\n") if point.strip()])
        
        # Check if file handling is required
        if st.session_state.problem_statement:
            st.session_state.requires_file_handling = check_file_handling_required(
                st.session_state.problem_statement
            )
        
        # Show success message
        st.success("Assignment details saved successfully!")
        
        # Display information that has been input
        display_extracted_info()
        
        # Set a flag in session state to remember we've saved
        st.session_state.manual_input_saved = True
        
        return True
    
    # Return True if we've saved input in a previous run
    if has_existing_input and st.session_state.get('manual_input_saved', False):
        display_extracted_info()
        return True
    
    return False

def display_extracted_info():
    """Display extracted or manually input information."""
    if st.session_state.assignment_number or st.session_state.problem_statement or st.session_state.theory_points:
        st.subheader("Assignment Information")
        st.markdown(f"**Assignment Number:** {st.session_state.assignment_number}")
        st.markdown(f"**Language:** {st.session_state.assignment_type}")
        
        with st.expander("Problem Statement", expanded=False):
            st.write(st.session_state.problem_statement)
        
        with st.expander("Theory Points", expanded=False):
            for point in st.session_state.theory_points:
                st.write(f"- {point}")
        
        st.markdown(f"**Requires File Handling:** {'Yes' if st.session_state.requires_file_handling else 'No'}")

def check_file_handling_required(problem_statement):
    """Check if the problem requires file handling."""
    if not problem_statement:
        return False
        
    # Call Gemini API to check if file handling is required
    gemini = GeminiAPI()
    result = gemini.check_file_handling_required(problem_statement)
    return result

def render_file_handling_section():
    """Render the file handling section for test files."""
    if st.session_state.requires_file_handling:
        st.subheader("File Handling")
        st.info("This assignment requires file handling. Please upload test files.")
        
        uploaded_files = st.file_uploader(
            "Upload test files", 
            accept_multiple_files=True,
            type=["txt", "csv", "dat", "json", "xlsx", "xls"]
        )
        
        if uploaded_files:
            st.session_state.uploaded_test_files = uploaded_files
            st.success(f"Uploaded {len(uploaded_files)} test files for code execution.")
            
            # Display file previews
            if len(uploaded_files) > 0:
                for i, file in enumerate(uploaded_files):
                    with st.expander(f"Preview: {file.name}"):
                        try:
                            content = file.getvalue().decode('utf-8')
                            st.text_area(f"File content", value=content, height=200)
                        except UnicodeDecodeError:
                            st.warning("Binary file - preview not available")
            
            return True, uploaded_files
        else:
            st.warning("Please upload at least one test file for file handling.")
            return False, []
    else:
        st.session_state.uploaded_test_files = []
        return True, []

def save_uploaded_file(uploaded_file, temp_dir=None, index: int = None) -> str:
    """Save an uploaded file to a temporary location and return the path."""
    # Use the provided temp_dir or default to session's temp_dir
    if temp_dir is None:
        temp_dir = st.session_state.temp_dir
    
    # For file handling tests, use standardized names (data.txt, data1.txt, etc.)
    if index is not None:
        # Get the file extension from the original file
        _, ext = os.path.splitext(uploaded_file.name)
        # Use default .txt extension if none is provided
        ext = ext if ext else ".txt"
        # Create standardized filename (data.txt, data1.txt, data2.txt, etc.)
        filename = f"data{index if index > 0 else ''}{ext}"
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

def check_valid_assignment():
    """Check if the input is a valid programming assignment."""
    if not st.session_state.problem_statement and not st.session_state.theory_points:
        return False
        
    gemini = GeminiAPI()
    
    # Only check if we have at least some content
    if st.session_state.problem_statement:
        is_valid = gemini.validate_programming_assignment(st.session_state.problem_statement)
        if not is_valid:
            return False
    
    return True

def process_assignment(student_info, temp_dir):
    """Process the assignment based on the inputs and generate outputs."""
    # Initialize progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Safety check
        status_text.text("Validating assignment...")
        is_valid = check_valid_assignment()
        if not is_valid:
            status_text.text("Invalid assignment")
            st.error("This doesn't appear to be a valid programming assignment. Please check your input.")
            progress_bar.progress(100)
            return False
        progress_bar.progress(10)
        
        # Step 2: Check if we have enough information to proceed
        if not st.session_state.problem_statement and not st.session_state.theory_points:
            status_text.text("Missing information")
            st.error("Please provide either a problem statement or theory points.")
            progress_bar.progress(100)
            return False
        
        # Step 3: Save test files if provided with standardized names
        file_paths = []
        if st.session_state.requires_file_handling and st.session_state.uploaded_test_files:
            status_text.text("Processing test files...")
            for i, file in enumerate(st.session_state.uploaded_test_files):
                file_path = save_uploaded_file(file, temp_dir=temp_dir, index=i)
                file_paths.append(file_path)
        progress_bar.progress(20)
        
        gemini = GeminiAPI()
        code_response = ""
        code = []
        outputs = []
        
        # Step 4: Generate code if we have a problem statement
        if st.session_state.problem_statement:
            status_text.text("Generating code solution using Gemini...")
            code_response = gemini.generate_code_and_outputs(
                st.session_state.problem_statement, 
                st.session_state.assignment_type,
                st.session_state.requires_file_handling
            )
            progress_bar.progress(40)
            
            # Step 5: Execute the code
            status_text.text("Executing code with test inputs...")
            code_executor = CodeExecutor(code_response, st.session_state.assignment_type, temp_dir=temp_dir)
            working_dir = f"C:\\Users\\{student_info['name']}\\Desktop\\programs"
            code, outputs = code_executor.execute_code(working_dir, file_paths)
            progress_bar.progress(60)
        
        # Step 6: Generate theoretical writeup if we have theory points
        writeup_response = ""
        if st.session_state.theory_points:
            status_text.text("Generating theoretical writeup using Gemini...")
            writeup_response = gemini.generate_writeup(
                st.session_state.theory_points, 
                code_response, 
                st.session_state.assignment_number, 
                st.session_state.problem_statement, 
                st.session_state.assignment_type
            )
            progress_bar.progress(70)
        
        # Step 7: Generate markdown and PDF
        status_text.text("Generating markdown and PDF...")
        markdown_gen = MarkdownGenerator(
            st.session_state.assignment_number,
            st.session_state.assignment_type,
            student_info["name"],
            student_info["prn"],
            student_info["batch"],
            st.session_state.problem_statement,
            code,
            outputs
        )
        
        filename = f"{student_info['prn']}_{student_info['name'].split(' ')[0]}_{student_info['batch']}.pdf"
        
        # Save markdown to temporary file in the session temp directory
        markdown_path = os.path.join(temp_dir, "output.md")
        upload_pdf_content = markdown_gen.generate_upload_markdown()
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(upload_pdf_content)
 
        # Convert markdown to PDF
        md_to_pdf = MarkdownToPDF()
        pdf_output_path = os.path.join(temp_dir, filename)
        
        md_to_pdf.save_pdf(upload_pdf_content, pdf_output_path)
        with open(pdf_output_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Format the writeup
        formatted_writeup = ""
        if writeup_response:
            writeup_formatter = WriteupFormatter(writeup_response)
            formatted_writeup = writeup_formatter.format_content()
        
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        # Save results to session state
        st.session_state.processing_complete = True
        st.session_state.formatted_writeup = formatted_writeup
        st.session_state.pdf_content = pdf_content
        st.session_state.upload_pdf_content = upload_pdf_content
        st.session_state.filename = filename
        
        return True
        
    except Exception as e:
        progress_bar.progress(100)
        status_text.text("Error processing assignment")
        st.error(f"Error: {str(e)}")
        return False

def display_results():
    """Display the processing results in tabs."""
    if not st.session_state.processing_complete:
        return
    
    # Create tabs for results
    tab1, tab2 = st.tabs(["Theory Writeup", "Upload Code PDF"])
    
    # Display content in tabs based on session state
    with tab1:
        if st.session_state.formatted_writeup:
            # Download button for writeup
            st.download_button(
                label="Download Writeup as Text",
                data=st.session_state.formatted_writeup,
                file_name=f"Assignment_{st.session_state.assignment_number}_Writeup.txt",
                mime="text/plain"
            )
            
            # Display the writeup
            st.markdown(st.session_state.formatted_writeup)
        else:
            st.info("No theory writeup was generated for this assignment.")
    
    with tab2:
        # Download button for PDF
        st.download_button(
            label="Download PDF",
            data=st.session_state.pdf_content,
            file_name=st.session_state.filename,
            mime="application/pdf"
        )
        # Display the markdown content
        st.markdown(st.session_state.upload_pdf_content)

def render_footer():
    """Render the application footer."""
    st.markdown("---")
    st.markdown("© 2025 Assignment Automation Tool | Made by [Neil](https://www.linkedin.com/in/neil-lunavat) with ❤️")
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; margin-top: 20px;">
        <a href="https://www.buymeacoffee.com/neil3196" target="_blank">
            <button style="background-color: #7765E3; color: #000000; border: none; border-radius: 5px; padding: 10px 15px; cursor: pointer; font-weight: bold;">
                Buy me a Predator 🐺
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main function to run the Streamlit application."""
    # Initialize session state
    init_session_state()
    
    # Create a common temporary directory for this session
    temp_dir = get_session_temp_dir()
    
    # Render header
    render_header()
    
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
    if has_input and st.session_state.requires_file_handling:
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