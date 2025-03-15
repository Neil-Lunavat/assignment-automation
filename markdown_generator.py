class MarkdownGenerator:
    def __init__(self, assignment_number, assignment_type, student_name, student_prn, student_batch, problem_statement, code, outputs):
        """Initialize with all necessary content for generating markdown."""
        self.assignment_number = assignment_number
        self.assignment_type = assignment_type
        self.student_name = student_name
        self.student_prn = student_prn
        self.student_batch = student_batch
        self.problem_statement = problem_statement
        self.code = code
        self.outputs = outputs
    
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
        with open(filename, "w") as f:
            f.write(markdown)
        return filename


class WriteupFormatter:
    def __init__(self, writeup_content):
        """Initialize with the writeup content from Gemini API."""
        self.writeup_content = writeup_content
    
    def format_content(self):
        """Format the writeup content ensuring proper markdown structure."""
        text = self.writeup_content
        start_marker = "```markdown"
        end_marker = "```"
        # Find the index of the first occurrence
        start_index = text.find(start_marker)
        if start_index == -1:
            return text  # No marker found
        
        # Find the last occurrence after our starting point
        end_index = text.rfind(end_marker)
        if end_index == -1:
            return text  # No ending marker found
        
        # Extract the content between markers
        return text[start_index+11:end_index]
    
    def save_writeup_to_file(self, filename):
        """Save the formatted writeup to a file."""
        content = self.format_content()
        with open(filename, "w") as f:
            f.write(content)
        return filename