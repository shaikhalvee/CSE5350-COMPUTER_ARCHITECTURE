; sum an array
; store-then-load test
       go   0
0      ld   2 .count     ; r2 has value of counter
       ldi  3 .vals     ; r3 points to first value
       ldi  1 0       ; r1 contains sum
.loop  add  1 *3      ; r1 = r1 + next array value
       inc  3
       dec  2
       bnz  2 .loop
       sys  1 16
       dw   0
.count dw   5
.vals  dw   3
       dw   2
       dw   0
       dw   8
       dw   100
16     dw   0
       end
0      ldi  1 42         ; r1=42
       st   1 .x         ; mem[x]=42
       ld   2 .x         ; r2=42
       int  1 0          ; end
.x     dw   0

