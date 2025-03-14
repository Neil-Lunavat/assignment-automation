import PyPDF2
import re

class PDFParser:
    def __init__(self, pdf_file):
        """Initialize with a PDF file path or file object."""
        self.pdf_file = pdf_file
        self.text = self._extract_text()
        self.assignment_type = self._determine_assignment_type()
    
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
    
    def _determine_assignment_type(self):
        """Determine if this is a C++ or Python assignment based on content."""
        
        if "Python" in self.text:
            return "python"
        elif "C++" in self.text or "Object Oriented Programming":
            return "cpp"
        
    
    def extract_problem_statement(self):
        """Extract the problem statement from the PDF, handling different formats."""
        # First try the standard format
        pattern = r"Problem Statement:(.+?)(?:Objective:|OBJECTIVE:|$)"
        match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try to find a problem statement after "AIM:" (common in C++ assignments)
        if self.assignment_type == "cpp":
            pattern = r"AIM:(.+?)(?:OBJECTIVE:|$)"
            match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try to extract from Title + Problem Statement format
        pattern = r"Title:(.+?)Problem Statement:(.+?)(?:Objective:|$)"
        match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
        if match:
            return f"{match.group(1).strip()}\n\n{match.group(2).strip()}"
        
        return "Could not extract problem statement"
    
    def extract_theory_points(self):
        """Extract theory points from the PDF, handling different formats."""
        theory_points = []
        
        # Look for the theory section
        pattern = r"Theory:(.+?)(?:Algorithm:|ALGORITHM|Software Requirements:|$)"
        match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
        if match:
            theory_text = match.group(1).strip()
            
            # Extract bullet points with bullet character
            bullet_points = re.findall(r"[●•]\s*([^●•]+?)(?=[●•]|$)", theory_text, re.DOTALL)
            if bullet_points:
                theory_points.extend([point.strip() for point in bullet_points if point.strip()])
            
            # If no bullet points found, try looking for numbered points or other formats
            if not theory_points:
                # Try extracting points with dashes
                dash_points = re.findall(r"-\s*([^-]+?)(?=[-]|$)", theory_text, re.DOTALL)
                if dash_points:
                    theory_points.extend([point.strip() for point in dash_points if point.strip()])
        
        # For C++ assignments, check the NOTE section which often contains theory points
        if self.assignment_type == "cpp" and not theory_points:
            pattern = r"NOTE:(.+?)(?:ALGORITHM|Algorithm|CONCLUSION|$)"
            match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
            if match:
                note_text = match.group(1).strip()
                
                # Extract bullet points from NOTE section
                bullet_points = re.findall(r"[●•]\s*([^●•]+?)(?=[●•]|$)", note_text, re.DOTALL)
                if bullet_points:
                    theory_points.extend([point.strip() for point in bullet_points if point.strip()])
        
        # If still no theory points found, return the whole theory section
        if not theory_points and match:
            return [match.group(1).strip()]
        
        return theory_points if theory_points else ["Could not extract theory points"]
    
    def extract_assignment_number(self):
        """Extract assignment number from the PDF."""
        # Try multiple patterns to catch different formats
        patterns = [
            r"Assignment\s+(?:No\.?|Number)?\s*(\d+)",
            r"Assignment\s*#\s*(\d+)",
            r"Assignment\s*(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"