from cocotb_bus.monitors import Monitor
from cocotb.triggers import FallingEdge
from cocotb.utils import get_sim_time


class Monitor_Template(Monitor):
    def __init__(self, instance_path, callback = None, logging=False):
        # default name
        self.name = "Monitor Template"

        # Assign signals howto
        # "instance_path" should be the path in the dut to the instance this
        # monitor will be spying on.
        # To find the path description, in the simulator GUI, right-click on of the
        # instance's signals and choose "Describe". The full path will be shown
        # in the "console" window.
        # When calling the monitor constructor (see scoreboard example), keep only
        # the part relative to the instance_path. For example: dut.inst_counter
        # After assignment and to confirm path correctness, you can use the ._path member, for example:
        #   print(self._clk._path)
        # Here the underscore is used to clearly distinguish class properties from local variables.

        self._clk   = instance_path.clk
        self._valid = None # replace with instance_path.???
        self._data  = None # replace with instance_path.???

        # Enable/disable logging/printing
        self._logging = logging

        # Function to call when ready to analyse the collected data.
        # For example, to push data to a model class or scoreboard.
        super().__init__(callback)

    # Helper function
    def writeToLog(self, text):
        if (self._logging == True):
            self.log.info(text)

    """###############################################################
    Required function - "main loop" for the monitor
    
    Template uses simple example code to find 0 --> transitions on a "valid"
    signal, reads the data on the bus, applies a bitmask (AND) and then
    pushes the result to the baseclass in case a callback function was 
    implicitely or explicitely attached. An implicit examples would be
    with a scoreboard. 
    ###############################################################"""
    async def _monitor_recv(self):
        # Initialize loop variable, if any
        strobe_detect = 0 # helper to find "0 --> 1 transitions"
        self.writeToLog("Starting Monitor")
        while(True):
            # sample in the middle of the clock
            await FallingEdge(self._clk)

            if (strobe_detect == 0 and self._valid.value == 1):
                # new data, do something with it locally
                ManipulateData = self._data.value.integer

                # optional: do something with the data, for example print message, sanity check.
                #           detailed manipulation should go in the model...
                self.writeToLog(f'New data!: {ManipulateData}')
                ManipulateData = ManipulateData & 0x7F
                self.writeToLog(f'... and after bitmask: {ManipulateData}')

                # send information (integer, list, tuple, object, etc) using the callback function
                # this might en up in a model, a scoreboard (checker)
                super()._recv(ManipulateData)

            # Last commands in loop, update strobe detection
            strobe_detect = self._valid.value

        # end of while loop
        pass
