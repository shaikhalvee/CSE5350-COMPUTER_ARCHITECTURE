; store-then-load test
       go   0
0      ldi  1 42         ; r1=42
       st   1 .x         ; mem[x]=42
       ld   2 .x         ; r2=42
       int  1 0          ; end
.x     dw   0
; sum an array with a loop (causes RAW hazard: dec r2 -> bnz r2)
        go   0
0       ldi  2 .count      ; r2 = loop count
        ldi  3 .vals       ; r3 = base addr of array
        ldi  1 0           ; r1 = sum

.loop   add  1 *3          ; r1 += mem[r3]
        inc  3             ; r3++
        dec  2             ; r2--
        bnz  2 .loop       ; branch if r2 != 0

        int  1 0           ; end (or sys 1 0)

.count  dw   5
.vals   dw   3
        dw   2
        dw   0
        dw   8
        dw   100

