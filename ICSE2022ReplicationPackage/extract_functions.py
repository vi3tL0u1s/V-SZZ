import subprocess
import xml.etree.ElementTree as ET
import os
import re
from setting import *
import tempfile

def checkout_file_at_commit(repo_path, relative_file_path, commit_hash):
    """
    Checks out a specific version of a file at a given commit hash.
    """
    try:
        # Change directory to the repository path
        os.chdir(repo_path)
        file_path = os.path.join(repo_path, relative_file_path)
        # Run the Git checkout command for the specific file at the given commit hash
        subprocess.run(['git', 'checkout', commit_hash, relative_file_path], check=True)
        print(f"Checked out file {relative_file_path} at commit {commit_hash}")
        os.chdir(WORK_DIR)
    except subprocess.CalledProcessError as e:
        print(f"Error checking out file: {e}")
        return None
    return file_path

def get_commit_hashes_between(repo_path, bic, bfc):
    """
    Get a list of commit hashes between two specified commits in a Git repository.
    The list is ordered from oldest to newest.

    :param repo_path: Path to the local Git repository.
    :param bic: The starting commit hash (older).
    :param fic: The ending commit hash (newer).
    :return: A list of commit hashes.
    """
    try:
        # Navigate to the repository directory
        os.chdir(repo_path)
        # file_path = os.path.join(repo_path, relative_file_path)
        command = ['git', 'log', '--format=%H', f'{bic}..{bfc}']
        
        # Execute the command
        result = subprocess.run(command, cwd=repo_path, check=True, capture_output=True, text=True)
        os.chdir(WORK_DIR)
        # Split the output into lines and return as a list
        # print(result.stdout.strip().split('\n')[0])
        return result.stdout.strip().split('\n')[1:]
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def check_file_extension(file_path, language):
    """
    Check if the file has the specified extension.

    :param file_path: The path to the file.
    :param extension: The extension to check for. Should include the dot, e.g., '.txt'.
    :return: True if the file has the specified extension, False otherwise.
    """
    _, file_extension = os.path.splitext(file_path)
    if language == 'c':
        extension = ['.c', '.h']
    elif language == 'cpp':
        extension = ['.cpp', '.hpp', '.cxx', '.hxx', '.cc', '.hh']
    
    return file_extension.lower() in extension

def convert_to_srcml(src_file_path):
    """
    Convert a C++ source file to srcML format and return as a string.
    """
    try:
        print('Converting to srcML...')
        command = ['srcml', src_file_path, '--position']

        # Run the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # with open('test.xml', 'w') as file:
        #     file.write(result.stdout)
        # print('Converted to srcML.')
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error converting to srcML: {e}")
        return None

def extract_function_containing_line(src_file_path, line_number, line_str):
    """
    Extract a function from srcML content based on a line string.
    """
    try:
        srcml_content = convert_to_srcml(src_file_path)
        # print(srcml_content)
        if not srcml_content:
            return None, None
        root = ET.fromstring(srcml_content)

        # Define the namespace
        ns = {'src': 'http://www.srcML.org/srcML/src'}
        # Search for the function containing the specified line
        for function in root.findall(".//src:function", ns):
            # if line_str in ET.tostring(function, encoding='unicode'):
            
            # <function pos:start="40:1" pos:end="54:1">
            pos_start = function.attrib.get('{http://www.srcML.org/srcML/position}start') 
            pos_end = function.attrib.get('{http://www.srcML.org/srcML/position}end')
            
            # Extract the starting and ending line numbers
            start_line = int(pos_start.split(':')[0]) if pos_start else None
            end_line = int(pos_end.split(':')[0]) if pos_end else None
            if start_line and end_line and start_line <= line_number <= end_line:
                function_src = convert_xml_string_to_source(ET.tostring(function, encoding='unicode'))
                if line_str in function_src:
                    function_name = function.find('./src:name', ns)
                    print(f'Found {line_str} in the function {function_name.text}.')
                    return function_src, function_name.text

    except Exception as e:
        print(f"Error While Finding The Function: {e}")

    return None, None

def convert_line_to_srcml(line_str, language, line_number):
    """
    Convert a single line of C/C++ code to srcML XML format and extract the specific part.
    """
    try:
        # Using srcML to convert the line to XML format
        if language == 'c':
            result = subprocess.run(['srcml', '--position', '--language=C', '-'], input=line_str, text=True, capture_output=True, check=True)
        elif language == 'cpp':
            result = subprocess.run(['srcml', '--position', '--language=C++', '-'], input=line_str, text=True, capture_output=True, check=True)
        srcml_output = result.stdout
        
        modified_srcml_output = srcml_output.replace('1:', f'{line_number}:')

        # Parse the srcML output
        root = ET.fromstring(modified_srcml_output)

        # Handle the namespace
        namespaces = {'src': 'http://www.srcML.org/srcML/src'}  # Define the namespace

        # Navigate to the 'call' element with the namespace
        call_element = root.find(".//src:call", namespaces)
        
        if call_element is not None:
            # Convert the 'call' element back to string, handling namespace
            call_element = ET.tostring(call_element, encoding='unicode', method='xml')
            first_tag_end = call_element.find('>') + 1
            last_tag_start = call_element.rfind('<')
            call_element = call_element[first_tag_end:last_tag_start]
            return call_element
        else:
            return "Call element not found."
    except subprocess.CalledProcessError as e:
        print(f"Error converting line to srcML: {e}")
        return None
    except ET.ParseError as e:
        return f"Error parsing src"
    
def wrap_srcml_content(srcml_content):
    """
    Wraps a srcML content snippet with the necessary root element for srcML.

    :param srcml_content: The srcML content of a function or other code snippet.
    :return: The wrapped srcML content.
    """
    srcml_wrapper_start = '<src:unit xmlns:src="http://www.srcML.org/srcML/src">'
    srcml_wrapper_end = '</src:unit>'

    wrapped_content = f"{srcml_wrapper_start}{srcml_content}{srcml_wrapper_end}"
    return wrapped_content

def convert_xml_string_to_source(xml_content):
    """
    Converts an XML string generated by srcML back to source code using the srcml command.

    :param xml_content: XML content as a string.
    :return: Converted source code as a string.
    """
    try:
        # Create a temporary file to hold the XML content
        xml_content = wrap_srcml_content(xml_content)
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.xml') as temp_xml_file:
            temp_xml_file.write(xml_content)
            temp_xml_file_path = temp_xml_file.name

        # Construct the srcml command
        command = ['srcml', temp_xml_file_path]

        # Execute the command and capture the output
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        lines = result.stdout.splitlines()
        return '\n'.join(lines[1:])
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while converting XML to source code: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    finally:
        # Clean up the temporary file
        if temp_xml_file:
            temp_xml_file.close()
            os.remove(temp_xml_file_path)


def main():
    # Change with your working directory in setting.py
    project = 'ChakraCore'
    repo_path = os.path.join(REPOS_DIR, project)
    relative_file_path = 'lib/Runtime/ByteCode/ByteCodeGenerator.cpp'
    if check_file_extension(relative_file_path, 'cpp'):
        language = 'cpp'
    elif check_file_extension(relative_file_path, 'c'):
        language = 'c'
    commit_hash = '5d8406741f8c60e7bf0a06e4fb71a5cf7a6458dc'  
    line_str = 'pnodeParent->sxFnc.funcInfo->OnEndVisitScope(pnodeScope->sxWith.scope);'  
    line_number = 3146
    bic = '5d8406741f8c60e7bf0a06e4fb71a5cf7a6458dc'
    bfc = 'dfd30e220dbff8baf85e3b6463b4be32e2b1b3d0'
    commits = get_commit_hashes_between(repo_path, bic, bfc)
    print(len(commits))
    # print(commits[0])
    # print(commits[-1])
    
    # exit()

    # adapted_line_str = convert_line_to_srcml(line_str, language, line_number)

    # print(adapted_line_str)
    # Checkout the file at the specific commit
    checked_out_file = checkout_file_at_commit(repo_path, relative_file_path, commit_hash)
    if checked_out_file:
        # Extract the function
        function_code, function_name = extract_function_containing_line(checked_out_file, line_number, line_str)
        if function_code:
            with open('test.cpp', 'w') as file:
                file.write(function_code)
        else:
            print("Function not found.")

if __name__ == "__main__":
    main()