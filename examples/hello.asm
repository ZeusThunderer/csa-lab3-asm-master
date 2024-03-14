section data:
    sus: "Hello",0
section text:
    _start:
        add r2,r0,sus
    loop:
        ld r1,r2
        sw out,r1
        add r2,r2,1
        beq r1,r0,end
        jmp loop
    end:
        hlt