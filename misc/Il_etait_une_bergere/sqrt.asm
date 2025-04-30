; Square root implementation using Heron's method (Babylonian method)
; Input: number in RB
; Output: integer square root in R0
; Uses R3 as a temporary register for immediate values 0 and 1
; Uses absolute jumps for labels.

; Special case for input = 0
MOV R0, #0       ; Initialize R0 to 0
MOV R3, #0       ; R3 = 0 (for comparison)
CMP RB, R3       ; Compare RB with R3 (which is 0)
JZA end          ; If input == 0, jump to end (Absolute Jump if Zero)

; Initialize guess
MOV R0, RB
MOV R3, #1       ; R3 = 1 (for division and addition)
SRL R0, R0, R3   ; Start with input/2 (using R3 for shift amount)
ADD R0, R0, R3   ; Ensure it's at least 1 (using R3 for addition)

; Main iteration loop using Heron's formula: x_n+1 = (x_n + N/x_n)/2
loop:
    ; Save current guess
    MOV R2, R0

    ; Calculate next approximation
    MOV R1, RB
    DIV R1, R1, R0   ; R1 = input/R0
    ADD R0, R0, R1   ; R0 = R0 + input/R0
    MOV R3, #1       ; R3 = 1 (for division)
    SRL R0, R0, R3   ; R0 = (R0 + input/R0)/2 (using R3 for shift amount)

    ; Check if converged
    CMP R0, R2
    JZA final_check  ; If no change, jump to final_check (Absolute Jump if Zero)
    JA loop          ; Otherwise continue (Absolute Jump Always)

final_check:
    ; Verify the result meets R0^2 <= input < (R0+1)^2

    ; Check R0^2 <= input
    MOV R1, R0
    MUL R1, R1, R1   ; R1 = R0^2
    CMP RB, R1       ; Compare input with R0^2 (Sets C if RB >= R1)
    JCA lower_bound_ok ; If C=1 (RB >= R1), jump to lower_bound_ok (Absolute Jump if Carry)

    ; input < R0^2, decrease R0
    MOV R3, #1       ; R3 = 1 (for subtraction)
    SUB R0, R0, R3   ; R0 = R0 - 1 (using R3)
    JA end           ; Jump to end (Absolute Jump Always)

lower_bound_ok:
    ; Check input < (R0+1)^2
    MOV R1, R0
    MOV R3, #1       ; R3 = 1 (for addition)
    ADD R1, R1, R3   ; R1 = R0 + 1 (using R3)
    MUL R1, R1, R1   ; R1 = (R0+1)^2
    CMP RB, R1       ; Compare input with (R0+1)^2 (Sets C if RB >= R1)
    JNCA end         ; If C=0 (RB < R1), R0 is correct, jump to end (Absolute Jump if No Carry)

    ; input >= (R0+1)^2, increase R0
    MOV R3, #1       ; R3 = 1 (for addition)
    ADD R0, R0, R3   ; R0 = R0 + 1 (using R3)
    ; Fall through to end label

end:
    STP