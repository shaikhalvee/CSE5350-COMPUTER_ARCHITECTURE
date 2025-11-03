; store-then-load test
       go   0
0      ldi  1 42         ; r1=42
       st   1 .x         ; mem[x]=42
       ld   2 .x         ; r2=42
       int  1 0          ; end
.x     dw   0
