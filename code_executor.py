import os
import re
import subprocess
import tempfile
import platform
from typing import Union, List, Tuple, Optional


class CodeExecutor:
    """A class that executes code with test inputs and captures the output."""
    
    def __init__(self, code_content: str, assignment_type: str):
        """Initialize with the code content and test inputs.
        
        Args:
            code_content: The content containing code blocks and test inputs
            assignment_type: The language type ('python', 'cpp', or 'c')
        """
        self.assignment_type = assignment_type.lower()
        self.code, self.test_inputs = self._extract_code_and_inputs(code_content)
        self.temp_dir = tempfile.mkdtemp()
    
    def _extract_code_and_inputs(self, code_content: str) -> Tuple[Union[str, List[str]], List[List[str]]]:
        """Extract code blocks and test inputs from the content.
        
        Args:
            code_content: Text containing code blocks and test inputs
            
        Returns:
            A tuple of (code, test_inputs) where:
            - code is either a single string or a list of code strings
            - test_inputs is a list of lists of input strings
        """
        # Extract all code blocks with the assignment type
        code_pattern = r"```" + self.assignment_type + r"\s+(.*?)\s+```"
        code_blocks = re.findall(code_pattern, code_content, re.DOTALL)
        codes = [block.strip() for block in code_blocks] if code_blocks else []
        
        # Extract all test input blocks
        test_pattern = r"TEST_START\s+(.*?)\s+TEST_END"
        test_blocks = re.findall(test_pattern, code_content, re.DOTALL)
        input_blocks = []
        
        for block in test_blocks:
            # Split by double newline to separate test cases
            inputs = block.strip().split('\n\n')
            input_blocks.append(inputs)
        
        # Handle case where no code blocks were found
        if not codes:
            code_match = re.search(code_pattern, code_content, re.DOTALL)
            codes = [code_match.group(1).strip()] if code_match else [code_content.strip()]
        
        # Handle case where no test input blocks were found
        if not input_blocks:
            test_match = re.search(test_pattern, code_content, re.DOTALL)
            if test_match:
                input_blocks = [test_match.group(1).strip().split('\n\n')]
            else:
                input_blocks = [[]]
        
        # Balance codes and input blocks
        self._balance_codes_and_inputs(codes, input_blocks)
        
        # Return single code string or list of strings
        return (codes[0], input_blocks[0]) if len(codes) == 1 else (codes, input_blocks)
    
    def _balance_codes_and_inputs(self, codes: List[str], input_blocks: List[List[str]]) -> None:
        """Ensure the number of code blocks and input blocks match.
        
        Args:
            codes: List of code strings
            input_blocks: List of lists of test inputs
        """
        if len(codes) > len(input_blocks):
            # If more codes than inputs, duplicate the last input block or add empty ones
            last_input = input_blocks[-1] if input_blocks else []
            input_blocks.extend([last_input] * (len(codes) - len(input_blocks)))
        elif len(input_blocks) > len(codes):
            # If more inputs than codes, keep only the first inputs matching the number of codes
            input_blocks[:] = input_blocks[:len(codes)]
    
    def save_code_to_file(self, index: Optional[int] = None) -> str:
        """Save the extracted code to a temporary file.
        
        Args:
            index: Index of the code to save (if multiple codes)
            
        Returns:
            Path to the saved file
        """
        is_multiple = isinstance(self.code, list)
        
        if is_multiple:
            # For multiple codes
            code_index = index if index is not None else 0
            code = self.code[code_index]
            ext = self._get_file_extension()
            filename = os.path.join(self.temp_dir, f"solution_{code_index}{ext}")
        else:
            # For single code
            code = self.code
            ext = self._get_file_extension()
            filename = os.path.join(self.temp_dir, f"solution{ext}")
        
        with open(filename, "w") as f:
            f.write(code)
        
        return filename
    
    def _get_file_extension(self) -> str:
        """Get the appropriate file extension based on the assignment type.
        
        Returns:
            File extension string including the dot
        """
        extensions = {
            "python": ".py",
            "cpp": ".cpp",
            "c": ".c"
        }
        return extensions.get(self.assignment_type, ".txt")
    
    def _get_compiler_command(self) -> str:
        """Get the appropriate compiler command based on the assignment type.
        
        Returns:
            Compiler command string
        """
        commands = {
            "cpp": "g++",
            "c": "gcc"
        }
        return commands.get(self.assignment_type, "")
    
    def _process_output(self, stdout: str, stderr: str, input_data: str) -> str:
        """Process the output of code execution.
        
        Args:
            stdout: Standard output from process
            stderr: Standard error from process
            input_data: Input data provided to the process
            
        Returns:
            Formatted result string
        """
        if stderr:
            return stderr
        
        # Split inputs and outputs
        input_lines = input_data.split('\n')
        stdout_parts = stdout.strip('\n').split(': ')
        
        result = ""
        input_index = 0
        
        # Match inputs with prompt lines
        for line in stdout_parts:
            if "Enter" in line and input_index < len(input_lines):
                result += line + ": " + input_lines[input_index] + "\n"
                input_index += 1
            
        # Add remaining output
        result += ': '.join(stdout_parts[input_index:])
        return result
    
    def _execute_compiled_code(self, exe_path: str, input_data: str, cwd: str, run_cmd: str) -> str:
        """Execute compiled code (for C and C++).
        
        Args:
            exe_path: Path to the executable
            input_data: Input data to provide
            cwd: Current working directory (for display)
            run_cmd: Command to show in output
            
        Returns:
            Execution result string
        """
        result = f"{cwd}> {run_cmd}\n"
        
        try:
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
            
            result += self._process_output(stdout, stderr, input_data)
            return result
            
        except subprocess.TimeoutExpired:
            return f"{result}Execution timed out after 10 seconds"
        except Exception as e:
            return f"{result}Error: {str(e)}"
    
    def _execute_python_code(self, code_file: str, input_data: str, cwd: str, file_name: str) -> str:
        """Execute Python code.
        
        Args:
            code_file: Path to the Python file
            input_data: Input data to provide
            cwd: Current working directory (for display)
            file_name: Filename to show in output
            
        Returns:
            Execution result string
        """
        result = f"{cwd}> python {file_name}\n"
        
        try:
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
                result += stderr
            else:
                result += self._process_output(stdout, stderr, input_data)
            
            return result
            
        except subprocess.TimeoutExpired:
            return f"{result}Execution timed out after 10 seconds"
        except Exception as e:
            return f"{result}Error: {str(e)}"
    
    def _compile_code(self, src_path: str, exe_path: str, compiler_cmd: str, src_file: str, cwd: str) -> Tuple[bool, str]:
        """Compile C or C++ code.
        
        Args:
            src_path: Path to the source file
            exe_path: Path for the executable output
            compiler_cmd: Compiler command to use
            src_file: Source filename to show in output
            cwd: Current working directory (for display)
            
        Returns:
            Tuple of (success, compile_output)
        """
        exe_name = os.path.basename(exe_path)
        compile_cmd = f"{cwd}> {compiler_cmd} {src_file} -o {exe_name}\n"
        
        compile_process = subprocess.Popen(
            [compiler_cmd, src_path, "-o", exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        _, compile_stderr = compile_process.communicate()
        
        # Check if compilation was successful
        if compile_process.returncode != 0:
            return False, compile_cmd + compile_stderr
        
        return True, compile_cmd
    
    def execute_code(self, cwd: str, assignment_type: str) -> Tuple[Union[str, List[str]], Union[List[str], List[List[str]]]]:
        """Execute the code with each test input and capture the output.
        
        Args:
            cwd: Current working directory (for display)
            assignment_type: The language type ('python', 'cpp', or 'c')
            
        Returns:
            Tuple of (code, outputs) where:
            - code is either a single string or a list of code strings
            - outputs is either a list of output strings or a list of lists of output strings
        """
        is_multiple = isinstance(self.code, list)
        
        if assignment_type == "python":
            return self._execute_python_assignment(cwd, is_multiple)
        elif assignment_type in ["cpp", "c"]:
            return self._execute_compiled_assignment(cwd, is_multiple, assignment_type)
        else:
            # Default case for unsupported assignment types
            return self.code, [f"Unsupported assignment type: {assignment_type}"]
    
    def _execute_python_assignment(self, cwd: str, is_multiple: bool) -> Tuple[Union[str, List[str]], Union[List[str], List[List[str]]]]:
        """Execute Python assignment code.
        
        Args:
            cwd: Current working directory (for display)
            is_multiple: Whether multiple code blocks exist
            
        Returns:
            Tuple of (code, outputs)
        """
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
                    result = self._execute_python_code(code_file, input_data, cwd, file_name)
                    program_outputs.append(result)
                
                all_outputs.append(program_outputs)
            return all_codes, all_outputs
        
        else:
            # Single program case
            code_file = self.save_code_to_file()
            
            outputs = []
            for input_data in self.test_inputs:
                result = self._execute_python_code(code_file, input_data, cwd, "solution.py")
                outputs.append(result)
            
            return self.code, outputs
    
    def _execute_compiled_assignment(self, cwd: str, is_multiple: bool, assignment_type: str) -> Tuple[Union[str, List[str]], Union[List[str], List[List[str]]]]:
        """Execute C or C++ assignment code.
        
        Args:
            cwd: Current working directory (for display)
            is_multiple: Whether multiple code blocks exist
            assignment_type: The language type ('cpp' or 'c')
            
        Returns:
            Tuple of (code, outputs)
        """
        compiler_cmd = self._get_compiler_command()
        file_ext = self._get_file_extension()
        
        if is_multiple:
            # Handle multiple programs
            all_codes = self.code
            all_inputs = self.test_inputs
            all_outputs = []
            
            for i, (code, inputs) in enumerate(zip(all_codes, all_inputs)):
                # Save code to file
                src_file = f"solution_{i}{file_ext}"
                src_path = os.path.join(self.temp_dir, src_file)
                with open(src_path, "w") as f:
                    f.write(code)
                
                exe_file = f"solution_{i}.exe" if platform.system() == "Windows" else f"solution_{i}"
                exe_path = os.path.join(self.temp_dir, exe_file)
                
                program_outputs = []
                
                # Compile the code
                success, compile_output = self._compile_code(src_path, exe_path, compiler_cmd, src_file, cwd)
                
                if not success:
                    # Compilation error
                    program_outputs.append(compile_output)
                    all_outputs.append(program_outputs)
                    continue  # Skip execution for this program

                for input_data in inputs:
                    # Command to run the compiled program (use ./ on Unix)
                    run_prefix = "./" if platform.system() != "Windows" else ""
                    run_cmd = f"{run_prefix}{os.path.basename(exe_path)}"
                    
                    result = self._execute_compiled_code(exe_path, input_data, cwd, run_cmd)
                    # Add compilation command to first output only
                    if len(program_outputs) == 0:
                        result = compile_output + result
                    
                    program_outputs.append(result)
                
                all_outputs.append(program_outputs)
            
            return all_codes, all_outputs
        
        else:
            # Single program
            src_file = f"solution{file_ext}"
            src_path = os.path.join(self.temp_dir, src_file)
            with open(src_path, "w") as f:
                f.write(self.code)
            
            exe_file = "solution.exe" if platform.system() == "Windows" else "solution"
            exe_path = os.path.join(self.temp_dir, exe_file)
            
            outputs = []
            
            # Compile the code
            success, compile_output = self._compile_code(src_path, exe_path, compiler_cmd, src_file, cwd)
            
            if not success:
                # Compilation error
                outputs.append(compile_output)
                return self.code, outputs
            
            for input_data in self.test_inputs:
                # Command to run the compiled program
                run_prefix = "./" if platform.system() != "Windows" else ""
                run_cmd = f"{run_prefix}{os.path.basename(exe_path)}"
                
                result = self._execute_compiled_code(exe_path, input_data, cwd, run_cmd)
                outputs.append(compile_output + result)
            
            return self.code, outputs