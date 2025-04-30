# Binary lullaby

Wow I was not expecting a Verilog challenge, this language is really fun.
Anyways, this challenge consists of a Verilog file that does a lot of nonsense no one cares to read except for the line `assign { y[15], y[7] } = { x[15], x[7] };`, and the output of what this complicated circuit gave when it was fed the flag. The challenge is also lacking an implementation of the logic gates it uses but that is not a problem, we can write it.

As the inputs are wires, the input can take only two values 0 and 1. For once bruteforce seems the only option, and bruteforce seems feasible as there are only $2^{14} = 16384$ different values to test. We will thus write a `gates.v` file with the implementation of the basic gates in Verilog and a `testbench.v` that will bruteforce this code until finding the correct output. Once we have the correct input we will simply decode it back to ASCII with `decode.py`.

To solve the challenge the only thing left is to execute our programs.
We are using Icarus to simulate the Verilog, and we had put the initial input in input.txt

```bash
iverilog -o sweet_bruteforcer testbench.v && vvp sweet_bruteforcer && uv run decode.py
```

This is `gates.v`

```verilog
module NAND (input A, input B, output Y);
  assign Y = ~(A & B);
endmodule

module NOR (input A, input B, output Y);
  assign Y = ~(A | B);
endmodule

module NOT (input A, output Y);
  assign Y = ~A;
endmodule

module XOR (input A, input B, output Y);
  assign Y = A ^ B;
endmodule
```

Our `testbench.v`

```verilog
`timescale 1ns / 1ps
`include "gates.v"
`include "netlist.v"

module testbench;

  reg  [15:0] x_candidate;
  wire [15:0] y_actual;
  reg  [15:0] y_target;
  reg  [13:0] unknown_bits_counter; // To iterate through 2^14 possibilities

  // Instantiate the Unit Under Test (UUT)
  circuit uut (
    .x(x_candidate),
    .y(y_actual)
  );

  integer file_handle;
  integer scan_handle;
  integer line_num;
  integer output_file_handle;

  initial begin
    file_handle = $fopen("input.txt", "r");
    if (file_handle == 0) begin
      $display("Error: Could not open input.txt");
      $finish;
    end

    output_file_handle = $fopen("output.txt", "w");
     if (output_file_handle == 0) begin
      $display("Error: Could not open output.txt for writing");
      $fclose(file_handle);
      $finish;
    end


    line_num = 0;
    while (!$feof(file_handle)) begin
      scan_handle = $fscanf(file_handle, "%b\n", y_target);
      if (scan_handle == 1) begin
        line_num = line_num + 1;

        x_candidate[15] = y_target[15];
        x_candidate[7]  = y_target[7];

        // Iterate through all possibilities for the 14 unknown bits
        begin : brute_force_loop
          for (unknown_bits_counter = 0; unknown_bits_counter < 16384; unknown_bits_counter = unknown_bits_counter + 1) begin
            // Assign unknown bits from counter
            x_candidate[14:8] = unknown_bits_counter[13:7]; // Map upper 7 bits
            x_candidate[6:0]  = unknown_bits_counter[6:0];  // Map lower 7 bits

            #1; // Wait for combinatorial logic to settle

            if (y_actual == y_target) begin
              $fdisplay(output_file_handle, "%b", x_candidate);
              disable brute_force_loop;
            end
          end
        end

         if (unknown_bits_counter == 16384) begin
             $display("Error: No input found for y_target = %b", y_target);
         end

      end
    end

    $fclose(file_handle);
    $fclose(output_file_handle);
    $finish;
  end

endmodule
```

And finally `decode.py`

```python
def decode_output(input_filepath: str = 'output.txt') -> str:
    decoded_string = ''

    with open(input_filepath, 'r') as f:
        for line in f:
            binary_string = line.strip()
            if len(binary_string) == 16:
                try:
                    char1_bin = binary_string[0:8]
                    char2_bin = binary_string[8:16]

                    char1 = chr(int(char1_bin, 2))
                    char2 = chr(int(char2_bin, 2))

                    decoded_string += char1 + char2
                except ValueError:
                    print(f'Skipping invalid binary line: {binary_string}')
                except OverflowError:
                    print(f'Skipping value out of ASCII range: {binary_string}')
            elif binary_string:
                print(f'Skipping line with incorrect length ({len(binary_string)} bits): {binary_string}')

    return decoded_string


if __name__ == '__main__':
    result = decode_output()
    if result is not None:
        print('Decoded Result:')
        print(result)
```
