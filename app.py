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
    page_icon="📚",
    layout="wide"
)

cookie_manager = stx.CookieManager()

def main():
    """Main function to run the Streamlit application."""
    # Header
    st.title("📚 Assignment Automation Tool")
    st.markdown("Upload an assignment PDF and get the code solution and writeup automatically.")
    
    if "show_success" not in st.session_state:
        st.session_state.show_success = False

    stored_info = cookie_manager.get("student_info")
    if not stored_info:
        stored_info = {
            "name": "",
            "prn": "",
            "batch": ""
        }
    
   # Create the sidebar inputs with stored values as defaults
    st.sidebar.header("Student Information")
    student_info = {
        "name": st.sidebar.text_input("Name", stored_info["name"]),
        "prn": st.sidebar.text_input("PRN", stored_info["prn"]),
        "batch": st.sidebar.text_input("Batch", stored_info["batch"])
    }
    
    # Save values to cookies when form is submitted
    if st.sidebar.button("Save Information"):
        cookie_manager.set("student_info", student_info)
        st.session_state.show_success = True
    
    if st.session_state.show_success:
        st.success("Information saved to cookies!")
        
    # Display current information
    st.write("Current Student Information:")
    st.write('```\n' + '\n'.join([i.upper() + ": " + student_info[i] for i in student_info.keys()]) + '\n```')

    # File uploader
    st.header("Upload Assignment PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        # Process button
        if st.button("Process Assignment"):
            with st.spinner("Generating code and write up..."):
                # Initialize progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Parse the PDF
                status_text.text("Extracting problem statement and theory points...")
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
                status_text.text("Generating code solution...")
                gemini = GeminiAPI()
                code_response = gemini.generate_code(problem_statement, assignment_type)
                progress_bar.progress(40)
                
                status_text.text("Generating theoretical writeup...")
                writeup_response = gemini.generate_writeup(theory_points, code_response, assignment_number, problem_statement, assignment_type)
                progress_bar.progress(60)
                
                # Step 3: Execute the code
                status_text.text("Executing code with test inputs...")
                code_executor = CodeExecutor(code_response)
                outputs = code_executor.execute_code(f"C:\\Users\\{student_info["name"]}\\Desktop\\programs")
                code = code_executor.get_code_content()
                progress_bar.progress(70)
                
                # Step 4: Generate markdown and PDF
                status_text.text("Generating markdown and PDF...")
                markdown_gen = MarkdownGenerator(
                    assignment_number,
                    student_info["name"],
                    student_info["prn"],
                    student_info["batch"],
                    problem_statement,
                    code,
                    outputs
                )
                
                filename = f"{student_info["prn"]}_{student_info["name"].split(' ')[0]}_{student_info["batch"]}.pdf"

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
                    
                    # Display results
                    st.header("Results")
                    
                    # Create tabs for different outputs
                    tab1, tab2 = st.tabs(["Theory Writeup", "Upload Code PDF"])
                    
                    with tab1:
                        # Add a download link for the writeup
                        st.download_button(
                            label="Download Writeup as Text",
                            data=formatted_writeup,
                            file_name=f"Assignment_{assignment_number}_Writeup.txt",
                            mime="text/plain"
                        )

                        st.markdown(formatted_writeup)
                    
                    with tab2:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_content,
                            file_name=filename,
                            mime="application/pdf"
                        )                

                        st.markdown(upload_pdf_content)
                        
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
                    
                # Clean up temporary files
                try:
                    os.unlink(pdf_path)
                    os.unlink(markdown_path)
                    os.unlink(pdf_output_path)
                except:
                    pass
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 Assignment Automation Tool | Made by [Neil](https://www.linkedin.com/in/neil-lunavat) with ❤️")

if __name__ == "__main__":
    main()