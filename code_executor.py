import os
import re
import subprocess
import tempfile
import platform
from typing import List, Tuple, Dict, Union, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import the enhanced execution result class
from output_formatter import EnhancedExecutionResult

class LanguageType(Enum):
    """Enum for supported programming languages."""
    PYTHON = "python"
    CPP = "cpp"
    C = "c"
    
    @classmethod
    def from_string(cls, value: str) -> "LanguageType":
        """Convert string to enum value safely."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.PYTHON  # Default to Python

@dataclass
class TestCase:
    """Data class to represent a test case."""
    inputs: str
    requires_file: bool = False
    file_path: Optional[str] = None

@dataclass
class ProgramInfo:
    """Data class to represent a program with its test cases."""
    code: str
    test_cases: List[TestCase]
    language: LanguageType

class CodeParser:
    """Parser for extracting code and test inputs from Gemini API response."""
    
    @staticmethod
    def extract_code_and_inputs(content: str, language_type: str) -> List[ProgramInfo]:
        """Extract multiple codes and test inputs from the Gemini API response.
        
        Args:
            content: The full response from Gemini API
            language_type: The programming language (python, cpp, c)
            
        Returns:
            List of ProgramInfo objects containing code and test cases
        """
        language = LanguageType.from_string(language_type)
        
        # Extract all code blocks
        code_pattern = f"```{language.value}\\s+(.*?)\\s+```"
        code_blocks = re.findall(code_pattern, content, re.DOTALL)
        
        # Extract all test input blocks
        test_pattern = r"TEST_START\s+(.*?)\s+TEST_END"
        test_blocks = re.findall(test_pattern, content, re.DOTALL)
        
        # Extract file handling flags
        file_pattern = r"FILE_REQUIRED\s+(.*?)\s+FILE_END"
        file_blocks = re.findall(file_pattern, content, re.DOTALL)
        
        # If no code blocks found, try to extract the whole content
        if not code_blocks:
            code_blocks = [content.strip()]
        
        # Process test blocks to get individual test cases
        input_blocks = []
        for block in test_blocks:
            # Split by newlines and remove empty lines
            test_cases = [line.strip() for line in block.strip().split('\n') if line.strip()]
            # Limit to exactly 2 test cases per program
            input_blocks.append(test_cases[:2])
        
        # If no test blocks found, create empty test case
        if not input_blocks:
            input_blocks = [["", ""]]  # Two empty test cases
        
        # Ensure we have enough test cases for each code block
        if len(code_blocks) > len(input_blocks):
            last_input = input_blocks[-1] if input_blocks else ["", ""]
            input_blocks.extend([last_input] * (len(code_blocks) - len(input_blocks)))
        elif len(input_blocks) > len(code_blocks):
            input_blocks = input_blocks[:len(code_blocks)]
        
        # Process file requirements
        file_required = [False] * len(code_blocks)
        if file_blocks:
            for i, file_block in enumerate(file_blocks):
                if i < len(file_required):
                    file_required[i] = True
        
        # Create ProgramInfo objects
        programs = []
        for i, (code, inputs) in enumerate(zip(code_blocks, input_blocks)):
            test_cases = []
            for input_data in inputs:
                requires_file = i < len(file_required) and file_required[i]
                test_cases.append(TestCase(inputs=input_data, requires_file=requires_file))
            
            programs.append(ProgramInfo(
                code=code.strip(),
                test_cases=test_cases,
                language=language
            ))
        
        return programs

class CodeRunner:
    """Runs code in various programming languages."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize with an optional temp directory."""
        self.temp_dir = temp_dir or tempfile.mkdtemp()
    
    def _save_code_to_file(self, code: str, filename: str) -> str:
        """Save code to a file.
        
        Args:
            code: The source code
            filename: The filename to save to
            
        Returns:
            The full path to the saved file
        """
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, "w") as f:
            f.write(code)
        return file_path
    
    def _run_process(self, 
                    command: List[str], 
                    input_data: str, 
                    timeout: int = 10) -> EnhancedExecutionResult:
        """Run a subprocess with the given command and input.
        
        Args:
            command: The command to run as a list
            input_data: Input data to feed to the process
            timeout: Maximum execution time in seconds
            
        Returns:
            EnhancedExecutionResult object with the results
        """
        cmd_str = " ".join(command)
        
        try:
            # Process pipe-separated inputs
            inputs = input_data.split('|')
            combined_input = '\n'.join(inputs)
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.temp_dir  # Set the working directory to temp_dir
            )
            
            stdout, stderr = process.communicate(input=combined_input, timeout=timeout)
            return EnhancedExecutionResult(command=cmd_str, stdout=stdout.strip(), stderr=stderr.strip())
            
        except subprocess.TimeoutExpired:
            return EnhancedExecutionResult(command=cmd_str, stdout="", timed_out=True)
        except Exception as e:
            return EnhancedExecutionResult(command=cmd_str, stdout="", error=str(e))
    
    def run_python(self, 
                   code: str, 
                   test_case: TestCase, 
                   filename: str = "solution.py") -> EnhancedExecutionResult:
        """Run Python code with the given input.
        
        Args:
            code: The Python code to run
            test_case: The test case to use
            filename: The filename to save the code to
            
        Returns:
            EnhancedExecutionResult with the execution results
        """
        file_path = self._save_code_to_file(code, filename)
        
        # If file handling is required, ensure file path is set
        if test_case.requires_file and test_case.file_path:
            # Always use data.txt as the standardized name - simply copy to temp_dir
            # Don't change the name - just copy the file
            with open(test_case.file_path, 'rb') as src:
                file_content = src.read()
            
            # Write to data.txt in the same directory as the code
            dest_path = os.path.join(self.temp_dir, "data.txt")
            with open(dest_path, 'wb') as dst:
                dst.write(file_content)
                
            print(f"Copied test file to {dest_path}")
        
        # Run the code
        command = ["python", filename]  # Use relative path since we set cwd
        return self._run_process(command, test_case.inputs)
    
    def run_cpp(self, 
                code: str, 
                test_case: TestCase, 
                filename: str = "solution.cpp") -> Tuple[EnhancedExecutionResult, Optional[EnhancedExecutionResult]]:
        """Run C/C++ code with the given input.
        
        Args:
            code: The C/C++ code to run
            test_case: The test case to use
            filename: The filename to save the code to
            
        Returns:
            Tuple of (compilation result, execution result)
        """
        file_path = self._save_code_to_file(code, filename)
        
        # Determine executable name
        exe_name = os.path.splitext(filename)[0]
        if platform.system() == "Windows":
            exe_name += ".exe"
        
        exe_path = os.path.join(self.temp_dir, exe_name)
        
        # If file handling is required, ensure file path is set
        if test_case.requires_file and test_case.file_path:
            # Always use data.txt as the standardized name in the same directory
            with open(test_case.file_path, 'rb') as src:
                file_content = src.read()
            
            dest_path = os.path.join(self.temp_dir, "data.txt")
            with open(dest_path, 'wb') as dst:
                dst.write(file_content)
                
            print(f"Copied test file to {dest_path}")
        
        # Compile the code
        compile_command = ["g++", file_path, "-o", exe_path]
        compile_result = self._run_process(compile_command, "")
        
        # If compilation failed, return only the compilation result
        if compile_result.stderr or compile_result.error:
            return compile_result, None
        
        # Run the executable
        run_command = [exe_path] if platform.system() == "Windows" else [f"./{exe_name}"]
        
        run_result = self._run_process(run_command, test_case.inputs)
        
        # For C++, we need to combine compilation and execution
        if run_result.error or run_result.stderr:
            # If execution failed, format the error but still include compilation info
            combined_result = EnhancedExecutionResult(
                command=run_command[0],
                stdout="",
                stderr=f"Compilation successful but execution failed: {run_result.error or run_result.stderr}",
                error=run_result.error
            )
            return None, combined_result
        
        return compile_result, run_result

class CodeExecutor:
    """Main class to execute code and manage results."""
    
    def __init__(self, code_content: str, assignment_type: str, temp_dir: str = None):
        """Initialize with the code content and assignment type.
        
        Args:
            code_content: The full response from Gemini API
            assignment_type: The programming language (python, cpp, c)
            temp_dir: Optional temporary directory to use
        """
        self.code_content = code_content
        self.assignment_type = assignment_type
        self.programs = CodeParser.extract_code_and_inputs(code_content, assignment_type)
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.runner = CodeRunner(self.temp_dir)
    
    def execute_code(self, 
                     working_dir: str, 
                     file_paths: Optional[List[str]] = None) -> Tuple[List[str], List[List[str]]]:
        """Execute all programs with their test cases.
        
        Args:
            working_dir: The current working directory (for display)
            file_paths: Optional list of file paths for file handling test cases
            
        Returns:
            Tuple of (code list, output list for all programs)
        """
        all_codes = []
        all_outputs = []
        
        # Add file paths to test cases if provided
        if file_paths:
            file_idx = 0
            for program in self.programs:
                for test_case in program.test_cases:
                    if test_case.requires_file and file_idx < len(file_paths):
                        test_case.file_path = file_paths[file_idx]
                        file_idx += 1
        
        # Execute each program
        for i, program in enumerate(self.programs):
            program_outputs = []
            all_codes.append(program.code)
            
            for j, test_case in enumerate(program.test_cases):
                filename = f"solution_{i}.{program.language.value}"
                
                if program.language == LanguageType.PYTHON:
                    result = self.runner.run_python(program.code, test_case, filename)
                    program_outputs.append(result.format_output(working_dir, test_case.inputs))
                    
                elif program.language in [LanguageType.CPP, LanguageType.C]:
                    compile_result, run_result = self.runner.run_cpp(program.code, test_case, filename)
                    
                    if run_result:
                        # Only show the execution output without compilation details
                        program_outputs.append(run_result.format_output(working_dir, test_case.inputs))
                    else:
                        # Compilation error
                        program_outputs.append(f"Compilation Error: {compile_result.stderr}")
            
            all_outputs.append(program_outputs)
        
        return all_codes, all_outputs