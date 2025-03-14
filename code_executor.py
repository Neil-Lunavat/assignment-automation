import os
import re
import subprocess
import tempfile
import platform

class CodeExecutor:
    def __init__(self, code_content, test_inputs):
        """Initialize with the code content and test inputs."""
        self.code_content = code_content
        self.test_inputs = test_inputs
        self.temp_dir = tempfile.mkdtemp()
        self.output_results = []
    
    def _extract_code_and_inputs(self):
        """Extract Python code and test inputs from the Gemini API response."""
        # Extract Python code
        python_code_pattern = r"```python\s+(.*?)\s+```"
        code_match = re.search(python_code_pattern, self.code_content, re.DOTALL)
        code = code_match.group(1) if code_match else self.code_content
        
        # Extract test inputs
        test_inputs_pattern = r"TEST_START\s+(.*?)\s+TEST_END"
        inputs_match = re.search(test_inputs_pattern, self.test_inputs, re.DOTALL)
        inputs = inputs_match.group(1).strip().split('\n') if inputs_match else []
        
        return code, inputs
    
    def save_code_to_file(self):
        """Save the extracted code to a temporary Python file."""
        code, _ = self._extract_code_and_inputs()
        
        # Save the code to a temporary file
        filename = os.path.join(self.temp_dir, "solution.py")
        with open(filename, "w") as f:
            f.write(code)
        
        return filename
    
    def execute_code(self, cwd):
        """Execute the code with each test input and capture the output."""
        code_file = self.save_code_to_file()
        _, inputs = self._extract_code_and_inputs()
        
        outputs = []
        for input_data in inputs:
            try:
                # Execute the Python file with the input
                process = subprocess.Popen(
                    ["python", code_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=input_data, timeout=10)
                
                if stderr:
                    result = f"{cwd}> python solution.py\n>> {input_data}\n{stderr}"
                else:
                    result = f"{cwd}> python solution.py\n>> {input_data}\n{stdout}"
                
                outputs.append(result)
                
            except subprocess.TimeoutExpired:
                outputs.append(f"{cwd}> python solution.py\n>> {input_data}\nExecution timed out after 10 seconds")
            except Exception as e:
                outputs.append(f"{cwd}> python solution.py\n>> {input_data}\nError: {str(e)}")
        
        self.output_results = outputs
        return outputs
    
    def get_code_content(self):
        """Return the extracted Python code."""
        code, _ = self._extract_code_and_inputs()
        return code
