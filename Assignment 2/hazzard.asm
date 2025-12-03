; in.asm — simple hazard + branch prediction test

        go   0          ; start at address 0

0       ; ---- setup ----
        ldi  0 3        ; r0 = loop count = 3
        ld   1 .x       ; r1 = mem[.x]
        add  2 1        ; RAW hazard: uses r1 right after ld r1
        ldi  1 10
        ldi  1 20       ; WAW hazard: two back-to-back writes to r1

.loop   dec  0          ; r0--
        bnz  0 .loop    ; RAW hazard: bnz reads r0 right after dec (and branch predicted)
        int  1 0        ; trap -> print state and halt

; ---- data ----
.x      dw   7
