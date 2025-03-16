import streamlit as st
import os
import tempfile
import base64
from dotenv import load_dotenv
import extra_streamlit_components as stx

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

def main():
    """Main function to run the Streamlit application."""
    
    # Create a container for the header with title and help button
    header_container = st.container()
    title_col, help_col = header_container.columns([5, 1])
    
    with title_col:
        st.title("🗿 Assignment Automation Tool")
        st.markdown("Upload an assignment PDF and get the code solution and writeup automatically.")

    with help_col:
        # Add some vertical space to align with the title
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
        
    if "show_success" not in st.session_state:
        st.session_state.show_success = False
    
    # Initialize processing_complete in session state if it doesn't exist
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False

    stored_info = cookie_manager.get("student_info")
    if not stored_info:
        stored_info = {
            "name": "",
            "prn": "",
            "batch": ""
        }
    
    # Create the sidebar inputs with stored values as defaults
    # Create the form with horizontal inputs using columns
    st.header("Student Information")

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

    # Save values to cookies when form is submitted
    if st.button("Save Information"):
        cookie_manager.set("student_info", student_info)
        st.session_state.show_success = True
    
    if st.session_state.show_success:
        st.success("Information saved to cookies!")
        
    # Display current information
    st.write("Crosscheck current student information:")
    st.write('```\n' + '\n'.join([i.upper() + ": " + student_info[i] for i in student_info.keys()]) + '\n```')

    # File uploader
    st.subheader("Upload Assignment PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        # Process button
        if st.button("Process Assignment"):
            with st.spinner("Processing"):
                # Initialize progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
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
                
                # Step 2: Use Gemini API to generate code and writeup
                status_text.text("Generating code solution using Gemini...")
                gemini = GeminiAPI()
                code_response = gemini.generate_code(problem_statement, assignment_type)
                progress_bar.progress(40)
                
                status_text.text("Generating theoretical writeup using Gemini...")
                writeup_response = gemini.generate_writeup(theory_points, code_response, assignment_number, problem_statement, assignment_type)
                progress_bar.progress(60)
                
                # Step 3: Execute the code
                status_text.text("Executing code with test inputs...")
                code_executor = CodeExecutor(code_response, assignment_type)
                code, outputs = code_executor.execute_code(f"C:\\Users\\{student_info['name']}\\Desktop\\programs", assignment_type)
                progress_bar.progress(70)

                # Step 4: Generate markdown and PDF
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

                # Save markdown to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp_md:
                    upload_pdf_content = markdown_gen.generate_upload_markdown()
                    tmp_md.write(upload_pdf_content.encode())
                    markdown_path = tmp_md.name
                
                # Convert markdown to PDF
                md_to_pdf = MarkdownToPDF()
                pdf_output_path = os.path.join(tempfile.gettempdir(), filename)
                try:
                    md_to_pdf.save_pdf(upload_pdf_content, pdf_output_path)
                    with open(pdf_output_path, "rb") as pdf_file:
                        pdf_content = pdf_file.read()
                    
                    # Format the writeup
                    writeup_formatter = WriteupFormatter(writeup_response)
                    formatted_writeup = writeup_formatter.format_content()
                    
                    progress_bar.progress(100)
                    status_text.text("Processing complete!")
                    
                    # Save results to session state so they persist between re-renders
                    st.session_state.processing_complete = True
                    st.session_state.formatted_writeup = formatted_writeup
                    st.session_state.pdf_content = pdf_content
                    st.session_state.upload_pdf_content = upload_pdf_content
                    st.session_state.assignment_number = assignment_number
                    st.session_state.filename = filename
                    
                    # Clean up temporary files
                    try:
                        os.unlink(pdf_path)
                        os.unlink(markdown_path)
                        os.unlink(pdf_output_path)
                    except:
                        pass
                    
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")

        if st.session_state.processing_complete:
            # Create tabs outside the button click handler so they persist
            tab1, tab2 = st.tabs(["Theory Writeup", "Upload Code PDF"])
                  
            # Display content in tabs based on session state
            with tab1:
                # Still keep the download option
                st.download_button(
                    label="Download Writeup as Text",
                    data=st.session_state.formatted_writeup,
                    file_name=f"Assignment_{st.session_state.assignment_number}_Writeup.txt",
                    mime="text/plain"
                )
                
                # Display the writeup
                st.markdown(st.session_state.formatted_writeup)
            
            with tab2:
                st.download_button(
                    label="Download PDF",
                    data=st.session_state.pdf_content,
                    file_name=st.session_state.filename,
                    mime="application/pdf"
                )
                st.markdown(st.session_state.upload_pdf_content)
        
    # Footer
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

if __name__ == "__main__":
    main()