# Babyfuscation

[Link to the challenge](https://hackropole.fr/fr/challenges/reverse/fcsc2025-reverse-babyfuscation/)

To solve this challenge we used gdb with the plugin pwndbg and IDA free.

This writeup will explain chronologically what we did

## Analysis of the Binary File

When decompiling the binary we see that all the variables and all the functions have very weird names.
Our objective was to rename each of these in IDA so as to gain clarity on what the program was really doing.

To rename the variables we just ran the program with gdb and stopped at a puts and got all the values from the stack. Once this was done we could know approximately what was the branch of success, what was transformed where and so on and so forth.

### Renaming the functions

Understading the functions was harder, mainly we identified that (in the following call hierarchy with main as common father to all these functions)

- `VsvYbpipYYgRoCeFtoxhtAmdFuNu3WvV` - gets out input
  - `LdUonKvqsjsJu4JdfAgtgbU9` - not so sure but looked similar to a strcmp or something alike, but it wasn't necessary to solve this question
- `wKtyPoT4WdyrkVzhvYUfvqo3M9iPVMd3` - transformed our input
  - `kRvUaKbhJewpX4HHFuMuPkNWc7xJ4cUV` - sort of len
- `VakkEeHbtHMpNqXPMkadR4v7K` - checked it against the obfuscated flag
  - `faubPTXHmhV4vfgEpzjqfMRjJ3qunsq9` - a strcmp that performs character by character comparison

Then we determined the length of the `jMunhwoW4bRqeCdJfXvfNrRm` string with which our transformed input is compared.
To do that, in gdb we

- Set a breakpoint at the start of the function `VakkEeHbtHMpNqXPMkadR4v7K`.
- Ran the program and hit the breakpoint.
- Used `info address jMunhwoW4bRqeCdJfXvfNrRm` to find the address of the string.
- Used `x/s &jMunhwoW4bRqeCdJfXvfNrRm` to examine the string in memory.
- Used `x/10gx &jMunhwoW4bRqeCdJfXvfNrRm` to examine the raw bytes of the string.
- Identified the null terminator and counted the number of characters to determine the length.

### Understanding `wKtyPoT4WdyrkVzhvYUfvqo3M9iPVMd3`

Next step was reversing this function... the function seemed to be mainly doing this
`out_byte = (i * 3 + 31) ^ ((in_byte * 8) | (in_byte >> 5))`
where `i` is the byte index, `in_byte` is the input byte, and `out_byte` is the output byte.

### Reversing (bruteforcing)

It seemed reasonably simple for a reverse challenge with no complex iterations... So we decided to implement the reverse logic directly in assembly. This was completely stupid as we should have rather done it in C or in python but it was fun trying to get that working.
We bruteforced the transformation byte by byte.

Steps :

- Created an assembly file `reverse_transform.s` with a function that takes the transformed output as input.
- For each byte position `i` from 0 to 71:
  - For each possible input byte value from 0 to 255:
    - Apply the transformation formula and check if it matches the target byte.
    - If found, store the input byte in the result buffer.
- Added a null terminator at the end of the recovered string.
- Made the program standalone by adding:
  - A data section with the target transformed output (`jMunhwoW4bRqeCdJfXvfNrRm`).
  - An initialization for the result buffer.
  - A `_start` function that calls the reverse transformation and prints the result.
  - Added `.intel_syntax noprefix` directive to specify Intel syntax.
  - Added proper size specifiers (`BYTE PTR`, `WORD PTR`, `DWORD PTR`, `QWORD PTR`) to memory references.
  - Fixed register usage and operand order to match Intel syntax expectations.
- Compiled with GNU Assembler:

  ```bash
  as -o reverse_transform.o reverse_transform.s
  ```

  - Linked to create an executable:

    ```bash
    ld -o reverse_transform reverse_transform.o
    ```

  - Executed the program:

    ```bash
    ./reverse_transform
    ```

  - The program output the recovered string to stdout.

The assembly program is [reverse_transform.s](./reverse_transform.s)
