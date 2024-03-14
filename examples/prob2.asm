section data:
    sum: 0
    fib1: 1
    fib2: 1
    max: 4000000 
    answ: 4613732
    success: "Answer is correct",0
section text:
    _start:
        ld r1,fib1      ;r1 = a
        ld r2,fib2      ;r2 = b
        ld r3,sum       ;
        ld r6,max        ;
    loop:
        add r4,r0,r1    ;c = a
        add r1,r1,r2    ;a = a+b
        add r2,r0,r4    ;b = c
        blt r6,r1,save   ;if max < a goto end 
        rem r5,r1,2     ;d = r1%2
        bnq r5,r0,next  ;if d != 0 goto next
        add r3,r3,r1    ;sum+=a
    next:
        jmp loop
    save:
        sw sum,r3
        ld r2,answ
        beq r3,r2,print
        jmp end
    print:
        add r2,r0,success
    loop_print:
        ld r1,r2
        sw out,r1
        add r2,r2,1
        beq r1,r0,end
        jmp loop_print
    end:
        hlt
        