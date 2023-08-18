import cocotb
from cocotb.binary import BinaryValue
from cocotb.log import SimLog
from gei815utils import gei815_get_expected_crc

# Models can be very simple, i.e. a single method (function) with
# a single property (variable) containing the calculated/expected result
# based on the input transaction.
#
# This example expects a bytes sequence and calculates a CRC.
# The result is placed in a Python list object to support
# multiple sequential calls to the function
#
# For the class project, this model will only work on the first command. Why?
class Model_Template: 
    def __init__(self, logging=False):
        self.expected_output = []
        self.byteList = []
        self._name = "None"
        self._logging = logging

        if not hasattr(self, "log"):
            self.log = SimLog("cocotb.model.%s" % (type(self).__qualname__))

    # Helper function
    def writeToLog(self, text):
        if (self._logging == True):
            self.log.info(text)

    # Function gets 1 byte a a time
    def add_input_transaction(self, transaction_buffer):
        self.byteList.append(transaction_buffer)

        if(len(self.byteList) == 6):
            self.writeToLog("Received 6th byte, calculating expected CRC.")
            CalculatedCRC = gei815_get_expected_crc(self.byteList)
            self.byteList.clear()
            self.expected_output.append(CalculatedCRC)
