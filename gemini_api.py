import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Union, Tuple

load_dotenv()

class GeminiAPI:
    """Class to interact with the Gemini API for code and writeup generation."""
    
    def __init__(self):
        """Initialize the Gemini API with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        
    def _sanitize_text(self, text: str) -> str:
        """Replace problematic Unicode characters with ASCII equivalents.
        
        Args:
            text: The text to sanitize
            
        Returns:
            Sanitized text with problematic characters replaced
        """
        # Map of problematic Unicode characters to safe ASCII replacements
        replacements = {
            '\u25cf': '*',  # Black circle bullet point
            '\u2022': '*',  # Bullet point
            '\u2023': '-',  # Triangular bullet
            '\u2043': '-',  # Hyphen bullet
            '\u2219': '*',  # Bullet operator
            '\u25cb': 'o',  # White circle
            '\u25aa': '-',  # Black small square
            '\u25ab': '-',  # White small square
            '\u25a0': '■',  # Black square
            '\u25a1': '□',  # White square
            # Add more as needed
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def check_file_handling_required(self, problem_statement: str) -> bool:
        """Check if the problem requires file handling.
        
        Args:
            problem_statement: The problem statement to analyze
            
        Returns:
            Boolean indicating if file handling is required
        """
        prompt = f"""
        Analyze this programming problem statement and determine if it requires file handling.
        File handling means the program needs to read from or write to files.
        
        Respond with ONLY 'yes' if file handling is required or 'no' if it's not.
        
        Problem statement:
        {problem_statement}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip().lower()
            return "yes" in result
        except Exception as e:
            print(f"Error checking file handling: {str(e)}")
            return False
    
    def validate_programming_assignment(self, content: str) -> bool:
        """Validate if the content is a programming assignment.
        
        Args:
            content: The content to validate
            
        Returns:
            Boolean indicating if the content is a valid programming assignment
        """
        prompt = f"""
        Determine if the following text describes a programming assignment or problem statement 
        that can be solved with code (in any programming language).
        
        Respond with ONLY 'yes' if it is a programming assignment/problem or 'no' if it's not.
        
        Text to analyze:
        {content}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip().lower()
            return "yes" in result
        except Exception as e:
            print(f"Error validating assignment: {str(e)}")
            return False
    
    def generate_code_and_outputs(self, problem_statement: str, assignment_type: str, requires_file_handling: bool = False) -> str:
        """Generate code solution and terminal outputs based on the problem statement.
        
        Args:
            problem_statement: The problem statement to solve
            assignment_type: The programming language to use (python, cpp, c)
            requires_file_handling: Whether the problem requires file handling
            
        Returns:
            Generated response with code and simulated outputs
        """
        # Parse problem statement to identify multiple subproblems
        subproblems = self._extract_subproblems(problem_statement)
        
        if not subproblems:
            # If no subproblems are identified, treat the entire statement as one problem
            return self._generate_code_with_outputs(problem_statement, assignment_type, requires_file_handling)
        else:
            # Generate code for each subproblem and combine the results
            all_responses = []
            for i, subproblem in enumerate(subproblems):
                response = self._generate_code_with_outputs(
                    subproblem, 
                    assignment_type, 
                    requires_file_handling,
                    subproblem_number=i+1
                )
                all_responses.append(response)
            
            combined_response = "\n\n".join(all_responses)
            return combined_response
    
    def _extract_subproblems(self, problem_statement: str) -> List[str]:
        """Extract multiple subproblems from a problem statement.
        
        Args:
            problem_statement: The complete problem statement
            
        Returns:
            List of individual subproblems, or empty list if no clear division
        """
        prompt = f"""
        Analyze this programming problem statement and determine if it contains multiple separate programming problems.
        If it contains multiple problems, extract each one and format them as:
        
        ```json
        {{
            "has_multiple_problems": true,
            "problems": [
                "First problem statement...",
                "Second problem statement...",
                "..."
            ]
        }}
        ```
        
        If it's a single problem, respond with:
        ```json
        {{
            "has_multiple_problems": false,
            "problems": []
        }}
        ```
        
        Problem statement:
        {problem_statement}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract the JSON part
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                import json
                parsed_data = json.loads(json_match.group(1))
                
                if parsed_data.get("has_multiple_problems", False):
                    return parsed_data.get("problems", [])
            
            return []
                
        except Exception as e:
            print(f"Error extracting subproblems: {str(e)}")
            return []
    
    def _generate_code_with_outputs(self, 
                                   problem_statement: str, 
                                   assignment_type: str, 
                                   requires_file_handling: bool = False,
                                   subproblem_number: Optional[int] = None) -> str:
        """Generate code and simulated terminal outputs for a single problem statement.
        
        Args:
            problem_statement: The problem statement to solve
            assignment_type: The programming language to use
            requires_file_handling: Whether the problem requires file handling
            subproblem_number: Optional number if this is part of multiple subproblems
            
        Returns:
            Generated response with code and simulated outputs in a specific format
        """
        subproblem_prefix = f"Subproblem {subproblem_number}: " if subproblem_number is not None else ""
        
        file_handling_instructions = ""
        if requires_file_handling:
            file_handling_instructions = """
            This problem requires file handling. Your solution should:
            1. Read from a file named EXACTLY "data.txt" 
            2. Process the data from the file according to the problem statement
            3. Output the results according to the problem statement
            
            In your terminal simulation:
            - Assume the file exists in the same directory
            - Show realistic outputs as if the file were read successfully
            - Create realistic sample data that would be in the file based on the problem
            """
        
        prompt = f"""
        You are an automated programming assignment solution generator for a FIRST-YEAR UNDERGRADUATE STUDENT with minimal programming experience. Generate a solution for the following {assignment_type} programming assignment problem.
        
        PROBLEM STATEMENT:
        {subproblem_prefix}{problem_statement}

        Your solution must follow these EXTREMELY STRICT requirements for a TRUE BEGINNER-LEVEL solution:

        1. **ABSOLUTE FIRST-YEAR CODE ONLY**: 
           - Write code as if by a student who just learned programming a few weeks ago
           - Use very simple variable names (a, b, arr, num1, num2, i, j, temp, etc.)
           - Add basic comments that explain obvious things
           - Include inefficiencies that a beginner would make

        2. **EXTREME SIMPLICITY IS MANDATORY**:
           - For Python: NO imports except maybe 'math' if absolutely necessary
           - For C++: ONLY use stdio.h/iostream, NO STL whatsoever - NO vector, NO algorithm, NO string, NO namespace std
           - For C: Only use stdio.h and perhaps stdlib.h if absolutely necessary
           - NO try/except or error handling of any kind
           - NO functions when possible (or only 1-2 very simple ones)
           - NO classes or object-oriented features
           - NO if __name__ == "__main__" structures

        3. **IMPLEMENT EVERYTHING FROM SCRATCH**:
           - Write sorting algorithms manually (bubble or selection sort ONLY)
           - Implement all string manipulation manually with loops and arrays
           - For C++, use C-style code (arrays, printf/scanf) rather than C++ features
           - Use basic loops and conditionals for everything

        4. **ADD BEGINNER CHARACTERISTICS**:
           - Include a few inefficient approaches (like nested loops where unnecessary)
           - Add slightly redundant code
           - Use simple algorithms even when better ones exist
           - Include a few extra variables
           - Write overly detailed comments on simple operations
           {file_handling_instructions}

        5. **TERMINAL SIMULATION**: 
           - Create a realistic terminal/command line simulation showing the program running
           - Show TWO complete test runs with different inputs and outputs
           - Format exactly like a real terminal session with prompts, inputs, and outputs
           - Make the terminal path be C:\\Users\\Student\\Desktop\\programs> python solution.py
           - For each test case, show the command being run, all program outputs, user inputs, and final results
           - USE ONLY ASCII CHARACTERS in your terminal output - no Unicode bullets or special symbols

        Your response MUST follow this exact structure and format:

        ```{assignment_type}
        [Your complete beginner-level code solution here]
        ```

        ```
        TEST_START
        [First terminal simulation showing the program running with test inputs and outputs]
        
        [Second terminal simulation showing the program running with different test inputs and outputs]
        TEST_END
        ```

        Do not include any explanations or text outside of these code and test blocks.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Sanitize the response to replace any problematic Unicode characters
            sanitized_response = self._sanitize_text(response.text)
            return sanitized_response
        except Exception as e:
            print(f"Error generating code and outputs: {str(e)}")
            fallback = f"""
            ```{assignment_type}
            # Error generating code
            print("An error occurred during code generation")
            ```
            
            ```
            TEST_START
            C:\\Users\\Student\\Desktop\\programs> python solution.py
            An error occurred during code generation
            
            C:\\Users\\Student\\Desktop\\programs> python solution.py
            An error occurred during code generation
            TEST_END
            ```
            """
            return fallback
    
    def generate_writeup(self, 
                        theory_points: List[str], 
                        code_response: str, 
                        assignment_number: str = "", 
                        problem_statement: str = "", 
                        assignment_type: str = "python") -> str:
        """Generate a theoretical writeup based on the provided theory points.
        
        Args:
            theory_points: List of theory points to include in the writeup
            code_response: The generated code solution
            assignment_number: The assignment number
            problem_statement: The problem statement
            assignment_type: The programming language
            
        Returns:
            Generated theoretical writeup
        """
        if not theory_points:
            return """
            ```markdown
            ## No write up required for this assignment.
            ```
            """
            
        theory = "\n".join([f"- {point}" for point in theory_points])
        
        # Extract just the code part from code_response (removing terminal outputs)
        code_pattern = f"```{assignment_type}\\s+(.*?)\\s+```"
        code_match = re.search(code_pattern, code_response, re.DOTALL)
        code_extract = code_match.group(1) if code_match else code_response
        
        prompt = f"""
        Create a comprehensive write-up for this {assignment_type} Assignment using this format:
        
        ```markdown
        # Assignment No {assignment_number}

        ## Title: 
        [Extract from the problem statement]

        ## Problem Statement: 
        {problem_statement}

        ## Objective: 
        [Extrapolate from theory and problem statement]

        ## Theory:

        For each of these theory topics:
        {theory}
        
        Create detailed sections with the following characteristics:
        
        1. Start each section with a heading of the point (e.g., "### How to generate Fibonacci series")
        2. Provide a clear conceptual explanation with examples and mathematical calculations where relevant
        3. Include fundamental understanding, followed by deeper insights
        4. For programming concepts, include practical examples with code snippets
        5. Explain mathematical properties and formulas where applicable
        7. Cover optimization techniques and best practices
        
        IMPORTANT: Use only ASCII characters in your explanations. Do not use Unicode bullet points or special symbols.
        Use standard markdown formatting:
        - Use asterisks (*) for bullet points
        - Use hyphens (-) for lists
        - Use 1. 2. 3. for numbered lists
        
        ## Algorithm:
        Provide a step-by-step algorithm that matches the following program(s):
        {code_extract}
        
        ## Conclusion:
        Summarize and write a conclusion on what was learned from implementing this assignment.
        Keep it concise and formal, only upto a paragraph.
        ```

        Strictly follow this format and only output the markdown, nothing else.
        Ensure there is NO extra text, no introductory phrases.
        The write-up should be basic to intermediate level up to a first year B.Tech. Student's level, and formatted as stated.
        Ensure it's detailed enough for 4-5 pages with information that's not too dense.
        """
        
        response = self.model.generate_content(prompt)
        # Sanitize the response to replace any problematic Unicode characters
        sanitized_response = self._sanitize_text(response.text)
        return sanitized_response