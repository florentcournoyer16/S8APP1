//////////////////////////////////////////////////////////////////////
// Author  :    Marc-Andre Tetrault
// Project :    GEI815
//
// Universite de Sherbrooke
//////////////////////////////////////////////////////////////////////


bind CRC8816 CRC8_Bindings
    #(.DATA_LENGTH(DATA_LENGTH),
    .DATA_LENGTH_BYTES(DATA_LENGTH_BYTES))

     inst_CRC8_Bindings(
        .cov_reset(reset),
        .cov_clk(clk),

        .cov_valid(i_valid),
        .cov_last(i_last),
        .cov_data(i_data),

        .cov_match(o_match),
        .cov_done(o_done),
        .cov_crc8(o_crc8)
	);

module CRC8_Bindings#(
    DATA_LENGTH = 32,
    DATA_LENGTH_BYTES = DATA_LENGTH/8)
	(
	input logic cov_reset,
	input logic cov_clk,

    input logic cov_valid,
    input logic cov_last,
    input logic [7:0] cov_data,

    input logic cov_match,
    input logic cov_done,
    input logic [DATA_LENGTH-1:0] cov_crc8
	);

default clocking DEFCLK @(posedge cov_clk);
endclocking


// Last implique que done montera a 1 apres 1 ou 2 coups d'horloge

sequence cov_done_s;
    cov_done
endsequence

property cov_done_p_a; 
    disable iff (cov_reset && !cov_done && !cov_match) $fell(cov_last) |-> ##[1:2] cov_done_s;
endproperty

property cov_done_p_c;
    disable iff (cov_reset && !cov_done && !cov_match) cov_last ##[1:2] cov_done_s;
endproperty

cov_done_a: assert property(cov_done_p_a) else $display($stime,,, "FAIL"); 
cov_done_c: cover property(cov_done_p_c) $display($stime,,, "PASS");

// Last implique que done montera a 1 apres 1 ou 2 coups d'horloge

// Si match a 1, cela implique done est aussi a 0

property conv_match_p_a;
    disable iff (cov_reset && !cov_done && !cov_match) cov_match |-> cov_done_s;
endproperty

property conv_match_p_c;
    disable iff (cov_reset && !cov_done && !cov_match) cov_match ##0 cov_done_s;
endproperty

cov_match_a: assert property(conv_match_p_a) else $display($stime,,, "FAIL"); 
cov_match_c: cover property(conv_match_p_c) $display($stime,,, "PASS");

// Si match a 1, cela implique done est aussi a 0

// Si match est devenu 1, cela implique que last était a 1 il y a 1-2 coups d'horloge

sequence cov_last_s(num_clk);
    $past(num_clk) or $past(num_clk+1)
endsequence

property cov_last_p_a;
    disable iff (cov_reset && !cov_done && !cov_match) $rose(cov_match) |-> cov_last_s(1);
endproperty

property cov_last_p_c;
    disable iff (cov_reset && !cov_done && !cov_match) $rose(cov_match) ##0 cov_last_s(1);
endproperty

cov_last_a: assert property(cov_last_p_a) else $display($stime,,, "FAIL"); 
cov_last_c: cover property(cov_last_p_c) $display($stime,,, "PASS");

// Si match est devenu 1, cela implique que last était a 1 il y a 1-2 coups d'horloge


// Au coup d'horloge apres que reset soit 1 vaut 0x0D

sequence CRC_after_reset_s;
    (cov_crc8 == 8'h0D);
endsequence

property CRC_after_reset_p_a;
    $rose(cov_reset) |-> ##1 CRC_after_reset_s;
endproperty

property CRC_after_reset_p_c;
    $rose(cov_reset) ##1 CRC_after_reset_s;
endproperty

CRC_after_reset_a: assert property(CRC_after_reset_p_a) else $display($stime,,, "FAIL"); 
CRC_after_reset_c: cover property(CRC_after_reset_p_c) $display($stime,,, "PASS");

// Au coup d'horloge apres que reset soit 1 vaut 0x0D


// La valeur du crc ne change pas si valide vaut 0

sequence crc_stable_s;
    $stable(cov_crc8)
endsequence


property CRC_stable_not_valid_p_a;
    disable iff (cov_reset && !cov_done && !cov_match) !cov_valid |-> ##1 crc_stable_s;
endproperty

property CRC_stable_not_valid_p_c;
    disable iff (cov_reset && !cov_done && !cov_match) !cov_valid ##1 crc_stable_s;
endproperty

CRC_stable_not_valid_a: assert property(CRC_stable_not_valid_p_a) else $display($stime,,, "FAIL"); 
CRC_stable_not_valid_c: cover  property(CRC_stable_not_valid_p_c) $display($stime,,, "PASS");

// Au coup d'horloge apres que reset soit 1 vaut 0x0D




endmodule