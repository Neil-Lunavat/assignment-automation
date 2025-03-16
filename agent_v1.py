# THIS IS A PROTOTYPE VERSION WHERE I ONLY IMPLEMENTED CODE TESTING AND MARKDOWN GENERTION
# I ALSO ADDED MD TO PDF API INTEGRATION AS A LEARNING STEP BEFORE MOVING ON TO THE STREAMLIT PROJECT


import subprocess
import sys
from google import genai

client = genai.Client(api_key="AIzaSyDfIAT5FXvwEE7QZeZ72VMiiJokCIHqCWo")

# Set the directory path to the location of the Python scripts
directory = r"C:\Users\Neil Lunavat\Desktop\programs\python"

def run_script(directory, script_path, inputs):
    """
    Simulates running a Python script in a command line interface with provided inputs.

    Args:
        directory (str): The current working directory to display in the prompt
        script_path (str): The relative path of the Python script to be run
        inputs (str): The inputs for the script, separated by newlines

    Returns:
        str: A formatted string showing the complete command line interaction
    """

    # Create the command to execute
    command = [sys.executable, script_path]

    # Run the script
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # inputs should be in "14\n19\n20" type of format for multiple else "input"

    stdout, stderr = process.communicate(input='\n'.join(inputs))

    # Print the interactive part with inputs inserted
    stdout_lines = [x.strip() for x in stdout.split(":")]
    input_index = 0

    output_capture = [f"{directory}> python {script_path}"]
    for line in stdout_lines.copy():
        if line.startswith("Enter") and input_index < len(inputs):
            output_capture.append(f"{line}: {inputs[input_index]}")
            input_index += 1
            stdout_lines.remove(line)

    output_capture.append(': '.join(stdout_lines))

    # Check if there were any errors
    if stderr:
        print(f"Error: {stderr}")

    return '\n'.join(output_capture)

# Initialize a list to store program outputs
programs = []

# Loop through the first 6 exercises to get their content
for i in range(1, 7):
    script_path = f'./Exercise/ex{i}.py'

    print(f"Running {script_path}")
    
    f = open(script_path)
    code = f.read()

    programs.append(code)

    # Generate test inputs using an API
    prompt = f"""You are a test input generator for Python programs. Follow these steps strictly:  

    ```python
    {code}
    ```

    1. **Analyze the Code Carefully:**  
    - Identify all `input()` functions.  
    - Determine if the program expects **only numbers** or **only strings** (never both).  
    - If `input()` is converted to `int()`, assume it expects numbers. Otherwise, assume it expects strings.  

    2. **Generate Two Valid Test Input Sets:**  
    - If the program expects **numbers**, generate **only numbers** (no words).  
        - If there's a single input, generate **one number**.  
        - IMPORTANT> If multiple inputs exist, generate numbers SEPARATED BY SPACE per test case. (eg. "12 18 20" and "39 68 27" for two lines of input)  
    - If the program expects **strings**, generate **only words** (no numbers).  
        - Use simple words like `"helloworld"` (no special characters or numbers).  

    3. **Format Output Exactly Like This:**
    TEST_START
    <inputs for test case 1, space separated if multiple inputs in a single program>
    <inputs for test case 2, space separated if multiple inputs in a single program>
    TEST_END

    - Ensure correct formatting, no extra text, and logically valid inputs based on the code.  
    - If the program requires multiple inputs, separate them by space.  

    **Strictly follow these rules to prevent hallucinations or incorrect outputs.** 
    """

    test_inputs = client.models.generate_content(model="gemini-2.0-flash", contents=prompt).text.split('\n')
    start = test_inputs.index("TEST_START")
    end = test_inputs.index("TEST_END")
    test_inputs = test_inputs[start+1:end]

    print("Testing inputs: ", test_inputs)
    # Extract the actual inputs from the generated prompt
    for i in range(len(test_inputs)):
        programs.append(run_script(directory, script_path, test_inputs[i].split(' ')))
    

upload = """# Function Exercise
Name: Neil Lunavat
PRN: 124B1B141
Batch: K-2

"""

for i in range(0, len(programs), 3):
    upload += f"\n### Exercise {int((i/3)+1)}:\n```python\n{programs[i]}\n```\n\n### Output:\n```\n{programs[i+1]}\n{programs[i+2]}\n```\n"

# print(upload)
import requests

# CSS styles
css = """
body {
  font-size: 80%;
}
table {
  border-collapse: collapse;
}
table, th, td {
  border: 1px solid DimGray;
}
th, td {
  text-align: left;
  padding: 1em;
}
"""

# API endpoint
url = "https://md-to-pdf.fly.dev"

# POST request to convert markdown to PDF
response = requests.post(url, data={"markdown": upload, "css": css})

# Save the response content as a PDF file
if response.status_code == 200:
    with open("124B1B141_Neil_K2.pdf", "wb") as f:
        f.write(response.content)
    print("PDF saved successfully as upload.pdf")
else:
    print(f"Error: {response.status_code}, {response.text}")
