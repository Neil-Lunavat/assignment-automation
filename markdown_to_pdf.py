import requests
import os
import tempfile

class MarkdownToPDF:
    def __init__(self):
        """Initialize the Markdown to PDF converter."""
        self.api_url = "https://md-to-pdf.fly.dev"
    
    def convert(self, markdown_content):
        """Convert markdown content to PDF using the md-to-pdf API."""
        styling = """body {
  font-size: 75%;
}

table {
  border-collapse: collapse;
}

table, th, td {
  border: 1px solid DimGray;
}

th, td {
  text-align: left;
  padding: 1em;
}"""
        try:
            # Prepare the data for the API request
            data = {
                'markdown': markdown_content,
                'css': styling,
                'engine': 'weasyprint'  # Default engine
            }
            
            # Make the API request
            response = requests.post(self.api_url, data=data)
            
            # Check if the request was successful
            if response.status_code == 200:
                return response.content  # Return the PDF content
            else:
                raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error converting markdown to PDF: {str(e)}")
    
    def save_pdf(self, markdown_content, output_path):
        """Convert markdown to PDF and save to file."""
        pdf_content = self.convert(markdown_content)
        
        with open(output_path, 'wb') as file:
            file.write(pdf_content)
        
        return output_path
    
    def convert_file(self, markdown_file_path, output_path=None):
        """Convert a markdown file to PDF and save it."""
        # Read the markdown file
        with open(markdown_file_path, 'r') as file:
            markdown_content = file.read()
        
        # If output path is not specified, use the same name with .pdf extension
        if output_path is None:
            base_name = os.path.splitext(markdown_file_path)[0]
            output_path = base_name + '.pdf'
        
        # Convert and save
        return self.save_pdf(markdown_content, output_path)