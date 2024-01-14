import re
import pandas as pd

def replace_newlines_before_first_brace_with_space(text):
    # Find the first brace
    first_brace_index = text.find('{')
    if first_brace_index == -1:
        return text  # No brace found; return original text

    # Replace all newline characters before the first brace with a space
    before_brace = text[:first_brace_index]
    after_brace = text[first_brace_index:]
    before_brace = re.sub(r'[\n\t]', ' ', before_brace)

    return before_brace + after_brace

# Example usage
# code_example = """Js::Var
# BailOutRecord::BailOutHelper(Js::JavascriptCallStackLayout * layout, Js::ScriptFunction ** functionRef, Js::Arguments& args, const bool isInlinee,
#     BailOutRecord const * bailOutRecord, uint32 bailOutOffset, void * returnAddress, IR::BailOutKind bailOutKind, Js::Var * registerSaves, BailOutReturnValue * bailOutReturnValue, Js::Var* pArgumentsObject,
#     Js::Var branchValue, void * argoutRestoreAddress)
# {
#     // Function body
# }
# """

# new_code = replace_newlines_before_first_brace_with_space(code_example)
# visible_newlines = new_code.replace('\n', '\\n\n')
# print(visible_newlines)

csv_file = 'results/bic-ChakraCore.csv'
df = pd.read_csv(csv_file)

# Getting the length of the DataFrame
length_of_csv = len(df)

print(length_of_csv)