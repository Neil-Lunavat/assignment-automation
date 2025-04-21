class MarkdownGenerator:
    def __init__(self, assignment_number, assignment_type, student_name, student_prn, student_batch, problem_statement, code, outputs):
        """Initialize with all necessary content for generating markdown."""
        self.assignment_number = assignment_number
        self.assignment_type = assignment_type
        self.student_name = student_name
        self.student_prn = student_prn
        self.student_batch = student_batch
        self.problem_statement = self._condense_problem_statement(problem_statement)
        self.code = code
        self.outputs = outputs
    
    def _condense_problem_statement(self, problem_statement):
        """Create a more concise version of the problem statement.
        
        Args:
            problem_statement: The original problem statement
            
        Returns:
            A condensed version of the problem statement
        """
        # If problem statement is already short, return as is
        if len(problem_statement.split()) < 100:
            return problem_statement
            
        import google.generativeai as genai
        import os
        from dotenv import load_dotenv
        
        try:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return problem_statement
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Condense the following programming assignment problem statement into a concise version.
            Keep all essential requirements, constraints, and input/output specifications.
            Remove unnecessary explanations, redundancies, and verbose descriptions.
            Focus on what the program needs to do, not how to do it.
            The result should be 30-50% shorter than the original.
            
            PROBLEM STATEMENT:
            {problem_statement}
            """
            
            response = model.generate_content(prompt)
            condensed = response.text.strip()
            
            # If the condensed version is too short or empty, return original
            if len(condensed) < 30 or len(condensed) / len(problem_statement) < 0.15:
                return problem_statement
                
            return condensed
            
        except Exception as e:
            print(f"Error condensing problem statement: {str(e)}")
            return problem_statement
    
    def generate_upload_markdown(self):
        """Generate markdown for the upload PDF.
        
        Handles both single program case and multiple program case.
        For single program:
            - code is a single string
            - outputs is a list of strings (one per test case)
        For multiple programs:
            - code is a list of strings [code1, code2, ...]
            - outputs is a nested list [[test1_1, test1_2], [test2_1, test2_2], ...]
        """
        # Common header for both cases
        markdown = f"""# Assignment {self.assignment_number}

## Student Details
- **Name:** {self.student_name}
- **PRN:** {self.student_prn}
- **Batch:** {self.student_batch}

## Problem Statement

```
{self.problem_statement}
```

"""
        
        # Check if we have multiple programs or a single one
        if isinstance(self.code, list):
            # Multiple programs case
            for program_idx, (program_code, program_outputs) in enumerate(zip(self.code, self.outputs), 1):
                # Add program header and code
                markdown += f"""
## Program {program_idx}
```{self.assignment_type}
{program_code}
```

### Program {program_idx} Output
"""
                # Add test cases for this program
                for test_idx, test_output in enumerate(program_outputs, 1):
                    markdown += f"""
#### Test Case {test_idx}
```
{test_output}
```
"""
        else:
            # Single program case - original implementation
            markdown += f"""
## Code
```{self.assignment_type}
{self.code}
```

## Output
"""
            for i, output in enumerate(self.outputs, 1):
                markdown += f"""
### Test Case {i}
```
{output}
```
"""
        
        return markdown
    
    def save_markdown_to_file(self, filename):
        """Save the generated markdown to a file."""
        markdown = self.generate_upload_markdown()
        with open(filename, "w", encoding="utf-8") as f:  # Add encoding parameter
            f.write(markdown)
        return filename