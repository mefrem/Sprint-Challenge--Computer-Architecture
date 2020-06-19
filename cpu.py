"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # Init 8 registrars
        self.reg = [0] * 8
        # Init our program counter
        self.pc = 0
        # Init our instruction reader
        self.ir = 0
        # Init memory with 256 bits
        self.ram = [0b0] * 256
        # Per our spec, reg 7 = 0xF4
        self.reg[7] = 0xF4
        self.sp = self.reg[7]


    def load(self):
        """Load a program into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        program = [
            # From print8.ls8
            0b10000010, # LDI R0,8
            0b00000000,
            0b00001000,
            0b01000111, # PRN R0
            0b00000000,
            0b00000001, # HLT
        ]

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def load(self):
        # Starting at beginning of RAM
        pointer = 0

        # Program to run comes from sys.argv[1]
        with open(sys.argv[1]) as f:
            for line in f:
                # Take leading script before # comment and strip whitespace
                opcode = line.split("#")[0].strip()
                if opcode == '':
                    continue
                value = int(opcode, 2)
                self.ram[pointer] = value
                pointer += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
             self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
             self.reg[reg_a] *= self.reg[reg_b]
        #if the comparison register is called
        elif op == 'CMP':
            #The flag parameter according to the spec:
            #FL bits: 00000LGE
            if self.reg[reg_a] == self.reg[reg_b]:
                #according to spec if values are equal...
                #If they are equal, set the Equal E flag to 1, otherwise set it to 0.
                self.flag = 0b00000001
            #if a is less than b
            elif self.reg[reg_a] < self.reg[reg_b]:
                #set the less than flag to 1
                self.flag = 0b00000100
            elif self.reg[reg_a] > self.reg[reg_b]:
                #set the greater than flag to 1
                self.flag = 0b00000010
        else:
            raise Exception("Unsupported ALU operation")
    
    def ram_read(self, address):
        return self.ram[address]
        
    def ram_write(self, value, address):
        self.ram[address] = value

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        # Our instruction registrar takes operand of program counter
        running = True
        while running:
            # Our instruction register set to ram indexed at program counter 
            self.ir = self.ram[self.pc]

            # HALT command
            if self.ir == 0b00000001:
                running = False
            
            # LDI, or Load Immediate; set specified register to specific value
            elif self.ir == 0b10000010:
                operand_a = self.ram[self.pc + 1] # Our register of interest
                operand_b = self.ram[self.pc + 2] # Value for that register
                
                self.reg[operand_a] = operand_b
                # Increment program counter by 3 steps in RAM
                self.pc += 3
            
            # PRN, or Print; printing value at given register
            elif self.ir == 0b01000111:
                print(self.reg[self.ram[self.pc + 1]])
                self.pc += 2
            
            # MULT, or Multiply; multiply values inside 2 registers provided
            elif self.ir == 0b10100010:    
                operand_a = self.ram[self.pc + 1] # register 1
                operand_b = self.ram[self.pc + 2] # register 2
                self.alu("MUL", operand_a, operand_b)
                self.pc += 3
            
            # ADD, or Addition; add values at locations designated by next two addresses
            elif self.ir == 0b10100000:
                operand_a = self.ram[self.pc + 1]
                operand_b = self.ram[self.pc + 2]
                self.alu('ADD',operand_a, operand_b)
                self.pc +=3
            
            # PUSH, or Push; Push a registrar's value to the stack
            elif self.ir == 0b01000101:
                reg = self.ram[self.pc+1] # The register of interest
                val = self.reg[reg] # That register's value
                # Decrement the stack pointer
                self.sp -= 1
                #push the value pulled from the registrar to the stack
                self.ram[self.sp] = val
                self.pc += 2

            # POP, or Pop; Pop a registrar's value from the stack
            elif self.ir == 0b01000110:
                reg = self.ram[self.pc+1] # The register of interest that will hold popped value
                value = self.ram[self.sp] # The value that's popped
                self.reg[reg] = value # Assigning value to register
                # Incrementing the stack pointer      
                self.sp += 1
                self.pc +=2

            # CALL, or Call; Call a subroutine
            elif self.ir == 0b01010000:
                return_address = self.pc + 2 # The register slot holding our subroutine's returned value
                self.sp -= 1 # Decrementing the stack pointer
                self.ram[self.sp] = return_address # Our stack is now the return address
                reg = self.ram[self.pc+1] # The register holding the called function 
                subroutine_location = self.reg[reg] # Grabbing subrouting location
                self.pc = subroutine_location # Program counter is now set to execute subroutine

            # RET, or Return; Return from subroutine
            elif self.ir == 0b00010001:
                return_address = self.ram[self.sp] # Taking value from top of stack (our subroutine value)
                self.sp += 1 # Increment the stack pointer, return to code prior to call
                self.pc = return_address # Set program counter to return address

            # CMP, or Compare; Compare the next two values
            elif self.ir == 0b10100111:
                operand_a = self.ram_read(self.pc + 1)
                operand_b = self.ram_read(self.pc + 2)
                self.alu("CMP", operand_a, operand_b) #call ALU function's CMP command
                self.pc += 3

            # JMP, or Jump; Jump the Program Counter to another location    
            elif self.ir == 0b01010100:
                address = self.ram_read(self.pc + 1)
                self.pc = self.reg[address]

            # JEQ, or Jump if Equal; If equal flag is set to true, jump to the address stored in the given register
            elif self.ir == 0b01010101:
                address = self.ram_read(self.pc + 1) # Address to travel to
                if self.flag == 0b00000001: # If flag is equal
                    self.pc = self.reg[address] # Jump to aforementioned address
                else:
                    self.pc +=2 # If not equal, skip command entirely
            
            
            # JNE, or Jump if Not Equal; If equal flag is set to false, jump to another address
            elif self.ir == 0b01010110:
                #JNE FUNCTION
                #the next value in the PC is the address to go to
                #IF CMP function did NOT return an equal flag
                address = self.ram_read(self.pc +1) # Address to travel to
                if self.flag != 0b00000001:
                    self.pc = self.reg[address] # Jump to aforementioned address
                else:
                    self.pc += 2 # Otherwise skip


            # If instruction unknown, print location for bug fixing
            else:
                print(f"Unknown instruction {self.ir} at address {self.pc}")
                sys.exit(1)
