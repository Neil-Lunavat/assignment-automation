import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAPI:
    def __init__(self):
        """Initialize the Gemini API with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_code(self, problem_statement):
        """Generate code solution based on the problem statement."""
        prompt = """
        Please generate a Python program to solve the following problem statement: '{problem_statement}'.

        The Python program MUST meet these requirements:

        1.  **Input Handling:**  It must include an input prompt to receive multiple numerical inputs on a single line, for example, like this: '12 48 32'.  It MUST use `.split()` and then `int()` with multiple assignment to convert these inputs into respective variables.
        2.  **String Input Compatibility:** If the problem statement involves string inputs, the program should handle them appropriately.
        3.  **Problem Solving Functions:**  The program must call functions that directly address and solve the problem described in the problem statement.
        4.  **Output Display:**  The program must display the output that is returned from these function calls.
        5.  **Code Style:**  Apply necessary comments and adhere to good coding practices.
        6.  **Docstrings:** Include a concise, one-liner docstring for each function to explain its purpose.

        Furthermore, you need to generate two valid sets of test inputs that are logically consistent with the code. Present these test inputs in this specific format:
        ```
        TEST_START
        <inputs for test case 1>
        <inputs for test case 2>
        TEST_END
        ```
        Your ENTIRE output MUST be formatted as follows, and contain NOTHING else: 
        ```python
        {generated python code}
        ```

        ```
        {generated test inputs}
        ```
        Ensure there is NO extra text, no introductory phrases, and that the test inputs are logically valid based on the code you generate.  The test inputs should be designed to properly test the functionality of the generated Python code.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def generate_writeup(self, theory_points, assignment_number="", problem_statement=""):
        """Generate a theoretical writeup based on the provided theory points."""
        theory = "\n".join([f"- {point}" for point in theory_points])
        
        prompt = f"""
        Create a comprehensive write-up for Assignment {assignment_number} using this format:
        
        # Assignment No {assignment_number}

        ## Title: 
        [Extract from the problem statement]

        ## Problem Statement: 
        {problem_statement}

        ## Objective: 
        To make students familiar with the use of control flow tools in Python.

        ## Outcome: 
        Use control flow statements to implement logic in programs.

        ## Theory:

        For each of these theory topics:
        {theory}
        
        Create detailed sections with the following characteristics:
        
        1. Start each section with a heading (e.g., "### How to generate Fibonacci series")
        2. Provide a clear conceptual explanation with examples and mathematical calculations where relevant
        3. Include fundamental understanding, followed by deeper insights
        4. For programming concepts, include practical examples with code snippets
        5. Explain mathematical properties and formulas where applicable
        6. Discuss real-world applications
        7. Cover optimization techniques and best practices
        
        ## Algorithm:
        Provide a step-by-step algorithm for solving the problem in the assignment.

        ## Conclusion:
        Write a reflection on what was learned from implementing this assignment, focusing on the understanding of control flow tools and their application.

        The write-up should be comprehensive, educational, and formatted in Markdown. Ensure it's detailed enough for 4-5 pages while maintaining academic rigor and clarity.
        """
        
        response = self.model.generate_content(prompt)
        return response.text