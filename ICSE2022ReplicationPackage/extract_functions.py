import subprocess
import xml.etree.ElementTree as ET
import os
import re
from setting import *
import tempfile
import json
import hashlib
import pandas as pd
import re

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
        # print('Converting to srcML...')
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
        ns = {
            'src': 'http://www.srcML.org/srcML/src',
            'pos': 'http://www.srcML.org/srcML/position',    
        }
        # Search for the function containing the specified line
        for function in root.findall(".//src:function", ns):
            # if line_str in ET.tostring(function, encoding='unicode'):
            
            # <function pos:start="40:1" pos:end="54:1">
            pos_start = function.attrib.get('{http://www.srcML.org/srcML/position}start') 
            pos_end = function.attrib.get('{http://www.srcML.org/srcML/position}end')
            
            # Extract the starting and ending line numbers
            start_line = int(pos_start.split(':')[0]) if pos_start else None
            end_line = int(pos_end.split(':')[0]) if pos_end else None

            # print((start_line <= line_number <= end_line))

            if start_line and end_line and (start_line <= line_number <= end_line):
                function_src = convert_xml_string_to_source(ET.tostring(function, encoding='unicode'))
                if line_str in function_src:
                    function_name = function.find('./src:name', ns)
                    # function_name_parts = function.findall('.//src:name', ns)
                    function_name = ''.join([part.text for part in function_name if part.text])
                    print(f'Found {line_str} in the function {function_name}.')
                    return function_src, function_name

    except Exception as e:
        print(f"Error While Finding The Function: {e}")

    return None, None

def extract_function_from_name(src_file_path, function_name):
    """
    Extract latent functions between the BFC and BIC based on file name and function name.
    """
    try:
        srcml_content = convert_to_srcml(src_file_path)
        # print(srcml_content)
        if not srcml_content:
            return None, None
        root = ET.fromstring(srcml_content)

        # Define the namespace
        ns = {
            'src': 'http://www.srcML.org/srcML/src',  # Adjust if needed
            'pos': 'http://www.srcML.org/srcML/position',
              # Adjust if needed
        }
        # Search for the function containing the specified line
        for function in root.findall(".//src:function", ns):
            extract_name = function.find('./src:name', ns)
            extract_name = ''.join([part.text for part in extract_name if part.text])
            if extract_name == function_name:
                function_src = convert_xml_string_to_source(ET.tostring(function, encoding='unicode'))
                if function_src:
                    return function_src
    except Exception as e:
        print(f"An error occurred while extracting the latent functions: {e}")

    return None

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
        # return '\n'.join(lines[1:])
        return '\n'.join(lines)
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

def replace_newlines_before_first_brace_with_space(text):
    # Find the first brace
    first_brace_index = text.find('{')
    if first_brace_index == -1:
        return text  # No brace found; return original text

    # Replace all newline characters before the first brace with a space
    before_brace = text[:first_brace_index]
    after_brace = text[first_brace_index:]
    before_brace = re.sub(r'\s+', ' ', before_brace)

    return before_brace + after_brace

def main():
    project = 'ChakraCore'
    repo_path = os.path.join(REPOS_DIR, project)
    # relative_file_path = 'lib/Runtime/ByteCode/ByteCodeGenerator.cpp'
    # if check_file_extension(relative_file_path, 'cpp'):
    #     language = 'cpp'
    # elif check_file_extension(relative_file_path, 'c'):
    #     language = 'c'
    

    # start with open json files
    file_name = f'results/my-{project}.json'
    # file_name = 'ICSE2022ReplicationPackage/results/my-ChakraCore.json'
    # file_name = os.path.join(os.getcwd(), file_name)
    with open(file_name, 'r') as file:
        vszz_out = json.load(file)
    out_data_list = []
    
    for bfc in vszz_out.keys():    
        if len(vszz_out[bfc]):  
            for deleted_line in vszz_out[bfc]:
                line_number = deleted_line['line_num']
                line_str = deleted_line['line_str']
                relative_file_path = deleted_line['file_path']
                previous_commits = deleted_line['previous_commits']
                for bic in previous_commits:
                    bic_commit_hash = bic[0]
                    bic_line_number = bic[1]
                    bic_line_str = bic[2]
                    # print(bic_commit_hash)
                    bic_file = checkout_file_at_commit(repo_path, relative_file_path, bic_commit_hash)
                    if bic_file:
                        bic_function_code, bic_function_name = extract_function_containing_line(bic_file, bic_line_number, bic_line_str)
                        if bic_function_code and bic_function_name:
                            bic_function_code = replace_newlines_before_first_brace_with_space(bic_function_code)
                            md5_function = hashlib.md5(bic_function_code.encode('utf-8')).hexdigest()
                            print("MD5")
                            print(md5_function)
                            print("FUNCTION NAME: ", bic_function_name)
                            out_data = {
                                'commit_hash': bic_commit_hash,
                                'type': 'bic',
                                'f_name': bic_function_name,
                                'md5': md5_function,
                                'src': bic_function_code,
                                'target' : 1
                            }
                            out_data_list.append(out_data)
                        elif bic_function_code is None or bic_function_name is None:
                            print(f"Function not found at commit {bic_commit_hash}, line {bic_line_number}, {bic_line_str}.")
                        
                        # getting latent
                        latents = get_commit_hashes_between(repo_path, bic_commit_hash, bfc)
                        if len(latents) > 0:
                            for lantent in latents:
                                latent_file = checkout_file_at_commit(repo_path, relative_file_path, lantent)
                                latent_function_code, latent_function_name = extract_function_containing_line(latent_file, bic_line_number, bic_line_str)
                                if latent_function_code and latent_function_name:
                                    latent_function_code = replace_newlines_before_first_brace_with_space(latent_function_code)
                                    md5_function = hashlib.md5(latent_function_code.encode('utf-8')).hexdigest()
                                    print("MD5")
                                    print(md5_function)
                                    print("FUNCTION NAME: ", latent_function_name)
                                    out_data = {
                                        'commit_hash': lantent,
                                        'type': 'latent',
                                        'f_name': latent_function_name,
                                        'md5': md5_function,
                                        'src': latent_function_code,
                                        'target' : 1
                                    }
                                    out_data_list.append(out_data)
                                elif latent_function_code is None or latent_function_name is None:
                                    print(f"Function not found at commit {lantent}, line {bic_line_number}, {bic_line_str}.")

    df = pd.DataFrame(out_data_list)
    df = df.drop_duplicates(subset='md5')
    column_order = ['commit_hash','type', 'f_name', 'md5', 'src', 'target']
    df = df[column_order]

    out_file= f"results/bic-{project}.csv"
    df.to_csv(out_file, index=False)


if __name__ == "__main__":
    main()