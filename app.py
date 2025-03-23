import streamlit as st
import os
import tempfile
import base64
from dotenv import load_dotenv
import extra_streamlit_components as stx
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

# Load local modules
from pdf_parser import PDFParser
from gemini_api import GeminiAPI
from code_executor import CodeExecutor, TestCase
from markdown_generator import MarkdownGenerator, WriteupFormatter
from markdown_to_pdf import MarkdownToPDF

# Create a global temporary directory for the session
def get_session_temp_dir():
    """Get or create a temporary directory for the current session."""
    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = tempfile.mkdtemp()
    return st.session_state.temp_dir

# Main application function
def main():
    """Main function to run the Streamlit application."""
    # Initialize session state
    init_session_state()
    
    # Create a common temporary directory for this session
    temp_dir = get_session_temp_dir()
    
    # Render header
    render_header()
    
    # Get student information
    student_info = render_student_info_section()
    
    # File uploader for assignment PDF
    st.subheader("Upload Assignment PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Save the uploaded file to the session temp directory
        pdf_path = save_uploaded_file(uploaded_file, temp_dir=temp_dir)
        
        # Render file handling section if needed
        requires_file_handling, test_files = render_file_handling_section()
        
        # Process button
        if st.button("Process Assignment", type="primary"):
            success = process_assignment(
                pdf_path, 
                student_info, 
                requires_file_handling,
                test_files,
                temp_dir
            )
    
    # Display results if processing is complete
    display_results()
    
    # Render footer
    render_footer()

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Assignment Automation Tool",
    page_icon="🗿",
    layout="wide"
)

cookie_manager = stx.CookieManager()

def render_file_handling_section():
    """Render the file handling section for test files."""
    st.subheader("File Handling")
    st.session_state.requires_file_handling = st.checkbox(
        "This assignment requires file handling", 
        value=st.session_state.requires_file_handling
    )
    
    if st.session_state.requires_file_handling:
        st.info("Upload test files for your code to use during execution. Files will be renamed to data.txt, data1.txt, etc.")
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
        else:
            st.session_state.uploaded_test_files = []
    else:
        st.session_state.uploaded_test_files = []
    
    return st.session_state.requires_file_handling, st.session_state.uploaded_test_files

def display_results():
    """Display the processing results in tabs."""
    if not st.session_state.processing_complete:
        return
    
    # Create tabs for results
    tab1, tab2 = st.tabs(["Theory Writeup", "Upload Code PDF"])
    
    # Display content in tabs based on session state
    with tab1:
        # Download button for writeup
        st.download_button(
            label="Download Writeup as Text",
            data=st.session_state.formatted_writeup,
            file_name=f"Assignment_{st.session_state.assignment_number}_Writeup.txt",
            mime="text/plain"
        )
        
        # Display the writeup
        st.markdown(st.session_state.formatted_writeup)
    
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
    
    # Define the dialog function that will show the QR code
    @st.dialog("Support My Work")
    def show_qr_code():
        st.subheader("Scan to send a donation")
        qr_image_path = "assets/upi_qr.png"
            
        # Display the image if it exists
        with open(qr_image_path, "rb") as img_file:
            img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            st.markdown(f"""
                <div style="display: flex; justify-content: center;">
                    <img src="data:image/png;base64,{img_b64}" width="300" alt="UPI QR Code">
                </div>
            """, unsafe_allow_html=True)

        st.markdown("*Thank you for supporting! More AI tools coming up to steamroll your degree.*")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Buy me a Predator 🐺", type="primary", key="donate_button", use_container_width=True):
            show_qr_code()

# Initialize session state variables
def init_session_state():
    """Initialize session state variables if they don't exist."""
    # Add temp_dir to the session state initialization
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

def render_header():
    """Render application header and help button."""
    header_container = st.container()
    title_col, help_col = header_container.columns([5, 1])
    
    with title_col:
        st.title("🗿 Assignment Automation Tool")
        st.markdown("Upload an assignment PDF and get the code solution and writeup automatically.")

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

def save_uploaded_file(uploaded_file, temp_dir=None, index: int = None) -> str:
    """Save an uploaded file to a temporary location and return the path.
    
    Args:
        uploaded_file: The uploaded file object
        temp_dir: The temporary directory to save to (uses session temp dir if None)
        index: Optional index for naming files for file handling tests
        
    Returns:
        Path to the saved file
    """
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

def process_assignment(
    pdf_path: str, 
    student_info: Dict[str, str], 
    requires_file_handling: bool = False,
    test_files: List[Any] = None,
    temp_dir: str = None
) -> bool:
    """Process the assignment and return whether it was successful.
    
    Args:
        pdf_path: Path to the uploaded PDF file
        student_info: Dictionary containing student information
        requires_file_handling: Whether the assignment requires file handling
        test_files: List of uploaded test files for file handling
        temp_dir: The temporary directory to use
        
    Returns:
        True if processing was successful, False otherwise
    """
    # Use provided temp_dir or default to session's temp_dir
    if temp_dir is None:
        temp_dir = st.session_state.temp_dir
    
    # Initialize progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Parse the PDF
        status_text.text("Extracting problem statement and theory points using Gemini...")
        pdf_parser = PDFParser(pdf_path)
        problem_statement = pdf_parser.extract_problem_statement()
        theory_points = pdf_parser.extract_theory_points()
        assignment_number = pdf_parser.extract_assignment_number()
        assignment_type = pdf_parser.assignment_type
        progress_bar.progress(20)
        
        # Display extracted information
        st.subheader("Extracted Information")
        st.markdown(f"**Assignment Number:** {assignment_number}")
        with st.expander("Problem Statement"):
            st.write(problem_statement)
        with st.expander("Theory Points"):
            for point in theory_points:
                st.write(f"- {point}")
        
        # Step 2: Use Gemini API to generate code
        status_text.text("Generating code solution using Gemini...")
        gemini = GeminiAPI()
        code_response = gemini.generate_code(
            problem_statement, 
            assignment_type,
            requires_file_handling
        )
        progress_bar.progress(40)
        
        # Save test files if provided with standardized names
        file_paths = []
        if test_files:
            for i, file in enumerate(test_files):
                file_path = save_uploaded_file(file, temp_dir=temp_dir, index=i)
                file_paths.append(file_path)
                
            # Display information about renamed files
            # st.info(f"Test files have been renamed to: {', '.join([os.path.basename(path) for path in file_paths])}")
            # st.info(f"Files saved in: {temp_dir}")
        
        # Step 3: Execute the code
        status_text.text("Executing code with test inputs...")
        code_executor = CodeExecutor(code_response, assignment_type, temp_dir=temp_dir)
        working_dir = f"C:\\Users\\{student_info['name']}\\Desktop\\programs"
        code, outputs = code_executor.execute_code(working_dir, file_paths)
        progress_bar.progress(60)
        
        # Step 4: Generate theoretical writeup
        status_text.text("Generating theoretical writeup using Gemini...")
        writeup_response = gemini.generate_writeup(
            theory_points, 
            code_response, 
            assignment_number, 
            problem_statement, 
            assignment_type
        )
        progress_bar.progress(70)
        
        # Step 5: Generate markdown and PDF
        status_text.text("Generating markdown and PDF using md-to-pdf API...")
        markdown_gen = MarkdownGenerator(
            assignment_number,
            assignment_type,
            student_info["name"],
            student_info["prn"],
            student_info["batch"],
            problem_statement,
            code,
            outputs
        )
        
        filename = f"{student_info['prn']}_{student_info['name'].split(' ')[0]}_{student_info['batch']}.pdf"

        # Save markdown to temporary file in the session temp directory
        markdown_path = os.path.join(temp_dir, "output.md")
        upload_pdf_content = markdown_gen.generate_upload_markdown()
        with open(markdown_path, "w") as f:
            f.write(upload_pdf_content)
        
        # Convert markdown to PDF
        md_to_pdf = MarkdownToPDF()
        pdf_output_path = os.path.join(temp_dir, filename)
        
        md_to_pdf.save_pdf(upload_pdf_content, pdf_output_path)
        with open(pdf_output_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Format the writeup
        writeup_formatter = WriteupFormatter(writeup_response)
        formatted_writeup = writeup_formatter.format_content()
        
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        # Save results to session state
        st.session_state.processing_complete = True
        st.session_state.formatted_writeup = formatted_writeup
        st.session_state.pdf_content = pdf_content
        st.session_state.upload_pdf_content = upload_pdf_content
        st.session_state.assignment_number = assignment_number
        st.session_state.filename = filename
        
        # Note: We don't clean up temporary files as we're now using a session-wide temp dir
        # They'll be cleaned up when the session ends or the app is restarted
        
        return True
        
    except Exception as e:
        progress_bar.progress(100)
        status_text.text("Error processing assignment")
        st.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    main()