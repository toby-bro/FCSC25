// Basic gate definitions for Verilator

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
