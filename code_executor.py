import re
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
            temp_dir: Optional temporary directory (not used but kept for API compatibility)
        """
        self.code_content = code_content
        self.assignment_type = assignment_type
        self.programs = CodeParser.extract_code_and_outputs(code_content, assignment_type)
    
    def execute_code(self, 
                     working_dir: str, 
                     file_paths: Optional[List[str]] = None) -> Tuple[List[str], List[List[str]]]:
        """Process AI-generated code and outputs to match the expected interface.
        
        Args:
            working_dir: Working directory (used for display in outputs)
            file_paths: Optional list of file paths (not used but kept for API compatibility)
            
        Returns:
            Tuple of (code list, output list for all programs)
        """
        all_codes = []
        all_outputs = []
        
        # Format the working_dir to match the expected format in the simulated outputs
        formatted_working_dir = working_dir.replace("\\", "\\\\") if working_dir else "C:\\Users\\Student\\Desktop\\programs"
        
        for program in self.programs:
            program_code = program.code
            all_codes.append(program_code)
            
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