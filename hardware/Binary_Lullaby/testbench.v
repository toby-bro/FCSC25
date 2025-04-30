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