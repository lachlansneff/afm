`timescale 1 ns / 1 ps

`define DEBUGREGS

module test;
    // Make a regular clock.
    reg clk = 0;
    always #5 clk = ~clk;

    reg rst = 1;
    initial begin
        repeat (1) @(posedge clk);
        rst <= 0;
    end

    initial begin
        $dumpfile("top.vcd");
        $dumpvars(0,test);
        repeat (100000) @(posedge clk);
        $finish;
    end

    wire led;

    top top(clk, rst, led);
endmodule
