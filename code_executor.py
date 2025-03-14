import os
import re
import subprocess
import tempfile
import platform

class CodeExecutor:
    def __init__(self, code_content):
        """Initialize with the code content and test inputs."""
        self.code, self.test_inputs = self._extract_code_and_inputs(code_content)
        self.temp_dir = tempfile.mkdtemp()
    
    def _extract_code_and_inputs(self, code_content):
        """Extract Python code and test inputs from the Gemini API response."""
        # Extract Python code
        python_code_pattern = r"```python\s+(.*?)\s+```"
        code_match = re.search(python_code_pattern, code_content, re.DOTALL)
        code = code_match.group(1) if code_match else code_content
        
        # Extract test inputs
        test_inputs_pattern = r"TEST_START\s+(.*?)\s+TEST_END"
        inputs_match = re.search(test_inputs_pattern, code_content, re.DOTALL)
        inputs = inputs_match.group(1).strip().split('\n') if inputs_match else []
        
        return code, inputs
    
    def save_code_to_file(self):
        """Save the extracted code to a temporary Python file."""
        
        # Save the code to a temporary file
        filename = os.path.join(self.temp_dir, "solution.py")
        with open(filename, "w") as f:
            f.write(self.code)
        
        return filename
    
    def execute_code(self, cwd):
        """Execute the code with each test input and capture the output."""
        code_file = self.save_code_to_file()
        
        outputs = []
        for input_data in self.test_inputs:
            try:
                # Create a command line style output header
                result = f"{cwd}> python solution.py\n"
                
                # Execute the Python file with the input
                process = subprocess.Popen(
                    ["python", code_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Split input_data into lines for handling multi-line inputs
                stdin_data = input_data
                
                stdout, stderr = process.communicate(input=stdin_data, timeout=10)
                
                if stderr:
                    # Handle error case
                    result += f"{stderr}"
                else:
                    stdout = stdout.strip('\n').split(': ')
                    input_index = 0
                    for line in stdout:
                        if "Enter" in line:
                            result += line + ": " + input_data + "\n"
                            input_index += 1
                    result += ': '.join(stdout[input_index:])
                
                outputs.append(result)
                
            except subprocess.TimeoutExpired:
                outputs.append(f"{cwd}> python solution.py\nExecution timed out after 10 seconds")
            except Exception as e:
                outputs.append(f"{cwd}> python solution.py\nError: {str(e)}")

        return outputs
    
    def get_code_content(self):
        """Return the extracted Python code."""
        return self.code
