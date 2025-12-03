; Task 4 demo: vector add + vector sum
; A = [1, 2, 3]
; B = [4, 5, 6]
; C = A + B = [5, 7, 9]
; vsum(C) = 21  (in r1)

        go   0          ; start execution at address 0

0       ; ---- Code ----
        ; optional: clear r0 / r1
        ldi   0 0       ; r0 = 0 (not strictly needed)
        ldi   1 0       ; r1 = 0

        ; Vector add: C = A + B
        vadd  0 .vadd_desc    ; r0 <- base address of C (from descriptor)

        ; Vector sum: r1 = sum(C[i])
        vsum  1 .vsum_desc    ; r1 <- sum of elements of C

        ; stop and dump state
        int   1 0             ; trap 1 → print regs/mem/stats, then halt

; ------------------ DESCRIPTORS ------------------

; vadd descriptor: [A_base, B_base, C_base, N]
.vadd_desc
        dw    .vecA           ; base address of A
        dw    .vecB           ; base address of B
        dw    .vecC           ; base address of C (destination)
        dw    3               ; N = 3 elements

; vsum descriptor: [C_base, N]
.vsum_desc
        dw    .vecC           ; base address of C
        dw    3               ; N = 3 elements

; ------------------ DATA VECTORS ------------------

.vecA
        dw    1
        dw    2
        dw    3

.vecB
        dw    4
        dw    5
        dw    6

; destination C, initialized to 0s
.vecC
        dw    0
        dw    0
        dw    0
