import argparse
import os
import re

def parse_puml_classes(puml_text):
    classes = {}
    class_pattern = re.compile(r'class\s+(\w+)\s*{')
    pos = 0
    while True:
        match = class_pattern.search(puml_text, pos)
        if not match:
            break
        class_name = match.group(1)
        start = match.end()
        brace_count = 1
        end = start
        while end < len(puml_text) and brace_count > 0:
            if puml_text[end] == '{':
                brace_count += 1
            elif puml_text[end] == '}':
                brace_count -= 1
            end += 1
        class_body = puml_text[start:end-1]
        # Debug summary
        print(f"Class: {class_name}")
        print("Raw lines:")
        for line in class_body.splitlines():
            print(f"  {line}")
        classes[class_name] = class_body.splitlines()
        pos = end

    # Extract properties and methods
    class_details = {}
    for class_name, lines in classes.items():
        properties = []
        methods = []
        for line in lines:
            # Remove comments
            line_no_comment = line.split("'")[0].strip()
            if not line_no_comment:
                continue
            if line_no_comment[0] in ['+', '-', '#']:
                # Determine if method or property by presence of '(' and ')'
                if '(' in line_no_comment and ')' in line_no_comment:
                    methods.append(line_no_comment)
                else:
                    properties.append(line_no_comment)
        class_details[class_name] = {
            'properties': properties,
            'methods': methods
        }
    return class_details

def extract_class_blocks(puml_content):
    class_blocks = []
    pattern = re.compile(r'class\s+(\w+)\s*{')
    pos = 0
    while True:
        match = pattern.search(puml_content, pos)
        if not match:
            break
        class_name = match.group(1)
        start_brace_pos = puml_content.find('{', match.end() - 1)
        if start_brace_pos == -1:
            pos = match.end()
            continue
        brace_count = 1
        end_pos = start_brace_pos + 1
        while end_pos < len(puml_content) and brace_count > 0:
            if puml_content[end_pos] == '{':
                brace_count += 1
            elif puml_content[end_pos] == '}':
                brace_count -= 1
            end_pos += 1
        class_block = puml_content[start_brace_pos + 1:end_pos - 1]
        class_blocks.append((class_name, class_block))
        pos = end_pos
    return class_blocks

def map_swift_type(type_str):
    type_str = type_str.strip()
    # Optional<T> → T?
    m = re.match(r'Optional<([\w\[\]\.<>,\s]+)>', type_str)
    if m:
        inner = map_swift_type(m.group(1).strip())
        return inner + '?'
    # List<T> → [T]
    m = re.match(r'List<([\w\[\]\.<>,\s]+)>', type_str)
    if m:
        inner = map_swift_type(m.group(1).strip())
        return f'[{inner}]'
    # Map<K,V> → [K: V]
    m = re.match(r'Map<([\w\[\]\.<>,\s]+),\s*([\w\[\]\.<>,\s]+)>', type_str)
    if m:
        key = map_swift_type(m.group(1).strip())
        val = map_swift_type(m.group(2).strip())
        return f'[{key}: {val}]'
    # Set<T> → Set<T>
    m = re.match(r'Set<([\w\[\]\.<>,\s]+)>', type_str)
    if m:
        inner = map_swift_type(m.group(1).strip())
        return f'Set<{inner}>'
    # Result<T, E> → Result<T, E>
    m = re.match(r'Result<([\w\[\]\.<>,\s]+),\s*([\w\[\]\.<>,\s]+)>', type_str)
    if m:
        t1 = map_swift_type(m.group(1).strip())
        t2 = map_swift_type(m.group(2).strip())
        return f'Result<{t1}, {t2}>'
    # Generic fallback: Type<...> → Type<...> with recursive mapping inside
    m = re.match(r'([\w_]+)<([\w\[\]\.<>,\s]+)>', type_str)
    if m:
        base = m.group(1)
        params = m.group(2)
        # Split params by comma, but handle nested generics carefully
        parts = []
        depth = 0
        current = ''
        for c in params:
            if c == '<':
                depth += 1
                current += c
            elif c == '>':
                depth -= 1
                current += c
            elif c == ',' and depth == 0:
                parts.append(current.strip())
                current = ''
            else:
                current += c
        if current:
            parts.append(current.strip())
        mapped_parts = [map_swift_type(p) for p in parts]
        return f'{base}<' + ', '.join(mapped_parts) + '>'
    # Chunk[*] or Type[*] → [Chunk] or [Type]
    m = re.match(r'(\w+)\[\*\]', type_str)
    if m:
        return f'[{m.group(1)}]'
    # float[] → [Float], int[] → [Int]
    m = re.match(r'(\w+)\[\]', type_str)
    if m:
        base = m.group(1).capitalize()
        return f'[{base}]'
    # Binary → Data
    if type_str == 'Binary':
        return 'Data'
    # float → Float, int → Int
    if type_str == 'float':
        return 'Float'
    if type_str == 'int':
        return 'Int'
    # オプショナル型
    if type_str.endswith('?'):
        return map_swift_type(type_str[:-1]) + '?'
    # 何もしない（そのまま返す）
    return type_str

def main():
    parser = argparse.ArgumentParser(description="PlantUML class diagram (.puml) to Swift class generator")
    parser.add_argument('--in', dest='input_dir', required=True, help='Input directory with .puml files')
    parser.add_argument('--out', dest='output_dir', required=True, help='Output directory for .swift files')
    cli_args = parser.parse_args()
    if not os.path.isdir(cli_args.input_dir):
        print(f"Input directory '{cli_args.input_dir}' does not exist.")
        return
    if not os.path.isdir(cli_args.output_dir):
        print(f"Output directory '{cli_args.output_dir}' does not exist. Creating it.")
        os.makedirs(cli_args.output_dir)

    # List all .puml files
    for fname in os.listdir(cli_args.input_dir):
        if fname.endswith('.puml'):
            # Read and parse the .puml file
            puml_path = os.path.join(cli_args.input_dir, fname)
            with open(puml_path, 'r', encoding='utf-8') as f:
                puml_content = f.read()
            print(f"Read {fname}: {puml_content[:100]}{'...' if len(puml_content) > 100 else ''}")

            # Extract all class blocks with nested braces handling
            class_blocks = extract_class_blocks(puml_content)
            if not class_blocks:
                print(f"No class found in {fname}")
                continue

            for class_name, class_block in class_blocks:
                # Debug summary of class block raw lines
                raw_lines = class_block.splitlines()
                print(f"Class '{class_name}' raw lines ({len(raw_lines)} lines):")
                for line in raw_lines:
                    print(f"  {line}")

                # Collect class-level comments (before first non-comment, non-empty line)
                class_comments = []
                idx = 0
                while idx < len(raw_lines):
                    line = raw_lines[idx].strip()
                    if not line or line.startswith("'") or line.startswith("//"):
                        if line.startswith("'") or line.startswith("//"):
                            class_comments.append(line)
                        idx += 1
                    else:
                        break

                # Improved property and method extraction logic with comment association
                properties = []
                methods = []
                pending_comments = []
                for line in raw_lines[idx:]:
                    line_stripped = line.strip()
                    # Track consecutive comment lines
                    if line_stripped.startswith("'") or line_stripped.startswith("//"):
                        pending_comments.append(line_stripped)
                        continue
                    # Remove inline comments starting with '//' or "'"
                    line_no_inline_comment = re.sub(r'//.*$', '', line_stripped)
                    line_no_inline_comment = re.sub(r"'.*$", '', line_no_inline_comment).strip()
                    if not line_no_inline_comment:
                        pending_comments = []
                        continue
                    if not (line_no_inline_comment.startswith('+') or line_no_inline_comment.startswith(
                            '-') or line_no_inline_comment.startswith('#')):
                        pending_comments = []
                        continue
                    # Match "+name: Type = defaultValue"
                    m_property_default = re.search(r'^[+\-#]\s*(\w+)\s*:\s*([\w\[\]\*\._<>]+)\s*=\s*(.+)$',
                                                   line_no_inline_comment)
                    if m_property_default:
                        prop_name = m_property_default.group(1)
                        prop_type = m_property_default.group(2) if m_property_default.group(2) else 'Any'
                        default_value = m_property_default.group(3).strip()
                        properties.append((prop_name, prop_type, pending_comments, default_value))
                        pending_comments = []
                        continue
                    # Match "+Type name"
                    m_property = re.search(r'^[+\-#]\s*([\w\[\]\*\._<>]+)\s+(\w+)$', line_no_inline_comment)
                    if m_property:
                        prop_type = m_property.group(1) if m_property.group(1) else 'Any'
                        prop_name = m_property.group(2)
                        properties.append((prop_name, prop_type, pending_comments, None))
                        pending_comments = []
                        continue
                    # Alternate property pattern "+name: Type"
                    m_property_alt = re.search(r'^[+\-#]\s*(\w+)\s*:\s*([\w\[\]\*\._<>]+)', line_no_inline_comment)
                    if m_property_alt:
                        prop_name = m_property_alt.group(1)
                        prop_type = m_property_alt.group(2) if m_property_alt.group(2) else 'Any'
                        properties.append((prop_name, prop_type, pending_comments, None))
                        pending_comments = []
                        continue

                    # Match "+name(args)" (method, no return type)
                    m_method_noreturn = re.search(r'^[+\-#]\s*(\w+)\s*\((.*?)\)\s*$', line_no_inline_comment)
                    if m_method_noreturn:
                        method_name = m_method_noreturn.group(1).strip()
                        params_str = m_method_noreturn.group(2).strip()
                        return_type = 'Void'
                        params_rendered = ''
                        if params_str:
                            param_list = []
                            for param in params_str.split(','):
                                param = param.strip()
                                if not param:
                                    continue
                                if ':' in param:
                                    param_name, param_type = map(str.strip, param.split(':', 1))
                                    param_list.append(f"{param_name}: {map_swift_type(param_type)}")
                                else:
                                    param_list.append(f"{param}: Any")
                            params_rendered = ', '.join(param_list)
                        methods.append((method_name, params_rendered, map_swift_type(return_type), pending_comments))
                        pending_comments = []
                        continue
                    # Match "+Type name" (property)
                    m_property = re.search(r'^[+\-#]\s*([\w\[\]\*\._<>]+)\s+(\w+)$', line_no_inline_comment)
                    if m_property:
                        prop_type = m_property.group(1) if m_property.group(1) else 'Any'
                        prop_name = m_property.group(2)
                        properties.append((prop_name, prop_type, pending_comments))
                        pending_comments = []
                        continue
                    # Alternate property pattern "+name: Type"
                    m_property_alt = re.search(r'^[+\-#]\s*(\w+)\s*:\s*([\w\[\]\*\._<>]+)', line_no_inline_comment)
                    if m_property_alt:
                        prop_name = m_property_alt.group(1)
                        prop_type = m_property_alt.group(2) if m_property_alt.group(2) else 'Any'
                        properties.append((prop_name, prop_type, pending_comments))
                        pending_comments = []
                        continue
                    # Warn if line not matched
                    print(f"[WARN] Could not parse property or method line: {line_stripped}")
                    pending_comments = []

                # Generate Swift class code
                swift_code = ''
                for cmt in class_comments:
                    cmt_text = cmt.lstrip("'").lstrip("//").strip()
                    swift_code += f'/// {cmt_text}\n'
                swift_code += f'class {class_name} {{\n'
                for prop_name, prop_type, comments, _ in properties:
                    for cmt in comments:
                        cmt_text = cmt.lstrip("'").lstrip("//").strip()
                        swift_code += f'    /// {cmt_text}\n'
                    swift_code += f'    var {prop_name}: {map_swift_type(prop_type)}\n'
                if properties:
                    params = ', '.join([
                        f'{prop_name}: {map_swift_type(prop_type)}{f" = {default_value}" if default_value else ""}'
                        for prop_name, prop_type, _, default_value in properties
                    ])
                    swift_code += f'\n    init({params}) {{\n'
                    for prop_name, _, _, _ in properties:
                        swift_code += f'        self.{prop_name} = {prop_name}\n'
                    swift_code += '    }\n'
                for method_name, params, ret_type, comments in methods:
                    for cmt in comments:
                        cmt_text = cmt.lstrip("'").lstrip("//").strip()
                        swift_code += f'    /// {cmt_text}\n'
                    swift_code += f'    func {method_name}({params}) -> {ret_type} {{\n        // TODO: implement\n    }}\n'
                swift_code += '}\n'

                # Add import Foundation if Data is used
                if 'Data' in swift_code:
                    swift_code = 'import Foundation\n\n' + swift_code

                # Write to output_dir
                swift_file_path = os.path.join(cli_args.output_dir, f'{class_name}.swift')
                with open(swift_file_path, 'w', encoding='utf-8') as f:
                    f.write(swift_code)

                # Write to output_dir
                print(f"Generated Swift code for {class_name}:\n{swift_code}")
                swift_file_path = os.path.join(cli_args.output_dir, f'{class_name}.swift')
                with open(swift_file_path, 'w', encoding='utf-8') as f:
                    f.write(swift_code)
                print(f"Wrote Swift file: {swift_file_path}")
    print("Done.")

if __name__ == '__main__':
    main()