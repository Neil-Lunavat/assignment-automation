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
    
    def generate_code(self, problem_statement, assignment_type):
        """Generate code solution based on the problem statement."""
        prompt = f"""
        Please generate a {assignment_type} program to solve the following problem statement: '{problem_statement}'.

        The {assignment_type} program MUST meet these requirements:

        1. **Beginner Level Code:** Write extremely simple code that looks like it's written by a student who JUST started learning programming. For Python, don't use advanced concepts like list comprehensions, f-strings, or if __name__ == "__main__".

        2. **Input Handling:** 
        - Python: Use simple input() with print prompts, split() for multiple inputs on one line, and basic type conversion.
        - C++: Use using namespace std; and cin with simple prompts.
        - C: Use scanf() with simple prompts.

        3. **Problem Solving:** Use basic functions that directly solve the problem for python - NO classes, NO complex data structures.
        3.5 **For C++**: use classes when object oriented programming concepts are stated in problem statement. 

        4. **Style:** Include simple comments and basic variable names. Don't use advanced error handling.

        5. **Output Format:** Use basic print statements (print() in Python, printf() in C, std::cout in C++).

        6. **Multiple Programs:** If multiple programs are needed in a problem statement, create separate blocks for each program.

        7. **Structure:** For Python, write plain functions and main code without any if __name__ == "__main__" blocks. For C/C++, use basic function definitions and a simple main() function.

        Generate two test inputs that can produce the output the program is trying to demonstrate. Format these inputs as:
        ```
        TEST_START
        <inputs for test case 1>

        <inputs for test case 2>
        TEST_END
        ```

        Your ENTIRE output MUST be formatted EXACTLY as follows with NOTHING else: 
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

        ENSURE:
        - Code is at beginner level (first semester programming student)
        - Use only basic libraries (stdio.h for C, iostream for C++, no imports for Python unless absolutely necessary)
        - Try to solve the programs using basic algorithms like bubble sort, binary search etc. to avoid use of libraries like algorithm and vector.
        - Avoid all advanced coding concepts and syntax
        - Use descriptive variable names that beginners would understand (num1, num2, result, etc.)
        - Include simple comments that explain what the code is doing
        - All inputs must come from the user (no hardcoded values)
        - Focus on procedural programming in python, and object oriented programming in C++ if stated
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def generate_writeup(self, theory_points, code_response="None", assignment_number="None", problem_statement="None", assignment_type="python"):
        """Generate a theoretical writeup based on the provided theory points."""
        
        if not theory_points:
            return """
            ```markdown
            ## No write up found for this one...
            ```
            """
        theory = "\n".join([f"- {point}" for point in theory_points])
        
        prompt = f"""
        Create a write-up for this {assignment_type} Assignment using this format:
        
        ```markdown
        # Assignment No {assignment_number}

        ## Title: 
        [Extract a simple title from the theory points]

        ## Problem Statement: 
        {problem_statement}

        ## Objective: 
        [Extrapolate from theory and problem statement]

        ## Theory:

        For each of these theory topics:
        {theory}
        
        Expand the write up for relevant number of paragraphs to fill up 5 pages with these points in mind:
        (Don't strictly follow this, the theory points are guidelines, not rules)

        1. Start each section with a simple heading (e.g., "### How to Generate Fibonacci Series")
        2. Provide a clear explanation with examples and mathematical calculations where relevant
        3. Include step-by-step explanations with basic examples
        4. For programming concepts, include only 2-3 short code snippets as examples for the entire write up, no more
        5. Use simple mathematical explanations - avoid complex notation and formulas

        ## Algorithm:
        Write a simple, step-by-step algorithm that matches this program:
        {code_response}
        
        ## Conclusion:
        Summarize and write a conclusion on what was learned from implementing this assignment.
        Keep it concise and formal, only upto a paragraph.
        ```

        Follow this format exactly and only output the markdown content.
        Make the entire write-up appropriate for a college student who is just beginning to learn programming (1-2 months of experience).
        Use:
        - Short paragraphs (4-5 sentences maximum)
        - Bullet points where appropriate
        - Concrete examples rather than abstract concepts
        - Avoid complex mathematical notations - use plain language explanations instead
        
        The goal is to create a 3-4 pages write-up that helps demonstrate understanding the concepts and gain in knowledge.
        """
        
        response = self.model.generate_content(prompt)
        return response.text