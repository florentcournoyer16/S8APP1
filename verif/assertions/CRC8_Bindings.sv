//////////////////////////////////////////////////////////////////////
// Author  :    Marc-Andre Tetrault
// Project :    GEI815
//
// Universite de Sherbrooke
//////////////////////////////////////////////////////////////////////


bind CRC8816 CRC8_Bindings inst_CRC8_Bindings(
        .cov_reset(reset),
        .cov_clk(clk),

        .cov_valid(i_valid),
        .cov_last(i_last),
        .cov_data(i_data),

        .cov_match(o_match),
        .cov_done(o_done),
        .cov_crc8(o_crc8)
	);

module CRC8_Bindings
	(
	input logic cov_reset,
	input logic cov_clk,

    input logic cov_valid,
    input logic cov_last,
    input logic [7:0] cov_data,

    input logic cov_match,
    input logic cov_done,
    input logic [7:0] cov_crc8
	);

default clocking DEFCLK @(posedge cov_clk);
endclocking

logic cov_reset_delayed;
always @(posedge cov_clk) begin
    cov_reset_delayed <= cov_reset;
end


// ------------------------------------------------------
string crc8_1_1_name = "CRC8.1.1"; string crc8_1_1_description = "cov_match is deasserted 1 clock cycle after a reset";
// ------------------------------------------------------

property prop_match_reset;
    $rose(cov_reset) |-> ##1 !cov_match;
endproperty

property prop_match_reset_;
    $rose(cov_reset) ##1 !cov_match;
endproperty

string test_name_pass = "test_name\t PASS";


ass_match_reset: assert property(prop_match_reset) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_1_1_name, crc8_1_1_description); 
cov_match_reset: cover property(prop_match_reset_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_1_1_name, crc8_1_1_description);

// ------------------------------------------------------
string crc8_1_2_name = "CRC8.1.2"; string crc8_1_2_description = "cov_done is deasserted 1 clock cycles after a reset";
// ------------------------------------------------------

property prop_done_after_reset;
    $rose(cov_reset) |-> ##1 !cov_done;
endproperty

property prop_done_after_reset_;
    $rose(cov_reset) ##1 !cov_done;
endproperty

ass_done_after_reset: assert property(prop_done_after_reset) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_1_2_name, crc8_1_2_description); 
cov_done_after_reset: cover property(prop_done_after_reset_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_1_2_name, crc8_1_2_description);

// ------------------------------------------------------
string crc8_1_3_name = "CRC8.1.3"; string crc8_1_3_description = "cov_crc8 is eq. to 0x0D 1 clock cycles after a reset";
// ------------------------------------------------------

sequence seq_crc8_reset_val;
    (cov_crc8 == 8'h0D);
endsequence

property prop_crc8_reset_val;
    $rose(cov_reset) |-> ##1 seq_crc8_reset_val;
endproperty

property prop_crc8_reset_val_;
    $rose(cov_reset) ##1 seq_crc8_reset_val;
endproperty

ass_crc8_reset_val: assert property(prop_crc8_reset_val) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_1_3_name, crc8_1_3_description); 
cov_crc8_reset_val: cover property(prop_crc8_reset_val_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_1_3_name, crc8_1_3_description);

// ------------------------------------------------------
string crc8_2_1_name = "CRC8.2.1"; string crc8_2_1_description = "cov_valid is asserted at least once";
string crc8_3_1_name = "CRC8.3.1"; string crc8_3_1_description = "cov_last is asserted at least once";
string crc8_4_1_name = "CRC8.4.1"; string crc8_4_1_description = "cov_data has a diverse bit coverage";
// ------------------------------------------------------

covergroup covg_in_sig @(posedge cov_clk iff(!cov_reset));
    cop_valid: coverpoint cov_valid {
        bins cov_valid_1 = {1};
    }
    cop_last: coverpoint cov_last {
        bins cov_last_1 = {1};
    }
    cop_data: coverpoint cov_data {
        bins data_bins[] = {[0:255]};
    }
    cro_last_valid: cross cop_last, cop_valid;
    cro_data_valid: cross cop_data, cop_valid;
endgroup

covg_in_sig covg_in_sig_inst = new();

real valid_cov;
real last_cov;
real data_cov;
real last_valid_cov;
real data_valid_cov;

always @(posedge cov_clk) begin
    valid_cov <= covg_in_sig_inst.cop_valid.get_coverage();
    last_cov <= covg_in_sig_inst.cop_last.get_coverage();
    data_cov <= covg_in_sig_inst.cop_data.get_coverage();
    last_valid_cov <= covg_in_sig_inst.cro_last_valid.get_coverage();
    data_valid_cov <= covg_in_sig_inst.cro_data_valid.get_coverage();
end

// ------------------------------------------------------
string crc8_3_2_name = "CRC8.3.2"; string crc8_3_2_description = "cov_last is always asserted at the same time as cov_valid";
// ------------------------------------------------------

property prop_last_and_valid;
    $fell(cov_last) |-> $fell(cov_valid); // TEST WAS MODIFIED AFTER SPEAKING WITH MARC-ANDRE
endproperty

property prop_last_and_valid_;
    $fell(cov_last) ##0 $fell(cov_valid); // TEST WAS MODIFIED AFTER SPEAKING WITH MARC-ANDRE
endproperty

ass_last_and_valid: assert property(prop_last_and_valid) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_3_2_name, crc8_3_2_description); 
cov_last_and_valid: cover property(prop_last_and_valid_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_3_2_name, crc8_3_2_description);

// ------------------------------------------------------
string crc8_5_1_name = "CRC8.5.1"; string crc8_5_1_description = "cov_last asserting implies that cov_done will assert in the next 2 clock cycles";
// ------------------------------------------------------

property prop_last_then_done; 
    disable iff(cov_reset_delayed) $fell(cov_last) |-> ##[1:2] $rose(cov_done);
endproperty

property prop_last_then_done_;
    disable iff(cov_reset_delayed) cov_last ##[1:2] $rose(cov_done);
endproperty

ass_last_then_done: assert property(prop_last_then_done) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_5_1_name, crc8_5_1_description); 
cov_last_then_done: cover property(prop_last_then_done_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_5_1_name, crc8_5_1_description);

// ------------------------------------------------------
string crc8_5_2_name = "CRC8.5.2"; string crc8_5_2_description = "cov_done is only deasserted 1 clock cycle after a reset";
// ------------------------------------------------------

property prop_done_without_reset;
    (cov_done && !cov_reset) |-> ##1 cov_done;
endproperty

property prop_done_without_reset_;
    (cov_done && !cov_reset) ##1 cov_done
endproperty

ass_done_without_reset: assert property(prop_done_without_reset) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_5_2_name, crc8_5_2_description); 
cov_done_without_reset: cover property(prop_done_without_reset_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_5_2_name, crc8_5_2_description);

// ------------------------------------------------------
string crc8_8_6_1_name = "CRC8.8.6.1"; string crc8_8_6_1_description = "o_match is both 0 and 1 when o_done is asserted";
string crc8_7_1_name = "CRC8.7.1"; string crc8_7_1_description = "cov_crc8 has a diverse bit coverage";
// ------------------------------------------------------

covergroup covg_out_sig @(negedge cov_clk iff(!cov_reset));
    cop_match: coverpoint cov_match {
        bins cov_match_0 = {0};
        bins cov_match_1 = {1};
    }
    cop_done: coverpoint cov_done {
        bins cov_done_1 = {1};
    }
    cop_crc8: coverpoint cov_crc8 {
        bins data_bins[] = {[0:255]};
    }
    cro_match_done: cross cop_match, cop_done;
endgroup

covg_out_sig covg_out_sig_inst = new();

real match_cov;
real done_cov;
real crc8_cov;
real match_done_cov;

always @(posedge cov_clk) begin
    match_cov <= covg_out_sig_inst.cop_match.get_coverage();
    done_cov <= covg_out_sig_inst.cop_done.get_coverage();
    crc8_cov <= covg_out_sig_inst.cop_crc8.get_coverage();
    match_done_cov <= covg_out_sig_inst.cro_match_done.get_coverage();
end

// ------------------------------------------------------
string crc8_6_2_name = "CRC8.6.2"; string crc8_6_2_description = "cov_done is asserted when cov_match is asserted";
// ------------------------------------------------------

property prop_match_and_done;
    disable iff(cov_reset_delayed) cov_match |-> cov_done;
endproperty

property prop_match_and_done_;
    disable iff(cov_reset_delayed) cov_match ##0 cov_done;
endproperty

ass_match_and_done: assert property(prop_match_and_done) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_6_2_name, crc8_6_2_description); 
cov_match_and_done: cover property(prop_match_and_done_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_6_2_name, crc8_6_2_description);

// ------------------------------------------------------
string crc8_6_6_name = "CRC8.6.6"; string crc8_6_6_description = "cov_match asserting implies that cov_last was asserted within the past 2 cycles";
// ------------------------------------------------------

sequence seq_match_after_last;
    $past(cov_last, 1) or $past(cov_last, 2)
endsequence

property prop_match_after_last;
    $rose(cov_match) |-> seq_match_after_last;
endproperty

property prop_match_after_last_;
   $rose(cov_match) ##0 seq_match_after_last;
endproperty

ass_match_after_last: assert property(prop_match_after_last) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_6_6_name, crc8_6_6_description); 
cov_match_after_last: cover property(prop_match_after_last_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_6_6_name, crc8_6_6_description);

// ------------------------------------------------------
string crc8_7_2_name = "CRC8.7.2"; string crc8_7_2_description = "cov_crc is stable when cov_valid is deasserted";
// ------------------------------------------------------

property prop_crc8_stable_when_not_valid;
    disable iff(cov_reset) !cov_valid |-> ##1 $stable(cov_crc8);
endproperty

property prop_crc8_stable_when_not_valid_;
    disable iff(cov_reset) !cov_valid ##1 $stable(cov_crc8);
endproperty

ass_crc8_stable_when_not_valid: assert property(prop_crc8_stable_when_not_valid) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", crc8_7_2_name, crc8_7_2_description); 
cov_crc8_stable_when_not_valid: cover  property(prop_crc8_stable_when_not_valid_) $display($stime,,, "\t %-10s \t %-80s \t PASS", crc8_7_2_name, crc8_7_2_description);


final begin
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", crc8_2_1_name, crc8_2_1_description, valid_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", crc8_3_1_name, crc8_3_1_description, last_valid_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", crc8_4_1_name, crc8_4_1_description, data_valid_cov);

    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", crc8_8_6_1_name, crc8_8_6_1_description, match_done_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", crc8_7_1_name, crc8_7_1_description, crc8_cov);
end


endmodule
