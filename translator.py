import re
import sys

from typing import Tuple, List
from isa import write_code


def translate_stage_1(raw: str) -> str:
    raws = raw.split("\n")
    cleaned_raws = []

    for r in raws:
        r = r.partition(";")[0]
        cleaned_raws.append(r.strip())

    text = " ".join(cleaned_raws)
    text = re.sub(r" +", " ", text)  # remove extra whitespaces

    return text


def replace_with_ascii(text):
    result = ""
    in_quotes = False
    for char in text:
        if char == "\"":
            in_quotes = not in_quotes
            continue
        if in_quotes:
            result += str(ord(char)) + ","
        else:
            result += char
    return result


def translate_stage_2(text) -> Tuple[list, list]:
    text = replace_with_ascii(text)
    data_section_index = text.find("section data:")
    text_section_index = text.find("section text:")

    data_tokens = re.split("[, ]", text[data_section_index + len("section data:"): text_section_index])
    data_tokens = list(filter(lambda token: token, data_tokens))
    data_tokens = list(map(lambda token: (token[:-1],) if token[-1] == ':' else token, data_tokens))

    instruction_tokens = re.split("[, ]", text[text_section_index + len("section text:"):])
    instruction_tokens = list(filter(lambda token: token, instruction_tokens))
    instruction_tokens = list(map(lambda token: (token[:-1],) if token[-1] == ':' else token, instruction_tokens))

    return data_tokens, instruction_tokens


def translate_stage_3(data_tokens: List[str], instruction_tokens: List[str]):
    data = []
    data_labels = {}
    code = []
    code_labels = {}

    for data_token in data_tokens:
        if isinstance(data_token, tuple):
            data_labels[data_token[0]] = len(data)
        elif data_token.isdigit():
            data.append(data_token)

    i = 0
    while i < len(instruction_tokens):
        token = instruction_tokens[i]
        if isinstance(token, tuple):
            code_labels[token[0]] = len(code)
            i += 1
            continue

        pre_opcode = instruction_tokens[i].upper()
        if pre_opcode in ["HLT"]:
            code.append({"opcode": pre_opcode, "args": []})
            i += 1
            pass
        elif pre_opcode in ["JMP"]:
            code.append({"opcode": pre_opcode, "args": [instruction_tokens[i + 1]]})
            i += 2
            pass
        elif pre_opcode in ["LD"]:
            addr_type = detect_addr_type(instruction_tokens[i + 2])
            code.append(
                {"opcode": pre_opcode, "addr_type": addr_type if addr_type != 0 else 1,
                 "args": [instruction_tokens[i + 1], instruction_tokens[i + 2].strip("[]")]})
            i += 3
            pass
        elif pre_opcode in ["SW"]:
            addr_type = detect_addr_type(instruction_tokens[i + 1])
            code.append(
                {"opcode": pre_opcode, "addr_type": addr_type if addr_type != 0 else 1,
                 "args": [instruction_tokens[i + 1].strip("[]"), instruction_tokens[i + 2]]})
            i += 3
            pass
        elif pre_opcode in ["JMP", "BEQ", "BLT", "BNQ"]:
            code.append({"opcode": pre_opcode, "args": [instruction_tokens[i + 1], instruction_tokens[i + 2], instruction_tokens[i + 3]]})
            i += 4
            pass
        elif pre_opcode in ["ADD", "SUB", "MUL", "DIV", "REM"]:
            addr_type = detect_addr_type(instruction_tokens[i + 3])
            code.append(
                {"opcode": pre_opcode, "addr_type": addr_type,
                 "args": [instruction_tokens[i + 1], instruction_tokens[i + 2], instruction_tokens[i + 3]]})
            i += 4
            pass
        else:
            raise SyntaxError(f"Unknown instruction: {pre_opcode }")

    return data, data_labels, code, code_labels


def detect_addr_type(arg: str) -> int:
    if re.fullmatch(r'r\d', arg):
        return 0
    elif re.fullmatch(r'\[r\d\]', arg):
        return 1
    return 2


def translate_stage_4(program: list, data: list) -> list:
    for i in range(len(program)):
        for arg in range(len(program[i]["args"])):
            if isinstance(program[i]["args"][arg], str):
                program[i]["args"][arg] = program[i]["args"][arg].replace("r", "")

    for i in range(len(data)):
        data[i] = {"opcode": "DATA","args": [data[i]]}

    united_memory = program + data
    return united_memory


def translate_to_struct(text) -> list:
    text = translate_stage_1(text)

    data_tokens, instruction_tokens = translate_stage_2(text)

    data, data_labels, code, code_labels = translate_stage_3(data_tokens, instruction_tokens)

    program = code
    for word_idx, word in enumerate(program):
        if isinstance(word, dict):
            for arg_idx, arg in enumerate(word["args"]):
                if arg in data_labels:
                    program[word_idx]["args"][arg_idx] = data_labels[arg] + len(code)
                elif arg in code_labels:
                    program[word_idx]["args"][arg_idx] = code_labels[arg]

    memory = translate_stage_4(program, data)

    return memory


def main(args):
    assert len(args) == 2, \
        "Wrong arguments: translator.py <input_file> <target_code_file>"

    source, target = args
    with open(source, "rt", encoding="utf-8") as f:
        source = f.read()

    united_memory = translate_to_struct(source)
    write_code(target, united_memory)


if __name__ == '__main__':
    main(sys.argv[1:])
