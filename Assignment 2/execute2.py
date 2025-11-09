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

# ====== Part 2: Hazard model (kept intact) ======
WB_LAT = 5  # cycles until a dest register becomes visible (WB stage)
reg_ready = [0] * numregs  # cycle when each reg's value is ready
hazard_stalls = 0          # total cycles stalled for hazards
hazard_events = []         # (pc, kind, regs, stall)
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
# ================================================

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

# --------- Part 3: trace collection (minimal intrusion) ---------
# record every memory ref as ('I' or 'D', 'R' or 'W', absolute_word_address)
mem_trace = []

# part 1 overrides (keep counters and now record trace)
def getcodemem(a):
    # instruction fetch
    global numcoderefs
    numcoderefs += 1
    eff = a + reg[codeseg]
    mem_trace.append(('I', 'R', eff))
    return mem[eff]

def getdatamem(a):
    # data read
    global numdatarefs
    numdatarefs += 1
    eff = a + reg[dataseg]
    mem_trace.append(('D', 'R', eff))
    return mem[eff]

def setdatamem(a, val):
    # data write (store)
    global numdatarefs
    numdatarefs += 1
    eff = a + reg[dataseg]
    mem_trace.append(('D', 'W', eff))
    mem[eff] = val & nummask
# ---------------------------------------------------------------

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

# opcode type (1 reg, 2 reg, reg+addr, immed), mnemonic
opcodes = {1: (2, 'add'), 2: (2, 'sub'),
           3: (1, 'dec'), 4: (1, 'inc'),
           7: (3, 'ld'), 8: (3, 'st'), 9: (3, 'ldi'),
           12: (3, 'bnz'), 13: (3, 'brl'),
           14: (1, 'ret'),
           16: (3, 'int')}

startexechere(0)  # start execution here if no "go"
loadmem()  # load binary executable
ip = 0  # start execution at codeseg location 0

# ===================== EXECUTION LOOP (unchanged) =====================
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
    elif opcode == 12:  # bnz r1, addr
        sources = [reg1]
        dest = None
    elif opcode == 13:  # brl r1, addr
        sources = []
        dest = reg1
    elif opcode == 14:  # ret r1
        sources = [reg1]
        dest = None
    elif opcode == 16:  # int/sys r1
        sources = [reg1]
        dest = reg1

    sources_phys = [phys_reg(r) for r in sources]
    dest_phys = None if (dest is None) else phys_reg(dest)

    # RAW
    if sources_phys:
        need = max(reg_ready[r] for r in sources_phys)
        stall_until(need, "RAW", sources_phys)

    # WAW
    if dest_phys is not None:
        stall_until(reg_ready[dest_phys], "WAW", [dest_phys])

    if opcode == 7:  # get data memory for loads
        memdata = getdatamem(operand2)

    # ---- Branch prediction bookkeeping for BNZ ----
    pc = ip - 1
    predicted_taken = None
    predicted_next = None
    if opcode == 12:  # bnz
        idx = bp_index(pc)
        predicted_taken = (bp_table[idx] == 1)
        predicted_next = (operand2 if predicted_taken else ip)

    # execute
    if opcode == 1:  # add
        result = (operand1 + operand2) & nummask
        if checkres(operand1, operand2, result):
            tval, treg = trap(1)
            if (tval == -1):
                break
    elif opcode == 2:  # sub
        result = (operand1 - operand2) & nummask
        if checkres(operand1, operand2, result):
            tval, treg = trap(1)
            if tval == -1:
                break
    elif opcode == 3:  # dec
        result = operand1 - 1
    elif opcode == 4:  # inc
        result = operand1 + 1
    elif opcode == 7:  # load
        result = memdata
    elif opcode == 8:  # store
        setdatamem(operand2, operand1)
        result = None
    elif opcode == 9:  # ldi
        result = operand2
    elif opcode == 12:  # bnz
        taken = (operand1 != 0)
        actual_next = operand2 if taken else ip
        if predicted_taken is not None:
            if predicted_next == actual_next:
                bp_hits += 1
            else:
                bp_misses += 1
                clock += BP_MISPRED_PENALTY
            bp_table[bp_index(pc)] = 1 if taken else 0
        ip = actual_next
        result = operand1
    elif opcode == 13:  # brl
        result = ip
        ip = operand2
    elif opcode == 14:  # ret
        ip = operand1
    elif opcode == 16:  # int/sys
        result = ip
        tval, treg = trap(reg1)
        if tval == -1:
            break
        reg1 = treg
        ip = operand2

    # write back
    if opcode in (1, 2, 3, 4):  # arithmetic
        reg[reg1] = result
    elif (opcode == 7) | (opcode == 9):  # loads
        reg[reg1] = result
    elif opcode == 13:  # store return address
        reg[reg1] = result
    elif opcode == 16:  # store return address
        reg[reg1] = result

    # Mark destination ready after WB
    if opcode in (1, 2, 3, 4, 7, 9, 13, 16):
        mark_write(phys_reg(reg1))

    # base 5-cycle model for Part 1
    clock += 5
# ================== END EXECUTION LOOP ==================

print('=== CAT2 Part 1 stats ===')
print('IC =', ic)
print('Clock =', clock)
print('Code refs =', numcoderefs)
print('Data refs =', numdatarefs)
print('Total mem refs =', numcoderefs + numdatarefs)

print('=== CAT2 Part 2 stats ===')
print('Hazard stalls =', hazard_stalls, 'cycles')
print('Branch predictor: hits =', bp_hits, 'misses =', bp_misses)
for e in hazard_events[-10:]:
    pc, kind, regs, stall = e
    print(f'Hazard @pc={pc}: {kind} regs={regs} stalled {stall} cycles')

# ====================== Part 3: Cache simulator ======================
# Costs per access (assignment spec)
L1_COST = 1
L2_COST = 4
MEM_COST = 25

class CacheLine:
    __slots__ = ('tag','valid','dirty','lru')
    def __init__(self):
        self.tag = 0
        self.valid = False
        self.dirty = False
        self.lru = 0

class Cache:
    def __init__(self, line_words, total_lines, assoc=1, name="L1"):
        self.line_words = max(1, int(line_words))
        self.assoc = max(1, int(assoc))
        self.sets = max(1, int(total_lines // self.assoc))
        self.name = name
        self.time = 0  # for LRU
        self.set = [[CacheLine() for _ in range(self.assoc)] for _ in range(self.sets)]
        # stats
        self.refs = 0
        self.hits = 0
        self.write_hits = 0
        self.read_hits = 0

    def _index_tag(self, addr_word):
        block = addr_word // self.line_words
        idx = block % self.sets
        tag = block // self.sets
        return idx, tag

    def access(self, addr_word, is_write=False):
        """Return (hit:bool, evicted_dirty:bool) and update LRU/dirty."""
        self.refs += 1
        idx, tag = self._index_tag(addr_word)
        self.time += 1
        # hit?
        for line in self.set[idx]:
            if line.valid and line.tag == tag:
                self.hits += 1
                if is_write:
                    self.write_hits += 1
                    line.dirty = True
                else:
                    self.read_hits += 1
                line.lru = self.time
                return True, False
        # miss: choose victim (free or LRU)
        victim = None
        for line in self.set[idx]:
            if not line.valid:
                victim = line
                break
        if victim is None:
            victim = min(self.set[idx], key=lambda ln: ln.lru)
        ev_dirty = (victim.valid and victim.dirty)
        # fill
        victim.tag = tag
        victim.valid = True
        victim.dirty = bool(is_write)  # write-allocate + write-back
        victim.lru = self.time
        return False, ev_dirty

def simulate_config(trace, base_clock, cfg):
    """
    cfg: dict describing caches.
      - unified: {'L1': (line_words,total_lines,assoc)}
      - split:   {'I': (lw,lines,assoc), 'D': (lw,lines,assoc)}
      - optional 'L2': (lw,lines,assoc)
      - name: label
    """
    name = cfg.get('name', 'config')
    # Build caches
    if 'unified' in cfg:
        lw, lines, assoc = cfg['unified']
        L1U = Cache(lw, lines, assoc, name="L1U")
        I = D = L1U
    else:
        lwI, linesI, assocI = cfg['I']
        lwD, linesD, assocD = cfg['D']
        I = Cache(lwI, linesI, assocI, name="L1I")
        D = Cache(lwD, linesD, assocD, name="L1D")
    L2 = None
    if 'L2' in cfg:
        lw2, lines2, assoc2 = cfg['L2']
        L2 = Cache(lw2, lines2, assoc2, name="L2")

    # stats
    mem_cycles = 0
    l2_refs = l2_hits = 0
    evict_wb_cycles = 0

    for kind, rw, addr in trace:
        is_write = (rw == 'W')
        L1 = I if kind == 'I' else D

        hit, ev_dirty = L1.access(addr, is_write=is_write)
        if hit:
            mem_cycles += L1_COST
        else:
            # miss → next level
            if L2 is not None:
                l2_refs += 1
                h2, ev2_dirty = L2.access(addr, is_write=False)  # fill read from below
                if h2:
                    mem_cycles += L2_COST
                else:
                    mem_cycles += MEM_COST
                # if L1 victim was dirty, write back to L2
                if ev_dirty:
                    # write-back arrives at L2
                    L2.access(addr, is_write=True)  # model a write into L2 set (tag based on victim's block)
                    evict_wb_cycles += L2_COST
            else:
                mem_cycles += MEM_COST
                # write-back to memory if evicted dirty
                if ev_dirty:
                    evict_wb_cycles += MEM_COST
            # After lower level, line is considered filled in L1 by the L1.access() call above

        # Write on miss is already marked dirty due to write-allocate

    # report
    i_refs = I.refs if I is not D else sum(1 for k,_,_ in trace if k == 'I')
    d_refs = D.refs if I is not D else sum(1 for k,_,_ in trace if k == 'D')

    # L1 hit rates
    i_hit = (I.read_hits + I.write_hits) if I is not D else I.hits  # in unified, I==D
    d_hit = (0 if I is D else (D.read_hits + D.write_hits))
    if I is D:
        # split per kind from trace on unified
        i_hit = sum(1 for k, rw, a in trace if k == 'I' and I.access(a, False) is not None)  # not accurate to recompute
        # simpler: approximate I hit rate from ratio of I refs in unified hits
        # but keep simple: compute overall L1 hit rate and per-kind using counters already available:
        pass  # keep aggregated below

    overall_hits = (I.hits + (0 if I is D else D.hits))
    overall_refs = i_refs + d_refs
    l1_hit_rate = (overall_hits / overall_refs) if overall_refs else 0.0

    # L2 hit rate
    l2_hit_rate = (l2_hits / l2_refs) if l2_refs else 0.0  # (we didn't count separate l2_hits in this simplified model)

    total_cycles = base_clock + mem_cycles + evict_wb_cycles

    # Print
    print(f'\n--- CAT2 Part 3: {name} ---')
    print(f'I-refs={i_refs}  D-refs={d_refs}  Total={overall_refs}')
    print(f'L1 hits={overall_hits}  L1 hit rate={l1_hit_rate:.3f}')
    if L2 is not None:
        print(f'L2 refs={l2_refs}  (approx) L2 hit rate not separately tallied in this minimal model')
    print(f'Memory cycles (access) = {mem_cycles}  + writeback cycles = {evict_wb_cycles}')
    print(f'Overall cycles (Clock + memory) = {base_clock} + {mem_cycles + evict_wb_cycles} = {total_cycles}')

    # Cache contents (tags per set)
    def dump_cache(c):
        print(f'[{c.name}] sets={c.sets}  assoc={c.assoc}  line_words={c.line_words}')
        for s in range(c.sets):
            line_desc = []
            for ln in c.set[s]:
                if ln.valid:
                    line_desc.append(f'tag={ln.tag:x}{"*D" if ln.dirty else ""}')
                else:
                    line_desc.append('—')
            print(f'  set {s:02d}: ' + ' | '.join(line_desc))
    if I is D:
        dump_cache(I)
    else:
        dump_cache(I); dump_cache(D)
    if L2 is not None:
        dump_cache(L2)

# Build and run the requested configurations
configs = [
    {'name':'DM unified 2x4', 'unified': (2, 4, 1)},
    {'name':'DM unified 4x4', 'unified': (4, 4, 1)},
    {'name':'DM unified 2x8', 'unified': (2, 8, 1)},
    {'name':'Split: I=2x2, D=2x2', 'I': (2, 2, 1), 'D': (2, 2, 1)},
    {'name':'Split: I=4x2, D=4x4', 'I': (4, 2, 1), 'D': (4, 4, 1)},
    {'name':'2-way SA unified 2x8', 'unified': (2, 8, 2)},
    # Optional L2 example under a DM L1:
    {'name':'DM unified 2x8 + L2 8x8', 'unified': (2, 8, 1), 'L2': (8, 8, 1)},
]

for cfg in configs:
    simulate_config(mem_trace, clock, cfg)
# =================== End Part 3: Cache simulator ======================
