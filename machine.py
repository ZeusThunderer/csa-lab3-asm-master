import logging
from collections import deque
import sys
from enum import Enum

from typing import List, Tuple, Deque

from isa import Opcode, read_code



class ALUOperation(int, Enum):
    ADD = 0
    SUB = 1
    MUL = 2
    DIV = 3
    REM = 4
    MOV = 5
    CMP = 6 


class SelOption(int, Enum):
    ALU = 0
    MEM = 1
    ARG = 2
    REG = 3
    ADR = 4
    INC = 5


class DataPath:
    memory_size: int #mem size
    memory: list #mem
    addr_reg: int # addres register
    input_addr: int # addres of input device
    output_addr: int # addres of output device

    reg_file: list #registers   
    reg_to_read: int #what register to read
    reg_to_write: int # what registes to write
    
    fl_zero: int
    fl_neg: int
    
    left_alu_arg: int
    right_alu_arg: int
    alu_out: int 
    arg_from_decoder: int 
    
    input_buff: list
    output_addr: list

    def __init__(self, data, memory_size: int, input_buff: list):
        assert memory_size > 0, "Memory size should be non-zero"
        assert len(data) <= (memory_size - 2), "Memory size is too small for this data" 
        self.memory_size = memory_size
        self.memory = data + [0] * (memory_size - len(data))
        self.addr_reg = 0
        self.input_addr = memory_size-2
        self.output_addr = memory_size-1
        self.reg_file = [0] * 9
        
        self.fl_zero = 0
        self.fl_neg = 0
        
        self.reg_to_write = 0
        self.reg_to_read = 0

        self.left_alu_arg = 0
        self.right_alu_arg = 0
        self.alu_out = 0
        self.arg_from_decoder = 0;
        
        self.input_buff = input_buff
        self.output_buff = []

    def sel_reg_to_write(self, sel):
        assert 0 <= sel <= 9, "Machine has only 9 registers. (r0 - r8)"
        self.reg_to_write = sel
    def sel_reg_to_read(self, sel):
        assert 0 <= sel <= 9, "Machine has only 9 registers. (r0 - r8)"
        self.reg_to_read = sel

    def latch_addr(self):
        self.addr_reg = self.alu_out % self.memory_size
        
    def latch_reg(self, src: SelOption):
        if src is SelOption.ALU:
            self.reg_file[self.reg_to_write] = self.alu_out
        elif src is SelOption.MEM:
            mem_val = self.memory[self.addr_reg]
            self.reg_file[self.reg_to_write] = int(mem_val["args"][0])
        self.reg_file[0] = 0
            
    def latch_left_alu_arg(self, src: SelOption):
        if src is SelOption.ARG:
            self.left_alu_arg = self.arg_from_decoder
        elif src is SelOption.REG:
            reg_val = self.reg_file[self.reg_to_read]
            self.left_alu_arg = reg_val
        elif src is SelOption.ADR:
            self.left_alu_arg = self.addr_reg
            
    def latch_right_alu_arg(self, src: SelOption):
        if src is SelOption.ARG:
            self.right_alu_arg = self.arg_from_decoder
        elif src is SelOption.REG:
            reg_val = self.reg_file[self.reg_to_read]
            self.right_alu_arg = reg_val
        elif src is SelOption.ADR:
            self.right_alu_arg = self.addr_reg
    
    
    def calculate(self, operation: ALUOperation):
        if operation is ALUOperation.ADD:
            self.alu_out = self.left_alu_arg + self.right_alu_arg
        elif operation is ALUOperation.SUB:
            self.alu_out = self.left_alu_arg - self.right_alu_arg
        elif operation is ALUOperation.MUL:
            self.alu_out = self.left_alu_arg * self.right_alu_arg
        elif operation is ALUOperation.DIV:
            self.alu_out = self.left_alu_arg // self.right_alu_arg
        elif operation is ALUOperation.REM:
            self.alu_out = self.left_alu_arg % self.right_alu_arg
        elif operation is ALUOperation.MOV:
            self.alu_out = self.left_alu_arg
        self.fl_neg = self.alu_out < 0
        self.fl_zero = self.alu_out == 0
    
    def read(self):
        if (self.addr_reg == self.input_addr):
            char_in  = self.input_buff.pop(0)
            self.memory[self.input_addr] =  {"opcode": "DATA","args": [(ord)(char_in)]}
            logging.info("INPUT: {}".format(char_in))
        return self.memory[self.addr_reg]
    
    
    
    def write(self):
        self.memory[self.addr_reg] =  {"opcode": "DATA", "args": [self.alu_out]}
        if self.addr_reg == self.output_addr:
            self.output_buff.append(chr(self.alu_out))
            logging.info("OUTPUT: '{}'".format(chr(self.alu_out))) 
    
   


class ControlUnit:
    data_path: DataPath
    instr_pointer: int
    opcode: Opcode
    
    def __init__(self, data_path):
        self.data_path = data_path
        self.instr_pointer = 0
        self._tick = 0
        self.opcode = None

    def tick(self):
        """Счётчик тактов процессора. Вызывается при переходе на следующий такт."""
        # logging.debug('%s', self)
        self._tick += 1

    def current_tick(self):
        """Возвращает текущий такт."""
        return self._tick

    def latch_ip(self, src: SelOption):
        if src is SelOption.ARG:
            self.instr_pointer = self.data_path.arg_from_decoder
        else:
            self.instr_pointer += 1
        
    
    def decode_and_execute_instruction(self):
        
        instr = self.data_path.memory[self.instr_pointer]
        self.opcode = instr["opcode"]

        if self.opcode is Opcode.HLT:
            raise StopIteration

        elif self.opcode is Opcode.JMP:
            self.data_path.arg_from_decoder = int(instr["args"][0])
            self.latch_ip(SelOption.ARG)
            self.tick()
        
        elif self.opcode is Opcode.LD:
            self.data_path.reg_to_write = int(instr["args"][0])
            if instr["args"][1] == "inp":
                self.data_path.addr_reg = self.data_path.input_addr
                self.data_path.read()
            elif instr["addr_type"] == 1:
                self.data_path.addr_reg =  self.data_path.reg_file[int(instr["args"][1])] 
            else:
                self.data_path.addr_reg = int(instr["args"][1])
            self.data_path.latch_reg(SelOption.MEM)
            self.latch_ip(SelOption.INC)
            self.tick()
            
        elif self.opcode is Opcode.SW:
            self.data_path.reg_to_read = int(instr["args"][1])
            if instr["args"][0] == "out":
                self.data_path.addr_reg = self.data_path.output_addr
            elif instr["addr_type"] == 1:
                self.data_path.addr_reg =  self.data_path.reg_file[int(instr["args"][0])] 
            else:
                self.data_path.addr_reg = int(instr["args"][0])
            self.tick()
            self.data_path.latch_left_alu_arg(SelOption.REG)
            self.data_path.calculate(ALUOperation.MOV)
            self.data_path.write()
            self.latch_ip(SelOption.INC)
            self.tick()
        
        elif self.opcode is Opcode.BEQ:
            self.data_path.reg_to_read = int(instr["args"][0])
            self.data_path.latch_left_alu_arg(SelOption.REG)
            self.tick()
            self.data_path.reg_to_read = int(instr["args"][1])
            self.data_path.latch_right_alu_arg(SelOption.REG)
            self.tick()
            self.data_path.calculate(ALUOperation.SUB)
            if (self.data_path.fl_zero):
                self.data_path.arg_from_decoder = int(instr["args"][2])
                self.latch_ip(SelOption.ARG)
            else:
                self.latch_ip(SelOption.INC)
            self.tick()
        
        elif self.opcode is Opcode.BNQ:
            self.data_path.reg_to_read = int(instr["args"][0])
            self.data_path.latch_left_alu_arg(SelOption.REG)
            self.tick()
            self.data_path.reg_to_read = int(instr["args"][1])
            self.data_path.latch_right_alu_arg(SelOption.REG)
            self.tick()
            self.data_path.calculate(ALUOperation.SUB)
            if not(self.data_path.fl_zero):
                self.data_path.arg_from_decoder = int(instr["args"][2])
                self.latch_ip(SelOption.ARG)
            else:
                self.latch_ip(SelOption.INC)
            self.tick()
        
        elif self.opcode is Opcode.BLT:
            self.data_path.reg_to_read = int(instr["args"][0])
            self.data_path.latch_left_alu_arg(SelOption.REG)
            self.tick()
            self.data_path.reg_to_read = int(instr["args"][1])
            self.data_path.latch_right_alu_arg(SelOption.REG)
            self.tick()
            self.data_path.calculate(ALUOperation.SUB)
            if self.data_path.fl_neg and not(self.data_path.fl_zero):
                self.data_path.arg_from_decoder = int(instr["args"][2])
                self.latch_ip(SelOption.ARG)
            else:
                self.latch_ip(SelOption.INC)
            self.tick()

        elif self.opcode in {Opcode.ADD,Opcode.SUB,Opcode.MUL,Opcode.DIV,Opcode.REM}:
            self.data_path.reg_to_read = int(instr["args"][1])
            self.data_path.latch_left_alu_arg(SelOption.REG)
            self.tick() 
            if instr["addr_type"] == 2:
                self.data_path.arg_from_decoder = int(instr["args"][2])
                self.data_path.latch_right_alu_arg(SelOption.ARG)
            elif instr["addr_type"] == 0:
                self.data_path.reg_to_read = int(instr["args"][2])
                self.data_path.latch_right_alu_arg(SelOption.REG)
            self.tick()
            if self.opcode is Opcode.ADD:
                self.data_path.calculate(ALUOperation.ADD)
            elif self.opcode is Opcode.SUB:
                self.data_path.calculate(ALUOperation.SUB)
            elif self.opcode is Opcode.MUL:
                self.data_path.calculate(ALUOperation.MUL)
            elif self.opcode is Opcode.DIV:
                self.data_path.calculate(ALUOperation.DIV)
            elif self.opcode is Opcode.REM:
                self.data_path.calculate(ALUOperation.REM)
            self.tick()
            self.data_path.reg_to_write = int(instr["args"][0])
            self.data_path.latch_reg(SelOption.ALU)
            self.latch_ip(SelOption.INC)
            self.tick()
                


    def __repr__(self):
        state = (
            "TICK: {} | IP: {} |OPCODE  {}| ADDR: {} | ALU_OUT: {} | R1: {} | R2: {} | R3: {} | "
            "R4: {} | R5: {} | R6: {} | R7: {} | "
            "R8: {} | N: {} | Z: {}"
        ).format(
            self._tick,
            self.instr_pointer,
            self.opcode,
            self.data_path.addr_reg,
            self.data_path.alu_out,
            self.data_path.reg_file[1],
            self.data_path.reg_file[2],
            self.data_path.reg_file[3],
            self.data_path.reg_file[4],
            self.data_path.reg_file[5],
            self.data_path.reg_file[6],
            self.data_path.reg_file[7],
            self.data_path.reg_file[8],
            self.data_path.fl_neg,
            self.data_path.fl_zero,
        )
        return state

def simulation(data: list, memory_size: int, limit: int, input_buff: list):
    """Запуск симуляции процессора.

    Длительность моделирования ограничена количеством выполненных инструкций.
    """
    # logging.info("{ INPUT MESSAGE } [ `%s` ]", "".join(input_tokens))
    # logging.info("{ INPUT TOKENS  } [ %s ]", ",".join(
    #     [str(ord(token)) for token in input_tokens]))
    data_path = DataPath(data,memory_size,input_buff)
    control_unit = ControlUnit(data_path)
    instr_counter = 0
    
    control_unit.__repr__()
    logging.info("%s", control_unit)
    try:
        while True:
            assert instr_counter < limit, "limit exceeded"
            control_unit.decode_and_execute_instruction()
            control_unit.__repr__()
            instr_counter += 1
            logging.info("%s", control_unit)
    except EOFError:
        logging.warning('Input buffer is empty!')
    except StopIteration:
        pass
    logging.info("output_buffer: {}".format(repr("".join(data_path.output_buff))))
    '''for i,mem in enumerate(data_path.memory):
        print(i,mem)'''
    return data_path.output_buff


def main(args):
    code_file, input_file,output_file = args
    data = read_code(code_file)
    input_buff = []
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        for ch in input_text:
            input_buff.append(ch)
    input_buff.append('\0')
    # ... ticks, data_memory_state
    output = simulation(
        data=data,
        memory_size=250,
        limit=400,
        input_buff=input_buff
    )
    with open(output_file,mode='r+',encoding="utf-8") as file:
        file.write("".join(output).replace('\0','\n'));
    return output


if __name__ == '__main__':
    assert len(sys.argv) == 4, "Wrong arguments: machine.py <code_file> <input_file> <output_file>"
    _, code_file, input_file, output_file = sys.argv
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
