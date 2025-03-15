import os
import re
import subprocess
import tempfile
import platform

class CodeExecutor:
    def __init__(self, code_content, assignment_type):
        """Initialize with the code content and test inputs."""
        self.assignment_type = assignment_type
        self.code, self.test_inputs = self._extract_code_and_inputs(code_content)
        self.temp_dir = tempfile.mkdtemp()
    
    def _extract_code_and_inputs(self, code_content):
        """Extract multiple codes and test inputs from the Gemini API response."""
        # Extract all code blocks with the assignment type
        code_pattern = r"```" + self.assignment_type + r"\s+(.*?)\s+```"
        code_blocks = re.findall(code_pattern, code_content, re.DOTALL)
        codes = [block.strip() for block in code_blocks] if code_blocks else []
        
        # Extract all test input blocks using TEST_START/TEST_END markers
        test_pattern = r"TEST_START\s+(.*?)\s+TEST_END"
        test_blocks = re.findall(test_pattern, code_content, re.DOTALL)
        input_blocks = [block.strip().split('\n\n') for block in test_blocks] if test_blocks else []
        
        # Handle case where no code blocks were found
        if not codes:
            # Fallback to original single code extraction
            code_match = re.search(code_pattern, code_content, re.DOTALL)
            if code_match:
                codes = [code_match.group(1).strip()]
            else:
                codes = [code_content.strip()]
        
        # Handle case where no test input blocks were found
        if not input_blocks:
            # Fallback to original single test input extraction
            test_match = re.search(test_pattern, code_content, re.DOTALL)
            if test_match:
                input_blocks = [test_match.group(1).strip().split('\n')]
            else:
                input_blocks = [[]]
        
        # Ensure codes and input blocks match in number
        if len(codes) > len(input_blocks):
            # If more codes than inputs, duplicate the last input block or add empty ones
            if input_blocks:
                last_input = input_blocks[-1]
                input_blocks.extend([last_input] * (len(codes) - len(input_blocks)))
            else:
                input_blocks = [[]] * len(codes)
        elif len(input_blocks) > len(codes):
            # If more inputs than codes, keep only the first inputs matching the number of codes
            input_blocks = input_blocks[:len(codes)]
        
        # Return a single code string or list of code strings
        if len(codes) == 1:
            return codes[0], input_blocks[0]
        else:
            return codes, input_blocks
    
    def save_code_to_file(self, index=None):
        """Save the extracted code to a temporary file."""
        # Handle both single code case and multiple code cases
        is_multiple = isinstance(self.code, list)
        
        if is_multiple:
            # If index is provided, save that specific code
            if index is not None:
                code = self.code[index]
                filename = os.path.join(self.temp_dir, f"solution_{index}.py")
            else:
                # Save the first code by default
                code = self.code[0]
                filename = os.path.join(self.temp_dir, "solution.py")
        else:
            # Single code case (backward compatibility)
            code = self.code
            filename = os.path.join(self.temp_dir, "solution.py")
        
        with open(filename, "w") as f:
            f.write(code)
        
        return filename
    
    def execute_code(self, cwd, assignment_type):
        """Execute the code with each test input and capture the output."""
        is_multiple = isinstance(self.code, list)
        
        if assignment_type == "python":
            if is_multiple:
                # Handle multiple Python programs
                all_codes = self.code
                all_inputs = self.test_inputs
                all_outputs = []
                
                for i, (code, inputs) in enumerate(zip(all_codes, all_inputs)):
                    code_file = self.save_code_to_file(i)
                    file_name = f"solution_{i}.py"
                    
                    program_outputs = []
                    for input_data in inputs:
                        try:
                            # Create command line style output header
                            result = f"{cwd}> python {file_name}\n"
                            
                            # Execute the Python file with input
                            process = subprocess.Popen(
                                ["python", code_file],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            
                            stdout, stderr = process.communicate(input=input_data, timeout=10)
                            
                            if stderr:
                                # Handle error case
                                result += f"{stderr}"
                            else:
                                input_data = input_data.split('\n')
                                stdout = stdout.strip('\n').split(': ')
                                input_index = 0
                                for line in stdout:
                                    if "Enter" in line:
                                        result += line + ": " + input_data[input_index] + "\n"
                                        input_index += 1
                                result += ': '.join(stdout[input_index:])
                            
                            program_outputs.append(result)
                            
                        except subprocess.TimeoutExpired:
                            program_outputs.append(f"{cwd}> python {file_name}\nExecution timed out after 10 seconds")
                        except Exception as e:
                            program_outputs.append(f"{cwd}> python {file_name}\nError: {str(e)}")
                    
                    all_outputs.append(program_outputs)
                return all_codes, all_outputs
            
            else:
                # Original single program case (for backward compatibility)
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
                        
                        stdout, stderr = process.communicate(input=input_data, timeout=10)
                        
                        if stderr:
                            # Handle error case
                            result += f"{stderr}"
                        else:
                            input_data = input_data.split('\n')
                            stdout = stdout.strip('\n').split(': ')
                            input_index = 0
                            for line in stdout:
                                if "Enter" in line:
                                    result += line + ": " + input_data[input_index] + "\n"
                                    input_index += 1
                            result += ': '.join(stdout[input_index:])
                        
                        outputs.append(result)
                        
                    except subprocess.TimeoutExpired:
                        outputs.append(f"{cwd}> python solution.py\nExecution timed out after 10 seconds")
                    except Exception as e:
                        outputs.append(f"{cwd}> python solution.py\nError: {str(e)}")
                return self.code, outputs
        
        elif assignment_type == "cpp":
            if is_multiple:
                # Handle multiple C++ programs
                all_codes = self.code
                all_inputs = self.test_inputs
                all_outputs = []
                
                for i, (code, inputs) in enumerate(zip(all_codes, all_inputs)):
                    # Save code to file
                    src_file = f"solution_{i}.cpp"
                    src_path = os.path.join(self.temp_dir, src_file)
                    with open(src_path, "w") as f:
                        f.write(code)
                    
                    exe_file = f"solution_{i}.exe"
                    exe_path = os.path.join(self.temp_dir, exe_file)
                    
                    program_outputs = []
                    
                    # Compile the C++ code
                    compile_cmd = f"{cwd}> g++ {src_file} -o {exe_file}\n"
                    compile_process = subprocess.Popen(
                        ["g++", src_path, "-o", exe_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    _, compile_stderr = compile_process.communicate()
                    
                    # Check if compilation was successful
                    if compile_process.returncode != 0:
                        # Compilation error
                        program_outputs.append(compile_cmd + compile_stderr)
                        all_outputs.append(program_outputs)
                        continue  # Skip execution for this program

                    for input_data in inputs:
                        try:
                            # Command to run the compiled program (use ./ on Unix)
                            run_prefix = "./" if platform.system() != "Windows" else ""
                            run_cmd = f"{run_prefix}solution_{i}"
                            
                            result = f"{cwd}> {run_cmd}\n"
                            
                            # Execute the compiled program
                            process = subprocess.Popen(
                                [exe_path],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            
                            # Use input data as stdin
                            stdout, stderr = process.communicate(input=input_data, timeout=10)
                            
                            if stderr:
                                result += f"{stderr}"
                            else:
                                input_data = input_data.split('\n')
                                stdout = stdout.strip('\n').split(': ')
                                input_index = 0
                                for line in stdout:
                                    if "Enter" in line:
                                        result += line + ": " + input_data[input_index] + "\n"
                                        input_index += 1
                                result += ': '.join(stdout[input_index:])
                            # Add compilation command and execution output
                            program_outputs.append(result)
                            
                        except subprocess.TimeoutExpired:
                            program_outputs.append(compile_cmd + f"{cwd}> {run_cmd}\nExecution timed out after 10 seconds")
                        except Exception as e:
                            program_outputs.append(compile_cmd + f"{cwd}> {run_cmd}\nError: {str(e)}")
                    
                    program_outputs[0] = compile_cmd + program_outputs[0]
                    all_outputs.append(program_outputs)
                
                return all_codes, all_outputs
            
            else:
                # Single C++ program
                src_file = "solution.cpp"
                src_path = os.path.join(self.temp_dir, src_file)
                with open(src_path, "w") as f:
                    f.write(self.code)
                
                exe_file = "solution"
                if platform.system() == "Windows":
                    exe_file += ".exe"
                exe_path = os.path.join(self.temp_dir, exe_file)
                
                outputs = []
                
                # Compile the C++ code
                compile_cmd = f"{cwd}> g++ {src_file} -o solution\n"
                compile_process = subprocess.Popen(
                    ["g++", src_path, "-o", exe_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                _, compile_stderr = compile_process.communicate()
                
                # Check if compilation was successful
                if compile_process.returncode != 0:
                    # Compilation error
                    outputs.append(compile_cmd + compile_stderr)
                    return self.code, outputs
                
                for input_data in self.test_inputs:
                    try:
                        # Command to run the compiled program
                        run_prefix = "./" if platform.system() != "Windows" else ""
                        run_cmd = f"{run_prefix}solution"
                        
                        result = f"{cwd}> {run_cmd}\n"
                        
                        # Execute the compiled program
                        process = subprocess.Popen(
                            [exe_path],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        # Use input data as stdin
                        stdout, stderr = process.communicate(input=input_data, timeout=10)
                        
                        if stderr:
                            result += f"{stderr}"
                        else:
                            input_data = input_data.split('\n')
                            stdout = stdout.strip('\n').split(': ')
                            input_index = 0
                            for line in stdout:
                                if "Enter" in line:
                                    result += line + ": " + input_data[input_index] + "\n"
                                    input_index += 1
                            result += ': '.join(stdout[input_index:])
                        # Add compilation command and execution output
                        outputs.append(compile_cmd + result)
                        
                    except subprocess.TimeoutExpired:
                        outputs.append(compile_cmd + f"{cwd}> {run_cmd}\nExecution timed out after 10 seconds")
                    except Exception as e:
                        outputs.append(compile_cmd + f"{cwd}> {run_cmd}\nError: {str(e)}")
                
                return self.code, outputs
        
        # Default case for unsupported assignment types
        return self.code, ["Unsupported assignment type: " + assignment_type]