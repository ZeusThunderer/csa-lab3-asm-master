"""
isa
"""
import json
from enum import Enum


class Opcode(str, Enum):
    """
    Opcode
    """
    DATA = "DATA"
    
    LD = 'LD'  # A <- [B]
    SW = 'SW'  # [A] <- B

    JMP = 'JMP'  # unconditional transition
    # a,b,i
    BEQ = "BEQ"  # Branch if Equal (A == B)
    BNQ = "BNQ" # not equals A != B
    BLT = "BLT"  # Branch if Less than (A < B)

    ADD = 'ADD'
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    REM = "REM"

    HLT = 'HLT'

    def __str__(self):
        return str(self.value)


ops_gr = {
    "mem": {
        Opcode.LD,
        Opcode.SW,
    },
    "branch": {
        Opcode.JMP,
        Opcode.BEQ,
        Opcode.BLT,
    },
    "arith": {
        Opcode.ADD,
        Opcode.SUB,
        Opcode.MUL,
        Opcode.DIV,
        Opcode.REM,
    }
}


def write_code(filename: str, memory: list):
    with open(filename, "w", encoding="utf-8") as file:
        # Почему не: `file.write(json.dumps(code, indent=4))`?
        # Чтобы одна инструкция была на одну строку.
        buf = []
        for instr in memory:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename: str):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        if "opcode" in instr:
            instr["opcode"] = Opcode(instr["opcode"])

    return code
