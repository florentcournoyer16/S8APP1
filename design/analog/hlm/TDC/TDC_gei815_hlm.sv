/*
    Author : Thomas Labbé
    Project : Sigma Delta DAQ
    
    Universite de Sherbrooke, 2021
*/

`timescale 1ns/1ps

import TDCTypes::*;

module TDC_dumb
    #(parameter
    TDC_CHANNEL channelNumber = CHAN_0
    )
    (// Ports declaration
        TDCInterface.internal bus,
        input                 clk,
        input                 trigger,
        input                 enable_channel,
        output                busy
    );

    // local variable
    reg find_falling_edge;
    assign bus.chan = channelNumber;

    always @(posedge trigger) begin
        bus.timestamp <= 32'($stime);
    end

    always @(negedge trigger) begin
        bus.timeOverThreshold <= 32'($stime);
    end

    always_ff @(posedge clk, posedge bus.clear) begin
        if (bus.clear) begin
            bus.hasEvent <= 0;
        end
        else if (!bus.hasEvent) begin
            find_falling_edge <= trigger;
            if(!trigger & find_falling_edge) begin
                bus.hasEvent <= 1;
            end
        end
    end
endmodule // TDC_dumb

