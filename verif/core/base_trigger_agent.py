from dataclasses import dataclass
from cocotb.handle import ModifiableObject
from cocotb.triggers import Timer
from base_uart_agent import TDCChannel
from cocotb.log import SimLog

@dataclass
class PulseConfig:
    rise_time: int
    fall_time: int
    channel: TDCChannel = TDCChannel.CHAN0

class BaseTriggerAgent():
    def __init__(self, trig: ModifiableObject):
        self._trig = trig
        self._log = SimLog("cocotb.%s" % type(self).__qualname__)
    async def send_pulses(self, pulses: list[PulseConfig], units: str = "ns") -> None:
        rise_time_list: list[int] = [pulse.rise_time for pulse in pulses]
        fall_time_list: list[int] = [pulse.fall_time for pulse in pulses]
        gen_time = 0
        while len(fall_time_list) > 0:
            min_fall: int = min(fall_time_list)
            if len(rise_time_list) > 0:
                min_rise: int = min(rise_time_list)
            else:
                min_rise = min(fall_time_list)+1
            
            await Timer(min([min_fall, min_rise])-gen_time, units=units)
            gen_time = min([min_fall, min_rise])
            if min_rise < min_fall:
                for pulse in pulses:
                    if pulse.rise_time == min_rise:
                        self._trig[pulse.channel.value].value = 1
                rise_time_list.remove(min_rise)
            if min_fall < min_rise:
                for pulse in pulses:
                    if pulse.fall_time == min_fall:
                        self._trig[pulse.channel.value].value = 0
                fall_time_list.remove(min_fall)
            if min_fall == min_rise:
                for pulse in pulses:
                    if pulse.fall_time == min_fall:
                        self._trig[pulse.channel.value].value = 0
                    if pulse.rise_time == min_rise:
                        self._trig[pulse.channel.value].value = 1
                fall_time_list.remove(min_fall)
                rise_time_list.remove(min_rise)
