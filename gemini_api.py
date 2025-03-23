import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

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
    
    def generate_code(self, problem_statement: str, assignment_type: str, requires_file_handling: bool = False) -> str:
        """Generate code solution based on the problem statement.
        
        Args:
            problem_statement: The problem statement to solve
            assignment_type: The programming language to use (python, cpp, c)
            requires_file_handling: Whether the problem requires file handling
            
        Returns:
            Generated code solution
        """
        file_handling_instructions = ""
        if requires_file_handling:
            file_handling_instructions = """
            This problem requires file handling. Your solution should:
            1. Read from a file with a STANDARDIZED NAME: "data.txt" for a single file or "data0.txt", "data1.txt", etc. for multiple files
            2. Process the data from the file according to the problem statement
            3. Output the results according to the problem statement
            
            IMPORTANT: Your code must use the EXACT FILENAME "data.txt" (or "data0.txt", "data1.txt", etc. for multiple programs) 
            to open and read the file. The user uploads their own file but our system renames it to this standardized name.
            
            Example:
            ```python
            # Open the file using the standardized name
            with open("data.txt", "r") as file:
                # Process the file
                lines = file.readlines()
            ```
            
            Add a FILE_REQUIRED marker at the beginning of your response, before the first code block:
            FILE_REQUIRED
            This program requires a file for testing. The file will be available as "data.txt".
            FILE_END
            
            For programs requiring user inputs AFTER reading a file, include those in your test inputs.
            """
        
        prompt = f"""
        Please generate a {assignment_type} program to solve the following problem statement: '{problem_statement}'.

        The {assignment_type} program MUST meet these requirements:

        1.  **Input Handling:**  It must include an input prompt to receive multiple numerical inputs on a single line, for example, like this: '12 48 32'.  (It MUST use `.split()` and then `int()` with multiple assignment to convert these inputs into respective variables for python) (For C++ only one input prompt to user is enough because it can accept input with spaces normally)
        2.  **String Input Compatibility:** If the problem statement involves string inputs, the program should handle them appropriately.
        3.  **Problem Solving Functions:**  The program must call functions that directly address and solve the problem described in the problem statement.
        4.  **Output Display:**  The program must display the output that is returned from these function calls.
        5.  **Code Style:**  Apply necessary comments and adhere to good coding practices.
        6.  **Docstrings:** Include a concise, one-liner docstring for each function to explain its purpose.
        7.  **Multiple Programs:** If there are multiple programs in a single problem statement, make multiple code snippets for each program. All programs should come first, then the respective test inputs in their own code blocks.
        {file_handling_instructions}
        
        Furthermore, you need to generate two valid sets of test inputs that are logically consistent with the code. Present these test inputs in this specific format:
        ```
        TEST_START
        <inputs for test case 1>

        <inputs for test case 2>
        TEST_END
        ```
        
        NOTE: If the program requires file handling, test inputs might be empty or might only include inputs AFTER the file is read. The system handles file uploads separately. For example, if your program first reads data.txt and then asks for user input, only include the user input part in the test inputs.
        There must be a newline between each test case.
        
        Your ENTIRE output MUST be formatted as follows, and contain NOTHING else: 
        ```{assignment_type}
        [generated code 1]
        ```
        ```{assignment_type}
        [generated code 2]
        ```

        ```
        TEST_START
        [generated test inputs for code 1]

        [generated test inputs for code 2]
        TEST_END
        ```

        ```
        TEST_START
        [generated test inputs for code 1 second set]

        [generated test inputs for code 2 second set]
        TEST_END
        ```

        ENSURE YOU HAVE GENERATED SEPARATE PROGRAMS FOR SEPARATE PROBLEM STATEMENTS. 
        Ensure your response contains only the code and test inputs - no explanations or extra text.
        Test inputs must be practical examples that effectively test your code's functionality.
        For problems requiring multiple programs, provide separate code and test inputs for each.
        Keep the code at a first-year undergraduate level - accept user inputs but avoid advanced libraries and complex approaches.
        Use only basic libraries (iostream for C++ is acceptable). Prefer simple procedural solutions without classes.
        DO NOT USE VECTOR OR ALGORITHM HEADERS.
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
            ## No write up found for this one...
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
        The write-up should be basic to intermeddiate level up to a first year B.Tech. Student's level, and formatted as stated.
        Ensure it's detailed enough for 4-5 pages with information that's not too dense.
        """
        
        response = self.model.generate_content(prompt)
        return response.text