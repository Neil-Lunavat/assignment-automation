import PyPDF2
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class PDFParser:
    def __init__(self, pdf_file):
        """Initialize with a PDF file path or file object."""
        self.pdf_file = pdf_file
        self.text = self._extract_text()
        
        # Initialize API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Parse the PDF content with Gemini
        self._parse_with_gemini()
        
    def _extract_text(self):
        """Extract all text from the PDF."""
        try:
            pdf_reader = PyPDF2.PdfReader(self.pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def _parse_with_gemini(self):
        """Use Gemini API to extract all needed information from the PDF text."""
        prompt = f"""
        Analyze the following assignment text and extract these specific details:
        1. Assignment Type: Determine if this is a Python, C++, or other type of assignment
        2. Assignment Number: Extract the assignment number
        3. Problem Statement: Extract the full problem statement
        4. Theory Points: Extract all theory points as a list

        Format your response EXACTLY as follows (with no other text):
        ```json
        {{
            "assignment_type": "python or cpp or other",
            "assignment_number": "number or Unknown if not found",
            "problem_statement": "full problem statement",
            "theory_points": [
                "theory point 1",
                "theory point 2",
                "etc..."
            ]
        }}
        ```

        Here is the assignment text:
        {self.text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract the JSON string
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                import json
                parsed_data = json.loads(json_match.group(1))
                
                # Set the class properties
                self.assignment_type = parsed_data.get("assignment_type", "unknown")
                self.assignment_number = parsed_data.get("assignment_number", "Unknown")
                self._problem_statement = parsed_data.get("problem_statement", "Could not extract problem statement")
                self._theory_points = parsed_data.get("theory_points", ["Could not extract theory points"])
            else:
                # Fallback to defaults if JSON parsing fails
                self.assignment_type = "unknown"
                self.assignment_number = "Unknown"
                self._problem_statement = "Could not extract problem statement"
                self._theory_points = ["Could not extract theory points"]
                
        except Exception as e:
            print(f"Error parsing with Gemini: {str(e)}")
            # Set default values if Gemini API fails
            self.assignment_type = "unknown"
            self.assignment_number = "Unknown"
            self._problem_statement = "Could not extract problem statement"
            self._theory_points = ["Could not extract theory points"]
            
    def extract_problem_statement(self):
        """Return the extracted problem statement."""
        return self._problem_statement
    
    def extract_theory_points(self):
        """Return the extracted theory points."""
        return self._theory_points
    
    def extract_assignment_number(self):
        """Return the extracted assignment number."""
        return self.assignment_number