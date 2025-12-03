#! python
# (c) DL, UTA, 2009 - 2016
import sys, string, time

wordsize = 31  # everything is a word. old val (24)
numregbits = 3  # actually +1, msb is indirect bit
opcodesize = 7  # old val (5)

addrsize = wordsize - (opcodesize + numregbits + 1)  # num bits in address
memloadsize = 1024  # change this for larger programs
numregs = 2 ** numregbits

regmask = (numregs * 2) - 1  # including indirect bit
# addmask = (2**(wordsize - addrsize)) -1            # maybe error?
nummask = (2 ** (wordsize)) - 1

opcposition = wordsize - (opcodesize + 1)  # shift value to position opcode
reg1position = opcposition - (numregbits + 1)  # first register position
reg2position = reg1position - (numregbits + 1)
memaddrimmedposition = reg2position  # mem address or immediate same place as reg2
realmemsize = memloadsize * 1  # this is memory size, should be (much) bigger than a program

# address mask update, coz mask the low address/immediate field
addmask = (1 << memaddrimmedposition) - 1

# memory management regs
codeseg = numregs - 1  # last reg is a code segment pointer
dataseg = numregs - 2  # next to last reg is a data segment pointer

# ints and traps
trapreglink = numregs - 3  # store return value here
trapval = numregs - 4  # pass which trap/int
mem = [0] * realmemsize  # this is memory, init to 0
reg = [0] * numregs  # registers
clock = 1  # clock starts ticking
ic = 0  # instruction count
numcoderefs = 0  # number of times instructions read
numdatarefs = 0  # number of times data read
starttime = time.time()
curtime = starttime

# Part 2: Hazard model (5-stage) & 1-bit branch predictor
WB_LAT = 5  # cycles until a dest register becomes visible (WB stage)
reg_ready = [0] * numregs  # cycle when each reg's value is ready
hazard_stalls = 0 # total cycles stalled for hazards
hazard_events = [] # (pc, kind, regs, stall)
IND_BIT = (1 << numregbits)

def stall_until(target_cycle, reason, regs):
    """If clock < target_cycle, stall and log it."""
    global clock, hazard_stalls
    if clock < target_cycle:
        stall = target_cycle - clock
        clock += stall
        hazard_stalls += stall
        # pc is the instruction we just fetched: ip-1
        hazard_events.append((ip - 1, reason, list(regs), stall))
        return stall
    return 0

def mark_write(dest_reg):
    """Mark when dest register will be ready (after WB)."""
    if dest_reg is not None:
        reg_ready[dest_reg] = clock + WB_LAT

# ---- 1-bit branch predictor ----
BP_ENTRIES = 64
BP_MISPRED_PENALTY = 3  # configurable control hazard penalty
bp_table = [0] * BP_ENTRIES   # 0=not-taken, 1=taken
bp_hits = 0
bp_misses = 0

def bp_index(pc):  # pc is word address of the branch instruction
    return pc & (BP_ENTRIES - 1)

PHYS_MASK = (1 << numregbits) - 1
def phys_reg(r):
    # strip indirect bit to get the base register index (0..numregs-1)
    return r & PHYS_MASK
# ---

def startexechere(p):
    # start execution at this address
    reg[codeseg] = p


def loadmem():  # get binary load image
    curaddr = 0
    for line in open("a.out", 'r').readlines():
        token = line.lower().split()  # first token on each line is mem word, ignore rest
        if token[0] == 'go':
            startexechere(int(token[1]))
        else:
            mem[curaddr] = int(token[0], 0)
            curaddr = curaddr + 1


def getcodemem(a):
    # get code memory at this address
    memval = mem[a + reg[codeseg]]
    return (memval)


def getdatamem(a):
    # get code memory at this address
    memval = mem[a + reg[dataseg]]
    return (memval)


def getregval(r):
    # get reg or indirect value
    if (r & (1 << numregbits)) == 0:  # not indirect
        rval = reg[r]
    else:
        rval = getdatamem(reg[r - numregs])  # indirect data with mem address
    return rval


def checkres(v1, v2, res):
    v1sign = (v1 >> (wordsize - 1)) & 1
    v2sign = (v2 >> (wordsize - 1)) & 1
    ressign = (res >> (wordsize - 1)) & 1
    if v1sign & v2sign & (not ressign):
        return 1
    elif (not v1sign) & (not v2sign) & (ressign):
        return 1
    else:
        return 0


def dumpstate(d):
    if d == 1:
        print(reg)
    elif d == 2:
        print(mem)
    elif d == 3:
        print('clock=', clock, 'IC=', ic, 'Coderefs=', numcoderefs, 'Datarefs=', numdatarefs, 'Start Time=', starttime,
              'Currently=', time.time())

def dump_task4(vec_base, N, sum_reg_idx=1):
    """
    Debug helper for Task 4:
    - vec_base: base address of result vector C (word address)
    - N: number of elements in the vector
    - sum_reg_idx: which register holds the scalar sum (default r1)
    """
    print('--- Task 4 debug dump ---')
    # Print the sum register
    sum_val = reg[sum_reg_idx]
    print(f"r{sum_reg_idx} (vector sum) = {sum_val} (0x{sum_val:x})")

    # Print vector contents directly from memory array
    base = vec_base + reg[dataseg]  # include data segment offset
    print(f"Vector C at logical address {vec_base}, length {N}:")
    for i in range(N):
        addr = base + i
        val = mem[addr]
        print(f"  C[{i}] @ mem[{addr}] = {val} (0x{val:x})")
    print('-------------------------')


def trap(t, a=None):
    # unusual cases
    # trap 0 illegal instruction
    # trap 1 arithmetic overflow
    # trap 2 sys call
    # trap 3+ user
    rl = trapreglink  # store return value here
    rv = trapval
    if (t == 0) | (t == 1):
        dumpstate(1)
        dumpstate(2)
        dumpstate(3)
    elif t == 2:  # sys call, reg trapval has a parameter
        what = reg[trapval]
        if what == 1:
            a = a  # elapsed time
    return (-1, -1)
    return (rv, rl)


# part 1 codes here
# def getcodemem(a):
#     # instruction fetch
#     global numcoderefs
#     numcoderefs += 1
#     return mem[a + reg[codeseg]]
#
# def getdatamem(a):
#     # data read
#     global numdatarefs
#     numdatarefs += 1
#     return mem[a + reg[dataseg]]
#
# def setdatamem(a, val):
#     # data write (store)
#     global numdatarefs
#     numdatarefs += 1
#     mem[a + reg[dataseg]] = val & nummask

# ---- Part 3: Cache & Main memory class
# Latencies
LAT_L1  = 1
LAT_L2  = 4
LAT_MEM = 25

class MainMem:
    def __init__(self, mem_array, name="MEM"):
        self.mem = mem_array
        self.name = name
        self.accesses = 0

    def read_word(self, addr):
        self.accesses += 1
        add_cycles(LAT_MEM)
        return self.mem[addr & (len(self.mem)-1)]

    def write_word(self, addr, val):
        self.accesses += 1
        add_cycles(LAT_MEM)
        self.mem[addr & (len(self.mem)-1)] = val & nummask

    def read_block(self, base_addr, block_words):
        # pull a whole block from memory
        return [self.read_word(base_addr + i) for i in range(block_words)]

class Cache:
    """
    Generic cache: supports direct-mapped (ways=1) and set-assoc (ways>1).
    LRU replacement. Write-allocate, write-through to lower level.
    """
    def __init__(self, block_words, lines, ways=1, name="L1", lat=1, lower=None):
        assert lines % ways == 0
        self.block_words = block_words      # num of words per cache block
        self.ways = ways                    # ways == 1 -> direct mapped. ways > 1 -> set-associative
        self.sets = lines // ways           # num of sets
        self.name = name
        self.lat = lat
        self.lower = lower                  # pointer to the next level (another cache or mainmem)
        self.tags = [[{"valid": False, "tag": None, "lru": 0, "data": [0]*block_words}
                      for _ in range(ways)] for _ in range(self.sets)]
        self.accesses = 0
        self.hits = 0

    def _set_idx_tag(self, word_addr):
        block_addr = word_addr // self.block_words
        set_idx = block_addr % self.sets
        tag = block_addr // self.sets
        word_off = word_addr % self.block_words
        return set_idx, tag, word_off, block_addr

    def _touch(self, set_idx, way):
        # update LRU
        for line in self.tags[set_idx]:
            line["lru"] += 1
        self.tags[set_idx][way]["lru"] = 0

    def _read_block_from_lower(self, base_addr, block_words):
        # Works whether lower is another Cache or MainMem
        if hasattr(self.lower, "read_block"):
            return self.lower.read_block(base_addr, block_words)
        else:
            # lower is a Cache: fetch words one by one via access()
            return [self.lower.access(base_addr + i, is_load=True) for i in range(block_words)]

    def access(self, word_addr, is_load=True, write_val=None):
        self.accesses += 1
        set_idx, tag, word_off, block_addr = self._set_idx_tag(word_addr)

        # tag lookup latency
        add_cycles(self.lat)

        # hit?
        hit_way = None
        for w, line in enumerate(self.tags[set_idx]):
            if line["valid"] and line["tag"] == tag:
                hit_way = w
                break

        if hit_way is not None:
            self.hits += 1
            self._touch(set_idx, hit_way)
            line = self.tags[set_idx][hit_way]
            if is_load:
                return line["data"][word_off]
            else:
                # write-allocate + write-through
                line["data"][word_off] = write_val & nummask
                if self.lower:
                    addr = block_addr * self.block_words + word_off
                    if hasattr(self.lower, "write_word"):
                        self.lower.write_word(addr, write_val & nummask)
                    else:
                        self.lower.access(addr, is_load=False, write_val=write_val & nummask)
                return None

        # miss: fetch block from lower
        victim = max(self.tags[set_idx], key=lambda L: L["lru"])
        if self.lower:
            base = block_addr * self.block_words
            block = self._read_block_from_lower(base, self.block_words)
        else:
            block = [0] * self.block_words

        victim.update({"valid": True, "tag": tag, "lru": 0, "data": block})

        if is_load:
            return victim["data"][word_off]
        else:
            victim["data"][word_off] = write_val & nummask
            if self.lower:
                addr = block_addr * self.block_words + word_off
                if hasattr(self.lower, "write_word"):
                    self.lower.write_word(addr, write_val & nummask)
                else:
                    self.lower.access(addr, is_load=False, write_val=write_val & nummask)

            return None

# Select one:
#   "U_DM_2x4", "U_DM_4x4", "U_DM_2x8",
#   "SPLIT_I2x2_D2x2", "SPLIT_I4x2_D4x4",
#   "U_SA2_2x8"
CACHE_MODE = "SPLIT_I4x2_D2x2"
USE_L2 = True  # set True to enable L2 = 8x8 unified

# Build hierarchy
mainmem = MainMem(mem, "MEM")

l2 = None
if USE_L2:
    # L2: 8x8 unified, direct-mapped (ways=1)
    l2 = Cache(block_words=8, lines=8, ways=1, name="L2", lat=LAT_L2, lower=mainmem)

l1i = l1d = l1u = None
if CACHE_MODE == "U_DM_2x4":
    l1u = Cache(2, 4, 1, "L1U DM 2x4", LAT_L1, lower=(l2 or mainmem))
elif CACHE_MODE == "U_DM_4x4":
    l1u = Cache(4, 4, 1, "L1U DM 4x4", LAT_L1, lower=(l2 or mainmem))
elif CACHE_MODE == "U_DM_2x8":
    l1u = Cache(2, 8, 1, "L1U DM 2x8", LAT_L1, lower=(l2 or mainmem))
elif CACHE_MODE == "U_SA2_2x8":
    l1u = Cache(2, 8, 2, "L1U 2-way 2x8", LAT_L1, lower=(l2 or mainmem))
elif CACHE_MODE == "SPLIT_I2x2_D2x2":
    l1i = Cache(2, 2, 1, "L1I DM 2x2", LAT_L1, lower=(l2 or mainmem))
    l1d = Cache(2, 2, 1, "L1D DM 2x2", LAT_L1, lower=(l2 or mainmem))
elif CACHE_MODE == "SPLIT_I4x2_D4x4":
    l1i = Cache(4, 2, 1, "L1I DM 4x2", LAT_L1, lower=(l2 or mainmem))
    l1d = Cache(4, 4, 1, "L1D DM 4x4", LAT_L1, lower=(l2 or mainmem))
else:
    # default to unified 2x4
    l1u = Cache(2, 4, 1, "L1U DM 2x4", LAT_L1, lower=(l2 or mainmem))


def getcodemem(a):
    # instruction fetch
    global numcoderefs
    numcoderefs += 1
    word_addr = a + reg[codeseg]
    if l1u is not None:
        return l1u.access(word_addr, is_load=True)
    else:
        return l1i.access(word_addr, is_load=True)

def getdatamem(a):
    # data load
    global numdatarefs
    numdatarefs += 1
    word_addr = a + reg[dataseg]
    if l1u is not None:
        return l1u.access(word_addr, is_load=True)
    else:
        return l1d.access(word_addr, is_load=True)

def setdatamem(a, val):
    # data store (write-allocate + write-through)
    global numdatarefs
    numdatarefs += 1
    word_addr = a + reg[dataseg]
    if l1u is not None:
        l1u.access(word_addr, is_load=False, write_val=val & nummask)
    else:
        l1d.access(word_addr, is_load=False, write_val=val & nummask)


# ---- Part 3: Cache config & helpers ----
def add_cycles(c):
    # add extra latency on top of your base 5/cycle model
    global clock
    if c > 0:
        clock += c

def _cache_report(c):
    if c is None or c.accesses == 0:
        return
    hr = (100.0 * c.hits / c.accesses) if c.accesses else 0.0
    print(f"{c.name}: accesses={c.accesses}, hits={c.hits}, hit%={hr:.1f}")

# opcode type (1 reg, 2 reg, reg+addr, immed), mnemonic
opcodes = {1: (2, 'add'), 2: (2, 'sub'),
           3: (1, 'dec'), 4: (1, 'inc'),
           7: (3, 'ld'), 8: (3, 'st'), 9: (3, 'ldi'),
           12: (3, 'bnz'), 13: (3, 'brl'),
           14: (1, 'ret'),
           16: (3, 'int'),
           17: (3, 'vadd'), 18: (3, 'vsum')}  # Part 4

startexechere(0)  # start execution here if no "go"
loadmem()  # load binary executable
ip = 0  # start execution at codeseg location 0
# while instruction is not halt
while 1:
    ir = getcodemem(ip)  # - fetch
    ip = ip + 1
    opcode = ir >> opcposition  # - decode
    reg1 = (ir >> reg1position) & regmask
    reg2 = (ir >> reg2position) & regmask
    addr = ir & addmask
    ic = ic + 1
    # - operand fetch
    if opcode not in opcodes:
        tval, treg = trap(0)
        if tval == -1:  # illegal instruction
            break
    memdata = 0  # contents of memory for loads
    if opcodes[opcode][0] == 1:  # dec, inc, ret type
        operand1 = getregval(reg1)  # fetch operands
    elif opcodes[opcode][0] == 2:  # add, sub type
        operand1 = getregval(reg1)  # fetch operands
        operand2 = getregval(reg2)
    elif opcodes[opcode][0] == 3:  # ld, st, br type
        operand1 = getregval(reg1)  # fetch operands
        operand2 = addr
    elif opcodes[opcode][0] == 0:  # ? type
        break

    # ===== Part 2: data hazard detection (RAW/WAW) =====
    # Identify source and destination regs precisely by opcode
    sources = []
    dest = None

    if opcode in (1, 2):  # add/sub: r1 <= f(r1, r2)
        sources = [reg1, reg2]
        dest = reg1
    elif opcode in (3, 4):  # dec/inc: r1 <= f(r1)
        sources = [reg1]
        dest = reg1
    elif opcode == 7:  # ld: r1 <= MEM[addr]
        sources = []  # (no true reg source dep for ld)
        dest = reg1
    elif opcode == 8:  # st: MEM[addr] <= r1
        sources = [reg1]
        dest = None
    elif opcode == 9:  # ldi: r1 <= imm
        sources = []
        dest = reg1
    elif opcode == 12:  # bnz r1, addr    (reads r1)
        sources = [reg1]
        dest = None
    elif opcode == 13:  # brl r1, addr    (writes link to r1)
        sources = []
        dest = reg1
    elif opcode == 14:  # ret r1          (reads r1)
        sources = [reg1]
        dest = None
    elif opcode == 16:  # int/sys r1      (reads and then writes r1)
        sources = [reg1]
        dest = reg1
    elif opcode == 17:  # vadd r1, addr  (vector add, result in reg1)
        sources = []    # params in memory descriptor, not in regs
        dest = reg1
    elif opcode == 18:  # vsum r1, addr  (vector sum, result in reg1)
        sources = []
        dest = reg1

    # convert logical to physical reg indices
    sources_phys = [phys_reg(r) for r in sources]
    dest_phys = None if (dest is None) else phys_reg(dest)

    # RAW: all sources must be ready before we proceed
    if sources_phys:
        need = max(reg_ready[r] for r in sources_phys)
        stall_until(need, "RAW", sources_phys)

    # WAW: don't overlap an outstanding earlier write to the same dest
    if dest_phys is not None:
        stall_until(reg_ready[dest_phys], "WAW", [dest_phys])

    if opcode == 7:  # get data memory for loads
        memdata = getdatamem(operand2)

    # ---- Branch prediction bookkeeping for BNZ (uses current ip as fallthrough) ----
    # pc of this instruction is ip-1 (we incremented ip right after fetch)
    pc = ip - 1
    predicted_taken = None
    predicted_next = None
    if opcode == 12:  # bnz
        idx = bp_index(pc)
        predicted_taken = (bp_table[idx] == 1)
        predicted_next = (operand2 if predicted_taken else ip)  # fallthrough is current

    # execute
    if opcode == 1:  # add
        result = (operand1 + operand2) & nummask
        if checkres(operand1, operand2, result):
            tval, treg = trap(1)
            if (tval == -1):  # overflow
                break
    elif opcode == 2:  # sub
        result = (operand1 - operand2) & nummask
        if checkres(operand1, operand2, result):
            tval, treg = trap(1)
            if tval == -1:  # overflow
                break
    elif opcode == 3:  # dec
        result = operand1 - 1
    elif opcode == 4:  # inc
        result = operand1 + 1
    elif opcode == 7:  # load
        result = memdata
    elif opcode == 8:  # store
        # operand1: value from reg1 (already fetched)
        # operand2: absolute address (low field)
        setdatamem(operand2, operand1)
        result = None  # nothing to write back
    elif opcode == 9:  # load immediate
        result = operand2
    elif opcode == 12:  # conditional branch
        # Actual outcome
        taken = (operand1 != 0)
        actual_next = operand2 if taken else ip
        # Compare to prediction (if we made one)
        if predicted_taken is not None:
            if predicted_next == actual_next:
                bp_hits += 1
            else:
                bp_misses += 1
                clock += BP_MISPRED_PENALTY  # control hazard penalty on mispredict
            # Update predictor to last outcome
            bp_table[bp_index(pc)] = 1 if taken else 0
        ip = actual_next
        result = operand1  # for consistency with your existing code path
    elif opcode == 13:  # branch and link
        result = ip
        ip = operand2
    elif opcode == 14:  # return
        ip = operand1
    elif opcode == 16:  # interrupt/sys call
        result = ip
        tval, treg = trap(reg1)
        if tval == -1:
            break
        reg1 = treg
        ip = operand2
    elif opcode == 17:  # vadd r1, addr  (vector add via descriptor at addr)
        # Descriptor layout at operand2:
        # [0] = A_base
        # [1] = B_base
        # [2] = C_base (destination)
        # [3] = N   (#elements, N < 32)
        desc_base = operand2
        baseA = getdatamem(desc_base + 0)
        baseB = getdatamem(desc_base + 1)
        baseC = getdatamem(desc_base + 2)
        N = getdatamem(desc_base + 3)

        # Perform C[i] = A[i] + B[i] for i = 0..N-1
        for i in range(N):
            a_val = getdatamem(baseA + i)
            b_val = getdatamem(baseB + i)
            c_val = (a_val + b_val) & nummask
            setdatamem(baseC + i, c_val)
            # cost of internal scalar add in 5-stage pipeline
            clock += 5

        # Put destination base in reg1 (optional, but useful)
        result = baseC

    elif opcode == 18:  # vsum r1, addr  (vector sum via descriptor at addr)
        # Descriptor layout at operand2:
        # [0] = C_base
        # [1] = N
        desc_base = operand2
        baseC = getdatamem(desc_base + 0)
        N = getdatamem(desc_base + 1)

        acc = 0
        for i in range(N):
            a_val = getdatamem(baseC + i)
            acc = (acc + a_val) & nummask
            clock += 5  # internal scalar add cost

        result = acc

    # write back
    # if ((opcode == 1) | (opcode == 2) |
    #         (opcode == 3) | (opcode == 4)):  # arithmetic
    if opcode in (1, 2, 3, 4, 17, 18):  # arithmetic + vector
        reg[reg1] = result
    elif (opcode == 7) | (opcode == 9):  # loads
        reg[reg1] = result
    elif opcode == 13:  # store return address
        reg[reg1] = result
    elif opcode == 16:  # store return address
        reg[reg1] = result

    # Mark destination ready after WB (for instructions that write a reg)
    if opcode in (1, 2, 3, 4, 7, 9, 13, 16, 17, 18):
        mark_write(phys_reg(reg1))

    # base 5-cycle model for Part 1
    clock += 5
    # end of instruction loop
# end of execution

dump_task4(vec_base=15, N=3, sum_reg_idx=1)

print('=== CAT2 Part 1 stats ===')
print('IC =', ic)
print('Clock =', clock)
print('Code refs =', numcoderefs)
print('Data refs =', numdatarefs)
print('Total mem refs =', numcoderefs + numdatarefs)

print('=== CAT2 Part 2 stats ===')
print('Hazard stalls =', hazard_stalls, 'cycles')
print('Branch predictor: hits =', bp_hits, 'misses =', bp_misses)
# If you want to see a few recent hazards:
for e in hazard_events[-10:]:
    pc, kind, regs, stall = e
    print(f'Hazard @pc={pc}: {kind} regs={regs} stalled {stall} cycles')

print('=== CAT2 Part 3 cache stats ===')
if l1u: _cache_report(l1u)
if l1i: _cache_report(l1i)
if l1d: _cache_report(l1d)
if l2:  _cache_report(l2)
print(f"Main memory accesses={mainmem.accesses}")
