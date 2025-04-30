.section .data
.globl aixxj3qmUvFTqgqLodmuaEap # Buffer to store the reversed flag
.align 16
aixxj3qmUvFTqgqLodmuaEap:
    .zero 73 # 72 bytes for result + 1 for null terminator

.globl jMunhwoW4bRqeCdJfXvfNrRm # Obfuscated flag data
.align 16
jMunhwoW4bRqeCdJfXvfNrRm:
    .quad 0xb5a805f032bf382d
    .quad 0x67f0e7ca538c9b04
    .quad 0xa57ae750f1c459f6
    .quad 0xbd5af750d9dcab74
    .quad 0x1d083790319e2bb6
    .quad 0x9f38670a692ca93e
    .quad 0x6d401f7293242b0e
    .quad 0x6dca4f1a51ee7bd4
    .quad 0x00f10572cb24f1ec

.section .text
.intel_syntax noprefix
.globl _start # Program entry point

_start:
    # Call the reverse function, passing the address of the obfuscated flag
    lea    rdi, [rip+jMunhwoW4bRqeCdJfXvfNrRm]
    call   reverse_wKtyPoT4WdyrkVzhvYUfvqo3M9iPVMd3

    # Print the reversed flag (72 bytes) to stdout
    mov    rax, 1                         # write syscall number
    mov    rdi, 1                         # stdout file descriptor
    lea    rsi, [rip+aixxj3qmUvFTqgqLodmuaEap] # buffer address
    mov    rdx, 72                        # buffer length
    syscall

    # Exit program
    mov    rax, 60                        # exit syscall number
    xor    rdi, rdi                       # exit code 0
    syscall


# Reverses the transformation: out_byte = (i * 3 + 31) ^ ((in_byte * 8) | (in_byte >> 5))
# Input: rdi = address of the 72-byte target output data (jMunhwoW4bRqeCdJfXvfNrRm)
# Output: Result stored in global buffer aixxj3qmUvFTqgqLodmuaEap
reverse_wKtyPoT4WdyrkVzhvYUfvqo3M9iPVMd3:
    endbr64
    push   rbp
    mov    rbp, rsp
    sub    rsp, 0x18            # Stack frame:
                                # [rbp-0x8]: i (outer loop counter, DWORD)
                                # [rbp-0xc]: test_in_byte (inner loop counter, WORD, only lower byte used)
                                # [rbp-0xd]: target_out_byte (current target byte, BYTE)
                                # [rbp-0x18]: input buffer address (QWORD)

    mov    QWORD PTR [rbp-0x18], rdi      # Store input buffer address

    mov    DWORD PTR [rbp-0x8], 0 # Initialize outer loop counter i = 0
    jmp    outer_loop_cond

outer_loop_start:
    # Get target_out_byte = input_buffer[i]
    mov    eax, DWORD PTR [rbp-0x8] # i
    cdqe                         # Sign-extend i to rax for addressing
    mov    rdi, QWORD PTR [rbp-0x18]
    movzx  ecx, BYTE PTR [rdi+rax] # Read target byte
    mov    BYTE PTR [rbp-0xd], cl # Store target_out_byte on stack

    # Inner loop: Iterate test_in_byte from 0 to 255
    mov    WORD PTR [rbp-0xc], 0  # Initialize inner loop counter test_in_byte = 0
    jmp    inner_loop_cond

inner_loop_start:
    # Load current test_in_byte
    movzx  ebx, BYTE PTR [rbp-0xc]  # bl = test_in_byte

    # Calculate K = i * 3 + 31
    mov    ecx, DWORD PTR [rbp-0x8] # i
    lea    edx, [rcx*2+rcx]       # edx = i * 3
    add    edx, 31                # edx = K

    # Calculate temp = (test_in_byte * 8) | (test_in_byte >> 5)
    mov    al, bl
    movzx  eax, al
    shl    eax, 3                 # eax = test_in_byte * 8
    mov    cl, bl
    sar    cl, 5                  # cl = test_in_byte >> 5 (arithmetic shift)
    movzx  ecx, cl
    or     eax, ecx               # eax = temp

    # Calculate xor_result = K ^ temp
    xor    eax, edx

    # Compare lower byte of xor_result with target_out_byte
    mov    cl, al
    cmp    cl, BYTE PTR [rbp-0xd]
    je     found_byte             # If match, jump to store the byte

    # Increment test_in_byte
    movzx  eax, WORD PTR [rbp-0xc]
    add    eax, 1
    mov    WORD PTR [rbp-0xc], ax
inner_loop_cond:
    cmp    WORD PTR [rbp-0xc], 256 # Loop while test_in_byte < 256
    jl     inner_loop_start

    # Byte not found (should not happen in this challenge)
    jmp    increment_outer_loop

found_byte:
    # Store the found test_in_byte into result_buffer[i]
    mov    eax, DWORD PTR [rbp-0x8] # i
    cdqe                         # rax = i
    lea    rsi, [rip+aixxj3qmUvFTqgqLodmuaEap] # result buffer address
    movzx  ecx, BYTE PTR [rbp-0xc] # found test_in_byte
    mov    BYTE PTR [rsi+rax], cl # result_buffer[i] = test_in_byte

increment_outer_loop:
    # Increment i
    add    DWORD PTR [rbp-0x8], 1

outer_loop_cond:
    # Loop while i < 72
    cmp    DWORD PTR [rbp-0x8], 72
    jl     outer_loop_start

    # Null-terminate the result buffer
    lea    rsi, [rip+aixxj3qmUvFTqgqLodmuaEap]
    mov    BYTE PTR [rsi+72], 0

    # Cleanup stack and return
    mov    rsp, rbp
    pop    rbp
    ret
