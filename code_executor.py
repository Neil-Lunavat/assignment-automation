import re
import os
from typing import List, Tuple, Dict, Union, Optional, Any
from dataclasses import dataclass
from enum import Enum

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
class SimulatedTestCase:
    """Data class to represent a simulated test case output."""
    terminal_output: str

@dataclass
class ProgramInfo:
    """Data class to represent a program with its test cases."""
    code: str
    test_cases: List[SimulatedTestCase]
    language: LanguageType

class CodeParser:
    """Parser for extracting code and terminal outputs from Gemini API response."""
    
    @staticmethod
    def extract_code_and_outputs(content: str, language_type: str) -> List[ProgramInfo]:
        """Extract code and terminal outputs from the Gemini API response.
        
        Args:
            content: The full response from Gemini API
            language_type: The programming language (python, cpp, c)
            
        Returns:
            List of ProgramInfo objects containing code and simulated test cases
        """
        language = LanguageType.from_string(language_type)
        programs = []
        
        # Check if we have multiple subproblems
        subproblem_sections = re.split(r'Subproblem \d+:', content)
        
        if len(subproblem_sections) > 1:
            # Process each subproblem section individually
            for i, section in enumerate(subproblem_sections[1:], 1):
                program_info = CodeParser._parse_single_program_section(section, language, f"Subproblem {i}")
                if program_info:
                    programs.append(program_info)
        else:
            # Process as a single program
            program_info = CodeParser._parse_single_program_section(content, language)
            if program_info:
                programs.append(program_info)
        
        return programs
    
    @staticmethod
    def _parse_single_program_section(content: str, language: LanguageType, prefix: str = "") -> Optional[ProgramInfo]:
        """Parse a single program section from the content.
        
        Args:
            content: The section content to parse
            language: The programming language
            prefix: Optional prefix for the code (e.g., "Subproblem 1")
            
        Returns:
            ProgramInfo object or None if parsing failed
        """
        # Extract code block
        code_pattern = f"```{language.value}\\s+(.*?)\\s+```"
        code_match = re.search(code_pattern, content, re.DOTALL)
        
        if not code_match:
            # Try with just the language name (without specifying the language in the regex)
            code_pattern = r"```(?:[a-z]+)?\s+(.*?)\s+```"
            code_match = re.search(code_pattern, content, re.DOTALL)
            
            if not code_match:
                return None
        
        code = code_match.group(1).strip()
        
        # Add prefix to code if provided
        if prefix:
            code = f"# {prefix}\n{code}"
        
        # Extract terminal outputs
        test_pattern = r"TEST_START\s+(.*?)\s+TEST_END"
        test_match = re.search(test_pattern, content, re.DOTALL)
        
        test_cases = []
        if test_match:
            # Split the test content by blank lines to get individual test cases
            test_content = test_match.group(1)
            test_sessions = re.split(r'\n\s*\n', test_content)
            
            # Create a test case for each terminal session
            for session in test_sessions:
                if session.strip():
                    test_cases.append(SimulatedTestCase(terminal_output=session.strip()))
        
        if not test_cases:
            # Create a fallback test case if none were found
            fallback_output = f"C:\\Users\\Student\\Desktop\\programs> python solution.py\nNo output available for this program."
            test_cases.append(SimulatedTestCase(terminal_output=fallback_output))
        
        return ProgramInfo(code=code, test_cases=test_cases, language=language)

class CodeExecutor:
    """Main class to parse and format AI-generated code and outputs."""
    
    def __init__(self, code_content: str, assignment_type: str, temp_dir: str = None):
        """Initialize with the code content and assignment type.
        
        Args:
            code_content: The full response from Gemini API
            assignment_type: The programming language (python, cpp, c)
            temp_dir: Optional temporary directory for test files
        """
        self.code_content = code_content
        self.assignment_type = assignment_type
        self.programs = CodeParser.extract_code_and_outputs(code_content, assignment_type)
        self.temp_dir = temp_dir
    
    def _read_test_file_contents(self, file_paths: List[str]) -> Dict[str, str]:
        """Read the contents of test files.
        
        Args:
            file_paths: List of file paths to read
            
        Returns:
            Dictionary mapping filenames to file contents
        """
        file_contents = {}
        
        if not file_paths:
            return file_contents
            
        for file_path in file_paths:
            try:
                filename = os.path.basename(file_path)
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                file_contents[filename] = content
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
                # Add placeholder content for failed reads
                file_contents[os.path.basename(file_path)] = f"[Error reading file: {str(e)}]"
                
        return file_contents
    
    def generate_realistic_outputs(self, 
                                  program_code: str, 
                                  file_contents: Dict[str, str], 
                                  working_dir: str) -> List[str]:
        """Generate realistic outputs for a program based on actual file contents.
        
        Args:
            program_code: The code to execute
            file_contents: Dictionary of file contents
            working_dir: Working directory path
            
        Returns:
            List of terminal outputs for test cases
        """
        import google.generativeai as genai
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Initialize Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fall back to default simulated outputs if no API key
            return ["Error: GEMINI_API_KEY is not set in the environment"]
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')  # Use appropriate model
        
        # Prepare file content description for the prompt
        file_descriptions = []
        for filename, content in file_contents.items():
            # Truncate very large files for the prompt
            if len(content) > 1000:
                content_preview = content[:1000] + "... [content truncated]"
            else:
                content_preview = content
                
            file_descriptions.append(f"File: {filename}\nContent:\n{content_preview}")
            
        file_content_text = "\n\n".join(file_descriptions)
        
        # Create prompt for Gemini
        prompt = f"""
        You are simulating the execution of this program with REAL FILE DATA.
        
        PROGRAM CODE:
        ```{self.assignment_type}
        {program_code}
        ```
        
        FILES AVAILABLE:
        {file_content_text}
        
        Based on the program code and the REAL file contents above, simulate EXACTLY what would happen when this program runs.
        Create TWO different realistic terminal sessions showing the program execution.
        
        Format the output EXACTLY like this:
        
        ```
        {working_dir}> python solution.py
        [Program output line 1]
        [Program prompt for input 1]: [User input 1]
        [More output lines...]
        ```
        
        ```
        {working_dir}> python solution.py
        [Different program output lines for second test case]
        [Program prompt for input 2]: [Different user input 2]
        [More output lines...]
        ```
        
        EXTREMELY IMPORTANT GUIDELINES:
        1. The program will read from the EXACT files shown above with EXACTLY the content provided
        2. Show realistic outputs based on processing the actual file contents
        3. Where user input is needed, make up realistic inputs that would work with the program
        4. If the file has CSV or structured data, show realistic processing of that data
        5. Show any errors that would realistically occur if the program tried to process the files
        6. Show ONLY the terminal output, no explanations
        """
        
        try:
            # Call Gemini API
            response = model.generate_content(prompt)
            output_text = response.text
            
            # Extract terminal sessions
            terminal_sessions = []
            session_pattern = r"```\s*(.*?)\s*```"
            
            for match in re.finditer(session_pattern, output_text, re.DOTALL):
                terminal_sessions.append(match.group(1).strip())
                
            # If no sessions found, create a fallback
            if not terminal_sessions:
                fallback_output = f"{working_dir}> python solution.py\nError: Could not generate realistic output"
                terminal_sessions.append(fallback_output)
                
            return terminal_sessions
                
        except Exception as e:
            # Return error message as a terminal session
            error_output = f"{working_dir}> python solution.py\nError generating output: {str(e)}"
            return [error_output]
    
    def execute_code(self, 
                     working_dir: str, 
                     file_paths: Optional[List[str]] = None) -> Tuple[Union[str, List[str]], Union[List[str], List[List[str]]]]:
        """Process AI-generated code and outputs.
        
        Args:
            working_dir: Working directory path
            file_paths: Optional list of file paths for test files
            
        Returns:
            Tuple of (code list, output list for all programs)
        """
        # Format the working directory for display
        formatted_working_dir = working_dir.replace("\\", "\\\\") if working_dir else "C:\\Users\\Student\\Desktop\\programs"
        
        # Read test file contents if provided
        file_contents = {}
        if file_paths:
            file_contents = self._read_test_file_contents(file_paths)
        
        all_codes = []
        all_outputs = []
        
        for program in self.programs:
            program_code = program.code
            all_codes.append(program_code)
            
            # If we have test files, generate realistic outputs based on them
            if file_contents:
                realistic_outputs = self.generate_realistic_outputs(
                    program_code, 
                    file_contents, 
                    formatted_working_dir
                )
                all_outputs.append(realistic_outputs)
            else:
                # Otherwise use the simulated outputs from Gemini's initial response
                program_outputs = []
                for test_case in program.test_cases:
                    # Replace the default path with the user's working directory if needed
                    terminal_output = test_case.terminal_output
                    if formatted_working_dir != "C:\\Users\\Student\\Desktop\\programs":
                        terminal_output = terminal_output.replace(
                            "C:\\Users\\Student\\Desktop\\programs",
                            formatted_working_dir
                        )
                    program_outputs.append(terminal_output)
                all_outputs.append(program_outputs)
        
        # Handle the case of no programs
        if not all_codes:
            all_codes = ["# No valid code could be extracted"]
            all_outputs = [["No valid output could be generated"]]
        
        # Handle the case of a single program (to match the expected interface)
        if len(all_codes) == 1:
            return all_codes[0], all_outputs[0]
        
        return all_codes, all_outputs