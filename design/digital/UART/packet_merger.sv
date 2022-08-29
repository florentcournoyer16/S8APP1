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
    UsartInterface.rx _rx,
    input logic clk,
    input logic reset
);
    typedef enum bit [2:0] {IDLE, RECEIVE_SEGMENTS, CHECK_COUNT, CALCULATE_CRC, VALIDATE_CRC, AWAIT_ACK} states;

    states state;
    logic [SEGMENT_COUNT_BITS:0] segmentCount;
    UartInterface #(8) uart();
    logic [TRANSMISSION_LENGTH-1:0] packet ;

    logic crc_clear_r;
    logic crc_valid_r;
    logic [CRC_LENGTH-1:0] crc_r;
    logic crc_ready_r;

    UartRx rx(uart.rx, clk, !reset);
    CRC8 #(.DATA_LENGTH(MESSAGE_LENGTH)) crc_calc (clk, reset, packet[MESSAGE_LENGTH-1:0], crc_clear_r, crc_valid_r, crc_r, crc_ready_r);
    assign uart.sig = _rx.sig;

    task FSM();
        case (state)
            IDLE: begin
                _rx.valid <= 0;
                uart.ready <= 0;
                segmentCount = 0;
                crc_valid_r <= 0;
                if (uart.valid) begin
                    state <= RECEIVE_SEGMENTS;
                end
            end
            RECEIVE_SEGMENTS: begin
                if (uart.valid) begin
                    packet[segmentCount*8 +: 8] <= uart.data; // at index segmentCount*8, insert 8 bits
                    uart.ready <= 1;
                    segmentCount++;
                    state <= CHECK_COUNT;
                end
            end
            CHECK_COUNT: begin
                uart.ready <= 0;
                if (segmentCount < SEGMENT_COUNT) begin
                    state <= RECEIVE_SEGMENTS;
                end else begin
                    _rx.data <= packet[MESSAGE_LENGTH-1:0];
                    _rx.valid <= 0;
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
                    _rx.valid <= (crc_r == packet[TRANSMISSION_LENGTH-1:TRANSMISSION_LENGTH-DATA_LENGTH]);
                    state <= AWAIT_ACK;
                end
            end

            AWAIT_ACK: begin
                crc_clear_r <= 0;
                if (!_rx.valid) begin
                    state <= IDLE;
                end 
                else if (_rx.ready) begin
                    _rx.valid <= 0;
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
            uart.ready <= 0;
            segmentCount = 0;
            packet <= 0;
        end else begin
            FSM();
        end
    end

    assign _rx.parity_error = 1'b0;
endmodule