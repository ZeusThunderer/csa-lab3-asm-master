section text:
    _start:
        ld r1,inp
        sw out,r1
        beq r1,r0,end
        jmp _start
    end:
        hlt