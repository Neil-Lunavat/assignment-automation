import os
import re
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
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
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
    
    def generate_code(self, problem_statement: str, assignment_type: str, requires_file_handling: bool = False) -> str:
        """Generate code solution based on the problem statement.
        
        Args:
            problem_statement: The problem statement to solve
            assignment_type: The programming language to use (python, cpp, c)
            requires_file_handling: Whether the problem requires file handling
            
        Returns:
            Generated code solution
        """
        # Parse problem statement to identify multiple subproblems
        subproblems = self._extract_subproblems(problem_statement)
        
        if not subproblems:
            # If no subproblems are identified, treat the entire statement as one problem
            return self._generate_single_code(problem_statement, assignment_type, requires_file_handling)
        else:
            # Generate code for each subproblem and combine the results
            all_code = ""
            for i, subproblem in enumerate(subproblems):
                code = self._generate_single_code(subproblem, assignment_type, requires_file_handling)
                all_code += f"\n\n# Subproblem {i+1}:\n{code}"
            return all_code
    
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
    
    def _generate_single_code(self, problem_statement: str, assignment_type: str, requires_file_handling: bool = False) -> str:
        """Generate code for a single problem statement.
        
        Args:
            problem_statement: The problem statement to solve
            assignment_type: The programming language to use
            requires_file_handling: Whether the problem requires file handling
            
        Returns:
            Generated code solution
        """
        file_handling_instructions = ""
        if requires_file_handling:
            file_handling_instructions = """
            This problem requires file handling. Your solution should:
            1. Read from a file named EXACTLY "data.txt"
            2. Process the data from the file according to the problem statement
            3. Output the results according to the problem statement
            
            IMPORTANT: Your code must use the EXACT FILENAME "data.txt" to open and read the file. Do not use any path, just the filename directly.
            
            Example for Python:
            ```python
            # Open the file using the standardized name
            file = open("data.txt", "r")
            lines = file.readlines()
            file.close()
            ```
            
            Example for C++:
            ```cpp
            FILE* file = fopen("data.txt", "r");
            // Read from file
            fclose(file);
            ```
            
            Add a FILE_REQUIRED marker at the beginning of your response, before the first code block:
            FILE_REQUIRED
            This program requires a file for testing. The file will be available as "data.txt".
            FILE_END
            
            For programs requiring user inputs AFTER reading a file, include those in your test inputs.
            """
        
        prompt = f"""
        Please generate a {assignment_type} program to solve the following problem statement: '{problem_statement}'.

        The {assignment_type} program MUST meet these STRICT requirements:

        1. **BEGINNER LEVEL CODE ONLY**: Write code as if for a first-year undergraduate student who is just learning to program.

        2. **SIMPLICITY IS ESSENTIAL**:
           - DO NOT use try/except blocks
           - DO NOT use if __name__ == "__main__" structures
           - For C++, DO NOT use <vector>, <algorithm>, or any STL containers
           - Use only the most basic control structures (if/else, for loops, while loops)
           - Avoid complex data structures - stick to arrays and simple variables

        3. **Input Handling**: For Python, ask the user to input numbers separated by spaces like this:
           ```python
           input_str = input("Enter numbers separated by spaces: ")
           numbers = [int(x) for x in input_str.split()]
           ```
           For C++, use simple cin for input.

        4. **Problem Solving**: Break down the solution into simple steps with comments.

        5. **NO ADVANCED TECHNIQUES**: Avoid lambdas, list comprehensions, or any feature that wouldn't be taught in the first semester.
        {file_handling_instructions}
        
        Furthermore, you need to generate two valid sets of test inputs that are logically consistent with the code. Present these test inputs in this specific format:
        ```
        TEST_START
        <inputs for test case 1>

        <inputs for test case 2>
        TEST_END
        ```
        
        NOTE: If the program requires file handling, test inputs might be empty or might only include inputs AFTER the file is read. The system handles file uploads separately.
        There must be a newline between each test case.
        
        Your ENTIRE output MUST be formatted as follows, and contain NOTHING else: 
        ```{assignment_type}
        [generated code]
        ```
        
        ```
        TEST_START
        [generated test inputs]

        [generated test inputs]
        TEST_END
        ```

        Ensure your response contains only the code and test inputs - no explanations or extra text.
        Test inputs must be practical examples that effectively test your code's functionality.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
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
        
        ## Algorithm:
        Provide a step-by-step algorithm that matches the following program(s):
        {code_response}
        
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
        return response.text