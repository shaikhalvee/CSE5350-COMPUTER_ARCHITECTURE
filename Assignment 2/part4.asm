; sum an array with a loop (causes RAW hazard: dec r2 -> bnz r2)
; Task 4 example: vector add + vector sum
; A = [1, 2, 3]
; B = [4, 5, 6]
; C = A + B = [5, 7, 9]
; vsum(C) = 21 (in r1)

        go   0
0       ldi  2 .count      ; r2 = loop count
        ldi  3 .vals       ; r3 = base addr of array
        ldi  1 0           ; r1 = sum

0       ; --- Vector add C = A + B ---
        vadd 0 .vadd_desc         ; r0 <- base of C (optional)

        ; --- Vector sum of C into r1 ---
        vsum 1 .vsum_desc         ; r1 <- sum of elements of C

        ; stop program
        int  1 0

; ------------------ DESCRIPTORS ------------------

; vadd descriptor: [A_base, B_base, C_base, N]
.vadd_desc
        dw   .vecA          ; base address of A
        dw   .vecB          ; base address of B
        dw   .vecC          ; base address of C (destination)
        dw   3              ; N = 3 elements  (N < 32)

.loop   add  1 *3          ; r1 += mem[r3]
        inc  3             ; r3++
        dec  2             ; r2--
        bnz  2 .loop       ; branch if r2 != 0
; vsum descriptor: [C_base, N]
.vsum_desc
        dw   .vecC          ; base address of C
        dw   3              ; N = 3 elements

        int  1 0           ; end (or sys 1 0)
; ------------------ DATA VECTORS ------------------

.count  dw   5
.vals   dw   3
.vecA
        dw   1
        dw   2
        dw   3

.vecB
        dw   4
        dw   5
        dw   6

; destination C, initialized to 0s
.vecC
        dw   0
        dw   8
        dw   100
        dw   0
        dw   0

