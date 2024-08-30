from base_uart_agent import BaseUartAgent, UartConfig

class CRC8UartAgent(BaseUartAgent):
    def __init__(self, uart_config: UartConfig):
        super(CRC8UartAgent, self).__init__(uart_config)
        self._crc8_offset: int = 0

    @property
    def crc8_offset(self) -> int:
        return self._crc8_offset

    @crc8_offset.setter
    def crc8_offset(self, offset: int) -> None:
        if not isinstance(offset, int):
            raise TypeError("property crc8_offset must be of type int")
        self._crc8_offset = offset

    def _calc_crc8(self, bytes_array: bytes) -> int:
        altered_crc8 = super(CRC8UartAgent, self)._calc_crc8(bytes_array) + self.crc8_offset
        return altered_crc8