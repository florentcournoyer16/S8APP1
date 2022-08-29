/*
    Author : Thomas Labbé
    Project : Sigma Delta DAQ
    
    Universite de Sherbrooke, 2021
*/

package UARTRx;
endpackage

`timescale 1ns/1ps
`ifndef UARTRX_DEF
`define UARTRX_DEF 1
`include "UartParam.svh"
`endif
module UartRx
    // Parameters decleration
    #(parameter 
        LB_DATA_WIDTH   = $clog2(UART_DATA_LENGTH),
        PULSE_WIDTH     = UART_CLK_FREQ / UART_BAUD_RATE ,// Be sure that CLK_FREQ > BAUD_RATE
        LB_PULSE_WIDTH  = $clog2(PULSE_WIDTH),
        HALF_PULSE_WIDTH= PULSE_WIDTH/2)
    
    // Ports declaration
     (UartInterface.rx    _rx,
      input  logic        clk,
      input  logic        reset);

    // States for the FSM
    typedef enum logic [1:0] {STATE_WAIT, STATE_LOAD, STATE_PARITY, STATE_END} states;
    states                   state;

    logic [UART_DATA_LENGTH-1:0]  data_tmp_r;
    logic [LB_DATA_WIDTH:0]  data_cnt;
    logic [LB_PULSE_WIDTH:0] clk_cnt;
    logic                    rx_done;
    logic                    parity;
    logic                    parity_error_r;
    logic [UART_DATA_LENGTH-1:0]  data_r;
    logic                    valid_r;

   task FSM();            
        case(state)
            // Wait for the start Bit. Using the Majority method.
            STATE_WAIT: begin
                if(_rx.sig == 0) begin
                    clk_cnt  <= (PULSE_WIDTH[LB_PULSE_WIDTH:0] + HALF_PULSE_WIDTH[LB_PULSE_WIDTH:0]);
                    data_cnt <= 0;
                    state    <= STATE_LOAD;
                end
            end

            // Recieve data and put it inside a temp value
            STATE_LOAD : begin
                if(0 < clk_cnt) begin
                    clk_cnt <= clk_cnt - 1;
                end
                else begin
                    data_tmp_r <= {_rx.sig, data_tmp_r[UART_DATA_LENGTH-1:1]};
                    clk_cnt <= PULSE_WIDTH[LB_PULSE_WIDTH:0];

                    if (UART_PARITY_CHECK == 1) begin
                        parity <= parity ^ _rx.sig;
                    end

                    if(data_cnt >= UART_DATA_LENGTH - 1) begin
                        if (UART_PARITY_CHECK == 0) begin
                            state <= STATE_END;
                        end
                        else begin
                            state <= STATE_PARITY;
                        end
                    end
                    else begin
                        data_cnt <= data_cnt + 1;
                    end
                end
            end

            STATE_PARITY: begin
                if(0 < clk_cnt) begin
                    clk_cnt <= clk_cnt - 1;
                end
                else begin
                    state <= STATE_END;
                    clk_cnt <= PULSE_WIDTH[LB_PULSE_WIDTH:0];
                    parity_error_r <= (_rx.sig != parity && UART_PARITY_CHECK != 0);
                    parity <= UART_PARITY_MODE;
                end
            end

            // Wait for stop bit 
            STATE_END: begin
                if(0 < clk_cnt) begin
                    clk_cnt <= clk_cnt - 1;
                end
                else if(_rx.sig) begin
                    state <= STATE_WAIT;
                end
            end

            default: begin
                state <= STATE_WAIT;
            end
        endcase
   endtask

always_ff @(posedge clk) begin
    if(!reset) begin
        data_r  <= 0;
        valid_r <= 0;
        parity_error_r <= 0;
        state <= STATE_WAIT;
        data_tmp_r <= 0;
        data_cnt <= 0;
        clk_cnt <= 0;
        parity <= UART_PARITY_MODE;
        parity_error_r <= 0;
    end else begin
        if(rx_done && !valid_r) begin
            valid_r <= 1;
            data_r  <= data_tmp_r;
        end
        else if(valid_r && _rx.ready) begin
            valid_r <= 0;
        end
        FSM();
    end
end
    

   assign _rx.data = data_r;
   assign _rx.valid = valid_r;
   assign _rx.parity_error = parity_error_r;
   assign rx_done = (state == STATE_END) && (clk_cnt == 0);
   
endmodule