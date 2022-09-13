import cocotb
from cocotb.binary import BinaryValue
from cocotb_bus.scoreboard import Scoreboard
# Model can be very simple, basically a single function member with

class TestbenchClass_WithOnlyScoreboard:
    def __init__(self, dut, logging=False):
        self._dut = dut
        self.expected_output = []
        self.name = "None"
        self._logging = logging

        #if not hasattr(self, "log"):
        #    self.log = SimLog("cocotb.model.%s" % (type(self).__qualname__))

    def BuildVerificationComponents(self):
        self.BuildVerificationComponents_MergerCRC8()
        # self.BuildVerificationComponents_OtherModule() # generic example for component group

    # Divide and conquer - One scoreboard per member function
    # Building is done in this order:
    #   1- Add monitor to fetch result from HDL module
    #   2- Add Python model for HDL module
    #   3- Add monitor to fetch model inputs from HDL
    #   4- Add scoreboard
    def BuildVerificationComponents_MergerCRC8(self):
        from Monitor_CRC8   import Monitor_CRC8
        from Monitor_Uart8  import Monitor_Uart8
        from Model_CRC8     import Model_CRC8

        # Instanciate and initialize CRC8 Monitor
        self.inst_MergerCRC8_monitor = Monitor_CRC8(self._dut.inst_packet_merger.crc_calc,
                                                    logging=self._logging)
        self.inst_MergerCRC8_monitor._name = "inst_MergerCRC8_monitor"

        # Instanciate model before monitor that feeds it (uart8).
        self.inst_MergerCRC8_model = Model_CRC8()
        self.inst_MergerCRC8_model.name = "inst_MergerCRC8_model"

        # Instanciate and initialize uart8 monitor. Link with model through callback
        self.inst_MergerCRC8_Uart8_Src = Monitor_Uart8(self._dut.inst_packet_merger,
                                            logging=self._logging,
                                            callback=self.inst_MergerCRC8_model.add_input_transaction)
        self.inst_MergerCRC8_Uart8_Src._name = "inst_CRC8_Uart8_Src"

        # Use cocotb scoreboard class. Instanciate, then connect/add_interface
        # with 1-monitor object and 2- model result
        # Pretty magical (nothing to do except build it).
        self.inst_MergerCRC8_scoreboard = Scoreboard(self._dut, fail_immediately=False)
        self.inst_MergerCRC8_scoreboard.name = "inst_CRC8_scoreboard"
        self.inst_MergerCRC8_scoreboard.add_interface(self.inst_MergerCRC8_monitor, self.inst_MergerCRC8_model.expected_output)


    def BuildVerificationComponents_OtherModule(self):
        #from ???   import Monitor1_Class
        #from ???   import Model_Class
        #from ???   import Monitor2_Class

        # Instanciate and initialize Monitor
        self.inst_monitor1 = Monitor1_Class(self._dut.inst_name1,
                                                    logging=self._logging)
        self.inst_monitor1._name = "inst_monitor1"

        # Instanciate model before monitor that feeds it.
        self.inst_model = Model_Class()
        self.inst_model.name = "inst_model"

        # Instanciate and initialize other monitor. Link with model through callback
        self.inst_monitor2 = Monitor2_Class(self._dut.inst_name2,
                                            logging=self._logging,
                                            callback=self.inst_model.callback)
        self.inst_monitor2._name = "inst_monitor2"

        # Use cocotb scoreboard class. Instanciate, then connect/add_interface
        # with 1-monitor object and 2- model result
        # Pretty magical (nothing to do except build it).
        self.inst_scoreboard = Scoreboard(self._dut) #, fail_immediately=False)
        self.inst_scoreboard.name = "inst_scoreboard"
        self.inst_scoreboard.add_interface(self.inst_monitor1, self.inst_model.model_result)
