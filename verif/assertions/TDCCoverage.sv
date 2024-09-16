//////////////////////////////////////////////////////////////////////
// Author  :    Marc-Andre Tetrault
// Project :    GEI815
//
// Universite de Sherbrooke
//////////////////////////////////////////////////////////////////////


bind TDC_dumb TDCCoverage inst_TDCCoverage(
	.cov_reset(reset),
	.cov_clk(clk),
	.cov_hasEvent(o_hasEvent),
	.cov_busy(o_busy),
	.cov_clear(i_clear),
	.cov_trigger(i_trigger),
	.cov_enable(i_enable_channel),
	.cov_TOT(o_pulseWidth),
	.cov_TS(o_timestamp)
	);

module TDCCoverage
	
	(
	input logic cov_reset,
	input logic cov_clk,
	input logic cov_hasEvent,
	input logic cov_busy,
	input logic cov_clear,
	input logic cov_trigger,
	input logic cov_enable,
	input logic [31:0] cov_TOT,
	input logic [31:0] cov_TS
	);

default clocking DEFCLK @(posedge cov_clk);
endclocking

sequence seq_glitchless_rose_trigger;
	($rose(cov_trigger) && !cov_busy) ##1 $stable(cov_trigger)
endsequence

sequence seq_glitchless_fell_trigger;
	($fell(cov_trigger) && cov_busy) ##1 $stable(cov_trigger)
endsequence


// ------------------------------------------------------
string tdc_1_1_name = "TDC.1.1"; string tdc_1_1_description = "cov_busy is asserted within the next two clock cycles after cov_trigger";
// ------------------------------------------------------

property prop_busy_after_trigger;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) seq_glitchless_rose_trigger |-> ##1 cov_busy;
endproperty

property prop_busy_after_trigger_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) seq_glitchless_fell_trigger ##1 cov_busy;
endproperty

ass_busy_after_trigger: assert property(prop_busy_after_trigger) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_1_1_name, tdc_1_1_description); 
cov_busy_after_trigger: cover property(prop_busy_after_trigger_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_1_1_name, tdc_1_1_description);

// ------------------------------------------------------
string tdc_1_2_name = "TDC.1.2"; string tdc_1_2_description = "cov_busy is only deactivated 20 cycles after a rising edge of cov_hasEvent";
// ------------------------------------------------------

property prop_busy_dead_time;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $rose(cov_hasEvent) |-> cov_busy ##0 $stable(cov_busy)[*20] ##1 !cov_busy;
endproperty

property prop_busy_dead_time_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $rose(cov_hasEvent) ##0 cov_busy ##0 $stable(cov_busy)[*20] ##1 !cov_busy;
endproperty

ass_busy_dead_time: assert property(prop_busy_dead_time) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_1_2_name, tdc_1_2_description); 
cov_busy_dead_time: cover property(prop_busy_dead_time_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_1_2_name, tdc_1_2_description);

// ------------------------------------------------------
string tdc_1_4_name = "TDC.1.4"; string tdc_1_4_description = "cov_busy is asserted after cov_trigger and cov_clear";
// ------------------------------------------------------

property prop_busy_after_trigger_clear;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $fell(cov_clear) ##1 seq_glitchless_rose_trigger |-> ##1 cov_busy;
endproperty

property prop_busy_after_trigger_clear_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $fell(cov_clear) ##1 seq_glitchless_rose_trigger ##1 cov_busy;
endproperty

ass_busy_after_trigger_clear: assert property(prop_busy_after_trigger_clear) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_1_4_name, tdc_1_4_description); 
cov_busy_after_trigger_clear: cover property(prop_busy_after_trigger_clear_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_1_4_name, tdc_1_4_description);

// ------------------------------------------------------
string tdc_1_5_name = "TDC.1.5"; string tdc_1_5_description = "cov_busy is not asserted after cov_clear with cov_trigger stable";
// ------------------------------------------------------

property prop_busy_after_clear_stable_trig;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $fell(cov_clear) ##1 (!cov_busy && cov_trigger && $stable(cov_trigger))[*2] |-> ##2 !cov_busy;
endproperty

property prop_busy_after_clear_stable_trig_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $fell(cov_clear) ##1 (!cov_busy && cov_trigger && $stable(cov_trigger))[*2] ##2 !cov_busy;
endproperty

ass_busy_after_clear_stable_trig: assert property(prop_busy_after_clear_stable_trig) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_1_5_name, tdc_1_5_description); 
cov_busy_after_clear_stable_trig: cover property(prop_busy_after_clear_stable_trig_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_1_5_name, tdc_1_5_description);

// ------------------------------------------------------
string tdc_1_6_name = "TDC.1.6"; string tdc_1_6_description = "cov_busy is not asserted if cov_enable is not asserted";
// ------------------------------------------------------

property prop_busy_without_enable;
	@(posedge cov_clk) disable iff(cov_reset) seq_glitchless_rose_trigger ##0 !cov_enable |-> ##2 !cov_busy;
endproperty

property prop_busy_without_enable_;
	@(posedge cov_clk) disable iff(cov_reset) seq_glitchless_rose_trigger ##0 !cov_enable ##2 !cov_busy;
endproperty

ass_busy_without_enable: assert property(prop_busy_after_trigger) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_1_6_name, tdc_1_6_description); 
cov_busy_without_enable: cover property(prop_busy_after_trigger_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_1_6_name, tdc_1_6_description);

// ------------------------------------------------------
string tdc_2_1_name = "TDC.2.1"; string tdc_2_1_description = "cov_hasEvent is asserted within 201 cycles after a falling edge of cov_trigger";
// ------------------------------------------------------

property prop_hasEvent_after_trigger_fell;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) seq_glitchless_fell_trigger |-> ##[0:199] $rose(cov_hasEvent);
endproperty

property prop_hasEvent_after_trigger_fell_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) seq_glitchless_fell_trigger  ##[0:199] $rose(cov_hasEvent);
endproperty

ass_hasEvent_after_trigger_fell: assert property(prop_hasEvent_after_trigger_fell) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_2_1_name, tdc_2_1_description); 
cov_hasEvent_after_trigger_fell: cover property(prop_hasEvent_after_trigger_fell_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_2_1_name, tdc_2_1_description);

// ------------------------------------------------------
string tdc_2_2_name = "TDC.2.2"; string tdc_2_2_description = "cov_hasEvent is deasserted on the cycle follow a rising edge of cov_clear";
// ------------------------------------------------------

property prop_hasEvent_after_clear_rose;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $rose(cov_clear) && cov_hasEvent |-> ##1 $fell(cov_hasEvent);
endproperty

property prop_hasEvent_after_clear_rose_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $rose(cov_clear) && cov_hasEvent ##1 $fell(cov_hasEvent);
endproperty

ass_hasEvent_after_clear_rose: assert property(prop_hasEvent_after_clear_rose) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_2_2_name, tdc_2_2_description); 
cov_hasEvent_after_clear_rose: cover property(prop_hasEvent_after_clear_rose_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_2_2_name, tdc_2_2_description);

// ------------------------------------------------------
string tdc_2_3_name = "TDC.2.3"; string tdc_2_3_description = "cov_TS is actualised on the same cycle of a rising edge of cov_hasEvent";
// ------------------------------------------------------

property prop_TS_hasEvent_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $rose(cov_hasEvent) ##0 $changed(cov_TS);
endproperty

cov_TS_hasEvent: cover property(prop_TS_hasEvent_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_2_3_name, tdc_2_3_description);

// ------------------------------------------------------
string tdc_2_4_name = "TDC.2.4"; string tdc_2_4_description = "cov_TOT is actualised on the same cycle of a rising edge of cov_hasEvent";
// ------------------------------------------------------

property prop_TOT_hasEvent_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) $rose(cov_hasEvent) ##0 $changed(cov_TOT);
endproperty

cov_TOT_hasEvent: cover property(prop_TOT_hasEvent_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_2_3_name, tdc_2_3_description);

// ------------------------------------------------------
string tdc_2_1_name_cp = "TDC.2.1"; string tdc_2_1_description_cp = "cov_hasEvent is asserted at least once";
string tdc_3_1_name = "TDC.3.1"; string tdc_3_1_description = "cov_TS values are covered";
string tdc_4_2_name = "TDC.4.2"; string tdc_4_2_description = "cov_TOT values are covered";
// ------------------------------------------------------

covergroup covg_out_sig
    @(negedge cov_clk iff(!cov_reset));
    cop_hasEvent: coverpoint cov_hasEvent;
    cop_TS: coverpoint cov_TS {
		bins possible_values[] = {[0:4275000000]};
	}
    cop_TOT: coverpoint cov_TOT {
		bins possible_values[] = {[0:1250000]};
	}
	cro_TS: cross cop_hasEvent, cop_TS;
	cro_TOT: cross cop_hasEvent, cop_TOT;
endgroup

covg_out_sig covg_out_sig_inst = new();

real hasEvent_cov;
real cov_TS_cov;
real cov_TOT_cov;

always @(posedge cov_clk) begin
    hasEvent_cov <= covg_out_sig_inst.cop_hasEvent.get_coverage();
    cov_TS_cov <= covg_out_sig_inst.cro_TS.get_coverage();
    cov_TOT_cov <= covg_out_sig_inst.cro_TOT.get_coverage();
end

// ------------------------------------------------------
string tdc_3_2_name = "TDC.3.2"; string tdc_3_2_description = "cov_TS is stable from the rising edge of cov_hasEvent to until the rising edge of cov_clear";
// ------------------------------------------------------

property prop_stable_TS;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) cov_hasEvent ##1 !$rose(cov_clear) |-> $stable(cov_TS);
endproperty

property prop_stable_TS_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) cov_hasEvent ##1 !$rose(cov_clear) ##0 $changed(cov_TS);
endproperty

ass_stable_TS: assert property(prop_stable_TS) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_3_2_name, tdc_3_2_description); 
cov_stable_TS: cover property(prop_stable_TS_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_3_2_name, tdc_3_2_description);

// ------------------------------------------------------
string tdc_4_3_name = "TDC.4.3"; string tdc_4_3_description = "cov_TOT is stable from the rising edge of cov_hasEvent to until the rising edge of cov_clear";
// ------------------------------------------------------

property prop_stable_TOT;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) cov_hasEvent ##1 !$rose(cov_clear) |-> $stable(cov_TOT);
endproperty

property prop_stable_TOT_;
	@(posedge cov_clk) disable iff(cov_reset || !cov_enable) cov_hasEvent ##1 !$rose(cov_clear) ##0 $changed(cov_TOT);
endproperty

ass_stable_TOT: assert property(prop_stable_TOT) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", tdc_4_3_name, tdc_4_3_description); 
cov_stable_TOT: cover property(prop_stable_TOT_) $display($stime,,, "\t %-10s \t %-80s \t PASS", tdc_4_3_name, tdc_4_3_description);

// ------------------------------------------------------
string tdc_7_1_name = "TDC.7.1"; string tdc_7_1_description = "cov_trigger is both asserted and deasserted";
string tdc_7_2_name = "TDC.7.2"; string tdc_7_2_description = "cov_clear is both asserted and deasserted";
string tdc_7_3_name = "TDC.7.3"; string tdc_7_3_description = "cov_enable is both asserted and deasserted";
string tdc_7_4_name = "TDC.7.4"; string tdc_7_4_description = "cov_trigger, cov_clear, and cov_enable are cross covered";
// ------------------------------------------------------

covergroup covg_in_sig
    @(negedge cov_clk iff(!cov_reset));
    cop_trigger: coverpoint cov_trigger;
    cop_clear: coverpoint cov_clear;
    cop_enable: coverpoint cov_trigger;
	cro_trig_clear_en: cross cop_clear, cop_trigger, cop_enable;
endgroup

covg_in_sig covg_in_sig_inst = new();

real trigger_cov;
real clear_cov;
real enable_cov;
real trig_clear_en_cov;

always @(posedge cov_clk) begin
	trigger_cov <= covg_in_sig_inst.cop_trigger.get_coverage();
	clear_cov <= covg_in_sig_inst.cop_clear.get_coverage();
	enable_cov <= covg_in_sig_inst.cop_enable.get_coverage();
	trig_clear_en_cov <= covg_in_sig_inst.cro_trig_clear_en.get_coverage();
end


final begin
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_2_1_name_cp, tdc_2_1_description_cp, hasEvent_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_3_1_name, tdc_3_1_description, cov_TS_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_4_2_name, tdc_4_2_description, cov_TOT_cov);

    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_7_1_name, tdc_7_1_description, trigger_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_7_2_name, tdc_7_2_description, clear_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_7_3_name, tdc_7_3_description, enable_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", tdc_7_4_name, tdc_7_4_description, trig_clear_en_cov);
end


endmodule
