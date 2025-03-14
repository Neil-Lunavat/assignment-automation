import streamlit as st
import os
import tempfile
import base64
from dotenv import load_dotenv

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

# Helper function to create a download link for the PDF
def get_pdf_download_link(pdf_content, filename, text):
    """Generate a download link for the PDF."""
    b64 = base64.b64encode(pdf_content).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    return href

def main():
    """Main function to run the Streamlit application."""
    # Header
    st.title("📚 Assignment Automation Tool")
    st.markdown("Upload an assignment PDF and get the code solution and writeup automatically.")
    
    # Sidebar for student information
    st.sidebar.header("Student Information")
    student_name = st.sidebar.text_input("Name", "")
    student_prn = st.sidebar.text_input("PRN", "")
    student_batch = st.sidebar.text_input("Batch", "")
    
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
            with st.spinner("Processing PDF..."):
                # Initialize progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Parse the PDF
                status_text.text("Extracting problem statement and theory points...")
                pdf_parser = PDFParser(pdf_path)
                problem_statement = pdf_parser.extract_problem_statement()
                theory_points = pdf_parser.extract_theory_points()
                assignment_number = pdf_parser.extract_assignment_number()
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
                code_response = gemini.generate_code(problem_statement)
                progress_bar.progress(40)
                
                status_text.text("Generating theoretical writeup...")
                writeup_response = gemini.generate_writeup(theory_points)
                progress_bar.progress(60)
                
                # Step 3: Execute the code
                status_text.text("Executing code with test inputs...")
                code_executor = CodeExecutor(code_response, code_response)
                outputs = code_executor.execute_code(f"C:\\Users\\{student_name}\\Desktop\\programs\\assignment_{assignment_number}.py")
                code = code_executor.get_code_content()
                progress_bar.progress(90)
                
                # Step 4: Generate markdown and PDF
                status_text.text("Generating markdown and PDF...")
                markdown_gen = MarkdownGenerator(
                    assignment_number,
                    student_name,
                    student_prn,
                    student_batch,
                    problem_statement,
                    code,
                    outputs
                )
                
                # Save markdown to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp_md:
                    markdown_content = markdown_gen.generate_upload_markdown()
                    tmp_md.write(markdown_content.encode())
                    markdown_path = tmp_md.name
                
                # Convert markdown to PDF
                md_to_pdf = MarkdownToPDF()
                pdf_output_path = os.path.join(tempfile.gettempdir(), f"Assignment_{assignment_number}.pdf")
                try:
                    md_to_pdf.save_pdf(markdown_content, pdf_output_path)
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
                    tab1, tab2, tab3 = st.tabs(["Code Solution", "Theoretical Writeup", "Download PDF"])
                    
                    with tab1:
                        st.subheader("Generated Python Code")
                        st.code(code, language="python")
                        
                        st.subheader("Execution Outputs")
                        for i, output in enumerate(outputs, 1):
                            with st.expander(f"Test Case {i}"):
                                st.text(output)
                    
                    with tab2:
                        st.subheader("Theoretical Writeup")
                        st.markdown(formatted_writeup)
                        
                        # Add a download link for the writeup
                        st.download_button(
                            label="Download Writeup as Text",
                            data=formatted_writeup,
                            file_name=f"Assignment_{assignment_number}_Writeup.txt",
                            mime="text/plain"
                        )
                    
                    with tab3:
                        st.subheader("Download Assignment PDF")
                        st.markdown(
                            get_pdf_download_link(
                                pdf_content,
                                f"{student_prn}_{student_name.split(' ')[0]}_{student_batch}.pdf",
                                "📥 Download PDF"
                            ),
                            unsafe_allow_html=True
                        )
                        
                        # Display a preview of the PDF
                        st.subheader("PDF Preview")
                        st.markdown(markdown_content)
                
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
    st.markdown("© 2025 Assignment Automation Tool | Made by [Neil](https://www.linkedin.com/in/neil-lunavat) with ❤️ using Streamlit and Gemini API")

if __name__ == "__main__":
    main()