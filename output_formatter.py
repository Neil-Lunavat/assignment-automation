import os
import re
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

class OutputFormatter:
    """Uses Gemini API to format program execution output to look natural."""
    
    def __init__(self):
        """Initialize with Gemini API key."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def format_execution_output(
        self, 
        working_dir: str, 
        command: str, 
        input_lines: List[str], 
        output_lines: List[str]
    ) -> str:
        """Format execution output using Gemini to create natural-looking interactions.
        
        Args:
            working_dir: The current working directory to display in prompt
            command: The command that was executed (e.g., "python solution_1.py")
            input_lines: List of input strings provided by the user
            output_lines: List of output strings from the program
            
        Returns:
            Formatted string showing a realistic program execution with inputs and outputs
        """
        # Create the prompt for Gemini
        prompt = f"""
        I need you to format the following program execution to look like a realistic command line interaction.

        Working directory: {working_dir}
        Command: {command}
        
        USER INPUTS (in order):
        {self._format_list(input_lines)}
        
        PROGRAM OUTPUTS (raw):
        {self._format_list(output_lines)}
        
        Format this as a realistic command-line interaction where:
        1. Start with the working directory and command
        2. When the program asks for input (lines containing "Enter", "Input", or ending with ":"), show the corresponding user input
        3. Show all program outputs exactly as they appear
        
        The format should be:
        ```
        {working_dir}> {command}
        [Program output line 1]
        [Program prompt for input 1]: [User input 1]
        ```
        
        IMPORTANT: Give me ONLY the formatted execution output, no explanation or additional text.
        Don't give additional examples. ONLY FORMAT WHAT'S PROVIDED IN THE PROMPT.
        """
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            # Extract just the formatted output
            formatted_output = response.text.strip()
            
            # Remove any markdown code blocks if present
            formatted_output = self._clean_response(formatted_output)
            
            return formatted_output
            
        except Exception as e:
            # Fallback to a simple format if Gemini fails
            return self._fallback_format(working_dir, command, input_lines, output_lines)
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for the prompt."""
        return "\n".join([f"- {item}" for item in items])
    
    def _clean_response(self, text: str) -> str:
        """Clean the Gemini response to extract just the formatted output."""
        # Remove markdown code blocks if present
        if text.startswith("```") and text.endswith("```"):
            # Find the first and last occurrence of ```
            start_idx = text.find("```")
            if start_idx != -1:
                # Look for the end of the first line with ```
                newline_idx = text.find("\n", start_idx)
                if newline_idx != -1:
                    start_idx = newline_idx + 1
                else:
                    start_idx = start_idx + 3
            
            end_idx = text.rfind("```")
            if end_idx != -1:
                text = text[start_idx:end_idx].strip()
        
        return text
    
    def _fallback_format(
        self, 
        working_dir: str, 
        command: str, 
        input_lines: List[str], 
        output_lines: List[str]
    ) -> str:
        """Fallback formatter in case Gemini API fails."""
        result = [f"{working_dir}> {command}"]
        
        input_idx = 0
        for line in output_lines:
            if (":" in line and 
                any(prompt in line.lower() for prompt in ["enter", "input", "provide", "type"]) and 
                input_idx < len(input_lines)):
                
                # This looks like an input prompt, append the input
                prompt_parts = line.split(":")
                result.append(f"{prompt_parts[0]}: {input_lines[input_idx]}")
                input_idx += 1
            else:
                # Regular output line
                result.append(line)
        
        return "\n".join(result)


class EnhancedExecutionResult:
    """Enhanced class to store and format execution results."""
    
    def __init__(self, 
                 command: str, 
                 stdout: str, 
                 stderr: str = "", 
                 timed_out: bool = False, 
                 error: str = ""):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.error = error
        self._formatter = OutputFormatter()
    
    def format_output(self, working_dir: str, input_data: str = "") -> str:
        """Format the execution result to look like a natural command-line interaction using Gemini.
        
        Args:
            working_dir: The current working directory
            input_data: The input data that was provided (pipe-separated for multiple inputs)
            
        Returns:
            Formatted output string showing a natural command line interaction
        """
        # Simplify the command display - extract just the solution_X.py part
        command_display = self.command
        
        # Replace the full path with just the simple filename pattern
        if "solution_" in command_display:
            # Extract just the solution_X.py part from the full command
            filename_match = re.search(r'solution_\d+\.\w+', command_display)
            if filename_match:
                simple_filename = filename_match.group(0)
                command_display = f"python {simple_filename}"
        
        # For execution errors or timeouts, show simple error message
        if self.timed_out:
            return f"{working_dir}> {command_display}\nExecution timed out after 10 seconds"
        
        if self.error:
            return f"{working_dir}> {command_display}\nError: {self.error}"
        
        if self.stderr:
            return f"{working_dir}> {command_display}\n{self.stderr}"
        
        # Split the input data by pipe character to get individual inputs
        input_lines = []
        if input_data:
            input_lines = input_data.split('|')
        
        # Split stdout into lines
        output_lines = self.stdout.strip().split('\n')
        
        # Use the formatter to create natural-looking output
        return self._formatter.format_execution_output(
            working_dir=working_dir,
            command=command_display,
            input_lines=input_lines,
            output_lines=output_lines
        )