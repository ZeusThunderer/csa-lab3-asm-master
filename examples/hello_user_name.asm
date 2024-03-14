section data:
    what: "What's your name?",0
    answ: "Hello "
    sus: 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    n: 16
section text:
    _start:
        add r2,r0,what
    print_what:
        ld r1,r2
        sw out,r1
        add r2,r2,1
        beq r1,r0,end1
        jmp print_what
    end1:
        add r4,r0,n
        ld r4,r4
        add r3,r0,r0
        add r2,r0,sus
    read_name:
        ld r1,inp
        sw r2,r1
        add r3,r3,1
        add r2,r2,1
        beq r3,r4,end
        beq r1,r0,end2
        jmp read_name
    end2:
        add r2,r0,answ
    loop2:
        ld r1,r2
        sw out,r1
        add r2,r2,1
        beq r1,r0,end3
        jmp loop2
    end3:
        hlt