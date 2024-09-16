//////////////////////////////////////////////////////////////////////
// Author  :    Marc-Andre Tetrault
// Project :    GEI815
//
// Universite de Sherbrooke
//////////////////////////////////////////////////////////////////////


// Bind statement usage in mixed-langage environments
//			https://www.youtube.com/watch?v=VuBqJoTRYyU


bind Registers RegisterBankCoverage u_RegisterBankCoverage(
	.cov_reset(reset),
	.cov_clk(clk),
	.cov_writeEnable(writeEnable),
	.cov_writeAck(writeAck),
	.cov_readEnable(readEnable),
	.cov_address(address),
	.cov_readData(readData),
	.cov_writeData(readData)
	);

module RegisterBankCoverage
	//#(parameter g_ChannelId = 15)
	(
	input logic cov_reset,
	input logic cov_clk,
    input logic cov_writeEnable,
    input logic cov_readEnable,
    input logic cov_writeAck,
    input logic [7:0] cov_address,
	input logic [31:0] cov_readData,
	input logic [31:0] cov_writeData
	);

default clocking DEFCLK @(posedge cov_clk);
endclocking

// Check that read strobes only 1 clock
property p_read_strobe_once;
	$rose(cov_readEnable) |=> $fell(cov_readEnable);
endproperty
ast_read_strobe_once : assert property(p_read_strobe_once);
cov_read_strobe_once : cover property(p_read_strobe_once);

// Check that write strobes only 1 clock
property p_write_ack_twice;
	$rose(cov_writeAck) |=> cov_writeAck ##1 $fell(cov_writeAck);
endproperty
ast_write_ack_twice : assert property(p_write_ack_twice);
cov_write_ack_twice : cover property(p_write_ack_twice);

// cover group: log if read and write access occured for all
// documented register address
// Lab: this covergroup will not work properly. Explore why and update.
// covergroup covg_RegisterAccess
//     @(negedge cov_clk && (cov_readEnable || cov_writeEnable) iff(!cov_reset));
// 	option.name		= "cov_RegisterAccess";
//     readMode       : coverpoint cov_readEnable { bins read_bins = {1}; }
//     writeMode      : coverpoint cov_writeEnable  { bins write_bins = {1}; }
//     addressSpace   : coverpoint cov_address { bins address_bins[] = {[0:9]}; }
// 	read_coverage  : cross readMode, addressSpace;
// 	write_coverage : cross writeMode, addressSpace;
// endgroup

// covg_RegisterAccess cov_userifCover = new();

// ------------------------------------------------------
string rb_1_1_name = "RB.1.1"; string rb_1_1_description = "cov_writeAck is deasserted 1 cycle after a rising edge on cov_reset";
// ------------------------------------------------------

property prop_writeAck_after_reset;
	@(posedge cov_clk) $rose(cov_reset) |-> ##1 !cov_writeAck;
endproperty

property prop_writeAck_after_reset_;
	@(posedge cov_clk) $rose(cov_reset) ##1 !cov_writeAck;
endproperty

ass_writeAck_after_reset: assert property(prop_writeAck_after_reset) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", rb_1_1_name, rb_1_1_description); 
cov_writeAck_after_reset: cover property(prop_writeAck_after_reset_) $display($stime,,, "\t %-10s \t %-80s \t PASS", rb_1_1_name, rb_1_1_description);

// ------------------------------------------------------
string rb_2_1_name = "RB.2.1"; string rb_1_2_description = "cov_writeEnable is asserted during a rising edge of cov_writeAck";
// ------------------------------------------------------

property prop_writeEnable_when_writeAck;
	@(posedge cov_clk) disable iff(cov_reset) $rose(cov_writeAck) |-> cov_writeEnable;
endproperty

property prop_writeEnable_when_writeAck_;
	@(posedge cov_clk) disable iff(cov_reset) $rose(cov_writeAck) ##1 cov_writeEnable;
endproperty

ass_writeEnable_when_writeAck: assert property(prop_writeEnable_when_writeAck) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", rb_2_1_name, rb_1_2_description); 
cov_writeEnable_when_writeAck: cover property(prop_writeEnable_when_writeAck_) $display($stime,,, "\t %-10s \t %-80s \t PASS", rb_2_1_name, rb_1_2_description);


// ------------------------------------------------------
string rb_2_2_name = "RB.2.2"; string rb_2_2_description = "cov_writeAck is always stable for 2 cycles when asserted";
// ------------------------------------------------------

property prop_writeAck_2_cycles;
	@(posedge cov_clk) disable iff(cov_reset) $rose(cov_writeAck) |-> ##1 cov_writeAck ##1 !cov_writeAck;
endproperty

property prop_writeAck_2_cycles_;
	@(posedge cov_clk) disable iff(cov_reset) $rose(cov_writeAck) ##1 cov_writeAck ##1 !cov_writeAck;
endproperty

ass_writeAck_2_cycles: assert property(prop_writeAck_2_cycles) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", rb_2_2_name, rb_2_2_description); 
cov_writeAck_2_cycles: cover property(prop_writeAck_2_cycles_) $display($stime,,, "\t %-10s \t %-80s \t PASS", rb_2_2_name, rb_2_2_description);


// ------------------------------------------------------
string rb_2_3_name = "RB.2.3"; string rb_2_3_description = "cov_writeAck is asserted on the follow cycle of a rising edge on cov_writeEnable";
// ------------------------------------------------------

property writeAck_after_writeEn;
	@(posedge cov_clk) disable iff(cov_reset || cov_readEnable) $rose(cov_writeEnable) |-> ##1 $rose(cov_writeAck);
endproperty

property writeAck_after_writeEn_;
	@(posedge cov_clk) disable iff(cov_reset || cov_readEnable) $rose(cov_writeEnable) ##1 $rose(cov_writeAck);
endproperty

ass_writeAck_after_writeEn: assert property(writeAck_after_writeEn) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", rb_2_3_name, rb_2_3_description); 
cov_writeAck_after_writeEn: cover property(writeAck_after_writeEn_) $display($stime,,, "\t %-10s \t %-80s \t PASS", rb_2_3_name, rb_2_3_description);

// ------------------------------------------------------
string rb_3_1_name = "RB.3.1"; string rb_3_1_description = "cov_address values are written to";
string rb_3_2_name = "RB.3.2"; string rb_3_2_description = "cov_address values are read";
string rb_4_1_name = "RB.4.1"; string rb_4_1_description = "cov_readData values are covered";
string rb_5_1_name = "RB.5.1"; string rb_5_1_description = "cov_writeData values are covered";
string rb_7_1_name = "RB.7.1"; string rb_7_1_description = "cov_readEnable is asserted";
string rb_8_1_name = "RB.8.1"; string rb_8_1_description = "cov_writeEnable is asserted";
// ------------------------------------------------------

covergroup covg_register_access
    @(negedge cov_clk && (cov_readEnable || cov_writeEnable) iff(!cov_reset));
    cop_readEnable: coverpoint cov_readEnable {
		bins read_bins = {1};
	}
    cop_writeEnable: coverpoint cov_writeEnable  {
		bins write_bins = {1};
	}
    cop_address: coverpoint cov_address {
		bins w_addr_bins[] = {7};
		bins r_addr_bins[] = {6, 9};
		bins wr_addr_bins[] = {1, 2, 3, 4, 5, 8};
	}
	cop_readData: coverpoint cov_readData;
	cop_writeData: coverpoint cov_writeData;
	cro_read_addr: cross cop_readEnable, cop_address;
	cro_write_addr: cross cop_writeEnable, cop_address;
	cro_readData: cross cop_readEnable, cop_readData;
	cro_writeData: cross cop_writeEnable, cop_writeData;
endgroup

covg_register_access covg_register_access_inst = new();

real readEnable_cov;
real writeEnable_cov;
real address_cov;
real read_addr_cov;
real write_addr_cov;
real readData_cov;
real writeData_cov;

always @(posedge cov_clk) begin
    readEnable_cov <= covg_register_access_inst.cop_readEnable.get_coverage();
    writeEnable_cov <= covg_register_access_inst.cop_writeEnable.get_coverage();
    address_cov <= covg_register_access_inst.cop_address.get_coverage();
    read_addr_cov <= covg_register_access_inst.cro_read_addr.get_coverage();
    write_addr_cov <= covg_register_access_inst.cro_write_addr.get_coverage();
	readData_cov <= covg_register_access_inst.cro_readData.get_coverage();
	writeData_cov <= covg_register_access_inst.cro_writeData.get_coverage();
end

// ------------------------------------------------------
string rb_4_3_name = "RB.4.3"; string rb_4_3_description = "cov_readData is stable if cov_readEnable and reset are deasserted";
// ------------------------------------------------------

property prop_readData_stable;
	@(posedge cov_clk) (!cov_readEnable && !cov_reset) |-> ##1 $stable(cov_readData);
endproperty

property prop_readData_stable_;
	@(posedge cov_clk) (!cov_readEnable && !cov_reset) ##1 $stable(cov_readData);
endproperty

ass_readData_stable: assert property(prop_readData_stable) else $display($stime,,, "\t %-10s \t %-80s \t FAIL", rb_4_3_name, rb_4_3_description); 
cov_readData_stable: cover property(prop_readData_stable_) $display($stime,,, "\t %-10s \t %-80s \t PASS", rb_4_3_name, rb_4_3_description);


final begin
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", rb_3_1_name, rb_3_1_description, write_addr_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", rb_3_2_name, rb_3_2_description, read_addr_cov);

    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", rb_4_1_name, rb_4_1_description, readData_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", rb_5_1_name, rb_5_1_description, writeData_cov);

    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", rb_7_1_name, rb_7_1_description, readEnable_cov);
    $display($stime,,, "\t %-10s \t %-80s \t %0.2f%%", rb_8_1_name, rb_8_1_description, writeEnable_cov);
end


endmodule
