import PyPDF2
import re

class PDFParser:
    def __init__(self, pdf_file):
        """Initialize with a PDF file object."""
        self.pdf_file = pdf_file
        self.text = self._extract_text()
        
    def _extract_text(self):
        """Extract all text from the PDF."""
        pdf_reader = PyPDF2.PdfReader(self.pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def extract_problem_statement(self):
        """Extract the problem statement from the PDF."""
        # Look for the problem statement section
        pattern = r"Problem Statement:(.+?)(?:Objective:|$)"
        match = re.search(pattern, self.text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Alternative approach if the first pattern doesn't match
        pattern = r"Title:(.+?)Problem Statement:(.+?)(?:Objective:|$)"
        match = re.search(pattern, self.text, re.DOTALL)
        if match:
            return f"{match.group(1).strip()}\n\n{match.group(2).strip()}"
        
        return "Could not extract problem statement"
    
    def extract_theory_points(self):
        """Extract theory points from the PDF."""
        # Look for the theory section
        pattern = r"Theory:(.+?)(?:Algorithm:|Software Requirements:|$)"
        match = re.search(pattern, self.text, re.DOTALL)
        if match:
            theory_text = match.group(1).strip()
            
            # Extract bullet points if they exist
            bullet_points = re.findall(r"●\s*([^●]+)", theory_text)
            if bullet_points:
                return bullet_points
            else:
                return [theory_text]
        
        return ["Could not extract theory points"]
    
    def extract_assignment_number(self):
        """Extract assignment number from the PDF."""
        pattern = r"Assignment\s+(?:No\.?|Number)?\s*(\d+)"
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            return match.group(1)
        return "Unknown"