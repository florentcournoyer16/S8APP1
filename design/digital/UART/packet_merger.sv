/*
    Author : Gabriel Lessard
    Project : Sigma Delta DAQ
    
    Universite de Sherbrooke, 2021
*/
`timescale 1ps/1ps
//import USARTPackage::*;
package PacketMergerPackage;
endpackage

module packet_merger #(
    DATA_LENGTH = 8,
    MESSAGE_LENGTH = 48,
    CRC_LENGTH = 8,
    TRANSMISSION_LENGTH = MESSAGE_LENGTH+CRC_LENGTH,
    SEGMENT_COUNT = TRANSMISSION_LENGTH/DATA_LENGTH,
    SEGMENT_COUNT_BITS = $clog2(SEGMENT_COUNT)-1)
    (
    UsartInterface.rx message_if,
    input logic clk,
    input logic reset
);
    typedef enum bit [2:0] {IDLE, RECEIVE_SEGMENTS, CHECK_COUNT, CALCULATE_CRC, VALIDATE_CRC, AWAIT_ACK} states;

    states state;
    logic [SEGMENT_COUNT_BITS:0] segmentCount;
    UartInterface #(8) uart_if();
    logic [TRANSMISSION_LENGTH-1:0] packet ;

    logic crc_clear_r;
    logic crc_valid_r;
    logic [CRC_LENGTH-1:0] crc_r;
    logic crc_ready_r;

    UartRx rx(uart_if.rx, clk, !reset);
    CRC8 #(.DATA_LENGTH(MESSAGE_LENGTH)) crc_calc (clk, reset, packet[MESSAGE_LENGTH-1:0], crc_clear_r, crc_valid_r, crc_r, crc_ready_r);
    assign uart_if.sig = message_if.sig;

    task FSM();
        case (state)
            IDLE: begin
                message_if.valid <= 0;
                uart_if.ready <= 0;
                segmentCount = 0;
                crc_valid_r <= 0;
                if (uart_if.valid) begin
                    state <= RECEIVE_SEGMENTS;
                end
            end
            RECEIVE_SEGMENTS: begin
                if (uart_if.valid) begin
                    packet[segmentCount*8 +: 8] <= uart_if.data; // at index segmentCount*8, insert 8 bits
                    uart_if.ready <= 1;
                    segmentCount++;
                    state <= CHECK_COUNT;
                end
            end
            CHECK_COUNT: begin
                uart_if.ready <= 0;
                if (segmentCount < SEGMENT_COUNT) begin
                    state <= RECEIVE_SEGMENTS;
                end else begin
                    message_if.data <= packet[MESSAGE_LENGTH-1:0];
                    message_if.valid <= 0;
                    state <= CALCULATE_CRC;
                end
            end
            CALCULATE_CRC: begin
                crc_valid_r <= 1;
                state <= VALIDATE_CRC;
            end
            VALIDATE_CRC: begin
            crc_valid_r <= 0;
                if (crc_ready_r) begin
                    crc_clear_r <= 1;
                    message_if.valid <= (crc_r == packet[TRANSMISSION_LENGTH-1:TRANSMISSION_LENGTH-DATA_LENGTH]);
                    state <= AWAIT_ACK;
                end
            end

            AWAIT_ACK: begin
                crc_clear_r <= 0;
                if (!message_if.valid) begin
                    state <= IDLE;
                end 
                else if (message_if.ready) begin
                    message_if.valid <= 0;
                    state <= IDLE;
                end
            end
        endcase
    endtask
    
    always_ff @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            crc_clear_r <= 0;
            crc_valid_r <= 0;
            uart_if.ready <= 0;
            segmentCount = 0;
            packet <= 0;
        end else begin
            FSM();
        end
    end

    assign message_if.parity_error = 1'b0;
endmodule
