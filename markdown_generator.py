class MarkdownGenerator:
    def __init__(self, assignment_number, student_name, student_prn, student_batch, problem_statement, code, outputs):
        """Initialize with all necessary content for generating markdown."""
        self.assignment_number = assignment_number
        self.student_name = student_name
        self.student_prn = student_prn
        self.student_batch = student_batch
        self.problem_statement = problem_statement
        self.code = code
        self.outputs = outputs
    
    def generate_upload_markdown(self):
        """Generate markdown for the upload PDF."""
        markdown = f"""# Assignment {self.assignment_number}

## Student Details
- **Name:** {self.student_name}
- **PRN:** {self.student_prn}
- **Batch:** {self.student_batch}

## Problem Statement
{self.problem_statement}

## Code
```python
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
        with open(filename, "w") as f:
            f.write(markdown)
        return filename


class WriteupFormatter:
    def __init__(self, writeup_content):
        """Initialize with the writeup content from Gemini API."""
        self.writeup_content = writeup_content
    
    def format_content(self):
        """Format the writeup content ensuring proper markdown structure."""
        # This is a simple formatter that could be expanded for more complex formatting
        # Currently, we assume the content from Gemini is already well-formatted markdown
        return self.writeup_content
    
    def save_writeup_to_file(self, filename):
        """Save the formatted writeup to a file."""
        content = self.format_content()
        with open(filename, "w") as f:
            f.write(content)
        return filename