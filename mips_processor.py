class MIPSProcessor:
    def __init__(self, start_pc=0x00400000):
        self.registers = [0] * 32
        self.start_pc = start_pc
        self.pc = start_pc
        self.instruction_memory = []
        self.data_memory = {}
        self.halted = False
        
        self.if_id = {}
        self.id_ex = {}
        self.ex_mem = {}
        self.mem_wb = {}

    def load_program(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if len(line) != 0:
                    bin_instr = bin(int(line, 16))[2:].zfill(32)
                    self.instruction_memory.append(bin_instr)

    def load_data(self, filename, start_address=0x10010000):
        with open(filename, 'r') as f:
            addr = start_address
            for line in f:
                line = line.strip()
                if len(line) != 0:
                    val = int(line, 16)
                    self.data_memory[addr] = val
                    addr += 4



    def print_state(self):
        print(f"CYCLE STATE : PC={hex(self.pc)}")
        print("Pipeline Stages :")
        print(f"  IF/ID : {self.if_id}")
        
        id_ex_summary = {k: v for k, v in self.id_ex.items()}
        if id_ex_summary:
             print(f"  ID/EX : {id_ex_summary}")

             
        print(f"EX/MEM: {self.ex_mem}")
        print(f"MEM/WB: {self.mem_wb}")

        print("Registers:")
    
        for i in range(32):
            reg_val = self.registers[i]
            print("R" + str(i) + ":" + hex(reg_val), end=" ")
            
            if (i + 1) % 8 == 0:
                print()
        
        sorted_mem = {}
        for k,v in sorted(self.data_memory.items()) : 
            if v != 0:
                sorted_mem[hex(k)] = hex(v)

        print("Data Memory:")
        print(sorted_mem)

    def _IF(self):
        idx = (self.pc - self.start_pc) // 4
        if 0 <= idx < len(self.instruction_memory):
            instr = self.instruction_memory[idx]
            self.if_id['instr'] = instr
            self.if_id['pc_next'] = self.pc + 4
        else:
            self.if_id['instr'] = '0' * 32
            self.if_id['pc_next'] = self.pc + 4

    def _ID(self):
        if not self.if_id:
            return

        instr = self.if_id.get('instr', '0' * 32)
        pc_next = self.if_id.get('pc_next', self.pc + 4)
        
        opcode = int(instr[0:6], 2)
        rs = int(instr[6:11], 2)
        rt = int(instr[11:16], 2)
        rd = int(instr[16:21], 2)
        shamt = int(instr[21:26], 2)
        funct = int(instr[26:32], 2)
        imm = int(instr[16:32], 2)
        
        if instr[16] == '1':
            imm_se = imm - (1 << 16)
        else:
            imm_se = imm
            
        address = int(instr[6:32], 2)
        
        val_rs = self.registers[rs]
        val_rt = self.registers[rt]
        
        self.id_ex = {
            'opcode': opcode,
            'rs': rs,
            'rt': rt,
            'rd': rd,
            'shamt': shamt,
            'funct': funct,
            'imm': imm,
            'imm_se': imm_se,
            'address': address,
            'val_rs': val_rs,
            'val_rt': val_rt,
            'pc_next': pc_next,
            'instr': instr
        }

    def _EX(self):
        if not self.id_ex:
            return

        opcode = self.id_ex['opcode']
        funct = self.id_ex['funct']
        shamt = self.id_ex['shamt']
        val_rs = self.id_ex['val_rs']
        val_rt = self.id_ex['val_rt']
        imm_se = self.id_ex['imm_se']
        imm = self.id_ex['imm']
        rd = self.id_ex['rd']
        rt = self.id_ex['rt']
        address = self.id_ex['address']
        pc_next = self.id_ex['pc_next']
        
        alu_result = 0
        mem_write_data = val_rt
        mem_read = False
        mem_write = False
        reg_write = False
        reg_dst = rt
        
        branch = False
        jump = False
        pc_target = 0
        
        if opcode == 0:
            reg_dst = rd
            reg_write = True
            
            if funct == 32 or funct == 33: # add / addu
                alu_result = (val_rs + val_rt) & 0xFFFFFFFF
            elif funct == 34 or funct == 35: # sub / subu
                alu_result = (val_rs - val_rt) & 0xFFFFFFFF
            elif funct == 36: # and
                alu_result = val_rs & val_rt
            elif funct == 37: # or
                alu_result = val_rs | val_rt
            elif funct == 38: # xor
                alu_result = val_rs ^ val_rt
            elif funct == 39: # nor
                alu_result = ~(val_rs | val_rt) & 0xFFFFFFFF
            elif funct == 42: # slt
                s_rs = val_rs if val_rs < 0x80000000 else val_rs - 0x100000000
                s_rt = val_rt if val_rt < 0x80000000 else val_rt - 0x100000000
                alu_result = 1 if s_rs < s_rt else 0
            elif funct == 43: # sltu
                alu_result = 1 if val_rs < val_rt else 0
            elif funct == 0: # sll
                if self.id_ex['instr'] == '0' * 32: 
                    reg_write = False
                else:
                    alu_result = (val_rt << shamt) & 0xFFFFFFFF
            elif funct == 2: # srl
                alu_result = (val_rt >> shamt) & 0xFFFFFFFF
            elif funct == 8: # jr
                jump = True
                pc_target = val_rs
                reg_write = False
            elif funct == 12: # syscall
                reg_write = False
                if self.registers[2] == 10:
                    self.halted = True
                
        else:
            if opcode == 2: # j
                jump = True
                pc_target = (pc_next & 0xF0000000) | (address << 2)
            elif opcode == 3: # jal
                jump = True
                pc_target = (pc_next & 0xF0000000) | (address << 2)
                reg_write = True
                reg_dst = 31
                alu_result = pc_next
            elif opcode == 4: # beq
                if val_rs == val_rt:
                    branch = True
                    pc_target = pc_next + (imm_se << 2)
            elif opcode == 5: # bne
                if val_rs != val_rt:
                    branch = True
                    pc_target = pc_next + (imm_se << 2)
            elif opcode == 8 or opcode == 9: # addi / addiu
                alu_result = (val_rs + imm_se) & 0xFFFFFFFF
                reg_write = True
            elif opcode == 12: # andi
                alu_result = val_rs & imm
                reg_write = True
            elif opcode == 13: # ori
                alu_result = val_rs | imm
                reg_write = True
            elif opcode == 14: # xori
                alu_result = val_rs ^ imm
                reg_write = True
            elif opcode == 10: # slti
                s_rs = val_rs if val_rs < 0x80000000 else val_rs - 0x100000000
                alu_result = 1 if s_rs < imm_se else 0
                reg_write = True
            elif opcode == 11: # sltiu
                imm_u = imm_se if imm_se >= 0 else imm_se + 0x100000000
                alu_result = 1 if val_rs < imm_u else 0
                reg_write = True
            elif opcode == 15: # lui
                alu_result = (imm << 16) & 0xFFFFFFFF
                reg_write = True
            elif opcode == 35: # lw
                alu_result = (val_rs + imm_se) & 0xFFFFFFFF
                mem_read = True
                reg_write = True
            elif opcode == 43: # sw
                alu_result = (val_rs + imm_se) & 0xFFFFFFFF
                mem_write = True
                
        self.ex_mem = {
            'alu_result': alu_result,
            'mem_write_data': mem_write_data,
            'mem_read': mem_read,
            'mem_write': mem_write,
            'reg_write': reg_write,
            'reg_dst': reg_dst,
            'branch': branch,
            'jump': jump,
            'pc_target': pc_target
        }

    def _Mem(self):
        if not self.ex_mem:
            return

        mem_read = self.ex_mem['mem_read']
        mem_write = self.ex_mem['mem_write']
        address = self.ex_mem['alu_result']
        write_data = self.ex_mem['mem_write_data']
        
        mem_data = 0
        if mem_read:
            mem_data = self.data_memory.get(address, 0)
        if mem_write:
            self.data_memory[address] = write_data
            
        self.mem_wb = {
            'mem_data': mem_data,
            'alu_result': address,
            'reg_write': self.ex_mem['reg_write'],
            'reg_dst': self.ex_mem['reg_dst'],
            'mem_read': mem_read
        }

        if self.ex_mem['branch'] or self.ex_mem['jump']:
            self.pc = self.ex_mem['pc_target']
        else:
            self.pc = self.if_id['pc_next']

    def _WB(self):
        if not self.mem_wb:
            return

        reg_write = self.mem_wb['reg_write']
        reg_dst = self.mem_wb['reg_dst']
        
        if reg_write and reg_dst != 0:
            if self.mem_wb['mem_read']:
                self.registers[reg_dst] = self.mem_wb['mem_data']
            else:
                self.registers[reg_dst] = self.mem_wb['alu_result']

    def step(self):
        if not self.halted:
            self._IF()
            if not self.halted:
                self._ID()
                self._EX()
                self._Mem()
                self._WB()

    def run(self):
        print("Starting execution...")
        cycles = 0
        while not self.halted :
            self.step()
            cycles += 1
            if not self.halted:
                self.print_state()
                
        print(f"Execution finished in {cycles} cycles.")
        self.print_state()

    
text_filename = "machine_code.txt"
data_filename = "data_code.txt"

processor = MIPSProcessor(start_pc=0x00400000)
processor.load_program(text_filename)
processor.load_data(data_filename, start_address=0x10010000)

initial_array = []
for i in range(5) :
    initial_array.append(processor.data_memory.get(0x10010000 + i*4, 0))

processor.run()

final_array = []
for i in range(5) :
    final_array.append(processor.data_memory.get(0x10010000 + i*4, 0))

print("           FINAL RESULTS          ")
print(f"Initial Array Values : {initial_array}")
print(f"Final Sorted Array   : {final_array}")
