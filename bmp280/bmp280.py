from time import sleep, time
from datetime import datetime
from enum import IntEnum
from smbus2 import SMBus
from .models import SensorData, SensorInfo, Measurement

class OSRS_T(IntEnum):
    X1 = 1 # 001 16-bit / 0.0050 C
    X2 = 2 # 010 17-bit / 0.0025 C
    X4 = 3 # 011 18-bit / 0.0012 C
    X8 = 4 # 100 19-bit / 0.0006 C
    X16 = 5 # 101 20-bit / 0.0003 C

class OSRS_P(IntEnum):
    X1 = 1 # 001 16-bit / 2.62 Pa
    X2 = 2 # 001 17-bit / 1.31 Pa
    X4 = 3 # 001 18-bit / 0.66 Pa
    X8 = 4 # 001 19-bit / 0.33 Pa
    X16 = 5 # 001 20-bit / 0.16 Pa

class PowerMode(IntEnum):
    SLEEP = 0 # 00
    FORCED = 1 # 01
    NORMAL = 3 # 11

class RegisterAddress(IntEnum):
    CTRL_MEAS = 0xF4
    CONFIG = 0xF5
    PRESSURE_TEMPERATURE = 0xF7
    COMPENSATION_PARAMETER = 0x88

class RegisterSize(IntEnum): # in byte
    CTRL_MEAS = 1
    CONFIG = 1
    PRESSURE_TEMPERATURE = 6
    COMPENSATION_PARAMETER = 24

class BMP280:

    def __init__(self, bus: SMBus, address: int = 0x77) -> None:
        self.__bus: SMBus = bus
        self.__address = address
        self.__tracker: float = 0
        self._configure_ctrl_meas()

    def chip_id(self) -> int:
        data = self.__bus.read_i2c_block_data(self.__address, 0xD0, 1)
        return data[0]

    def get_measurement(self) -> SensorData:
        if (time() - self.__tracker < 1):
            sleep(1)
        compensation_data = self._get_compensation_parameter()
        
        data = self.__bus.read_i2c_block_data(self.__address, 
                                              RegisterAddress.PRESSURE_TEMPERATURE, 
                                              RegisterSize.PRESSURE_TEMPERATURE)
        
        temperature_data = self._get_temperature_data(data[3:])

        temp_celsius = self._convert_temperature_data_to_celsius(temperature_data, 
                                                                 compensation_data[:3])

        utcnow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        self.__tracker = time()

        return SensorData(sensor=SensorInfo(maker="Bosch Sensortec", 
                                            model="BMP280", serial=None, 
                                            version=None),
                                            measurements=[
            Measurement(name="temperature", unit="C", value=temp_celsius, 
                        timestamp=utcnow)
        ])

    def _configure_ctrl_meas(self, osrs_t: OSRS_T = OSRS_T.X16, 
                            osrs_p: OSRS_P = OSRS_P.X16, 
                            mode: PowerMode = PowerMode.NORMAL) -> None:
        ctrl_meas = (osrs_t << 5) | (osrs_p << 2) | mode 
        self.__bus.write_i2c_block_data(self.__address, 
                                        RegisterAddress.CTRL_MEAS, [ctrl_meas])

    def _get_compensation_parameter(self) -> list[int]:
        data = self.__bus.read_i2c_block_data(self.__address, 
                                              RegisterAddress.COMPENSATION_PARAMETER, 
                                              RegisterSize.COMPENSATION_PARAMETER)
        
        unsigned_idx = [0, 6]

        converted: list[int] = []

        for i in range(0, len(data), 2):
            short = (data[i+1] << 8) | data[i]

            if i in unsigned_idx:
                converted.append(short)
                continue

            converted.append(short if short < 32768 else short - 65536)

        return converted

    def _get_temperature_data(self, data: list[int]) -> int:
        return (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)

    def _convert_temperature_data_to_celsius(self, data: int, 
                                             compensation: list[int]) -> float:
        var1 = ((((data >> 3) - (compensation[0] << 1))) * compensation[1]) >> 11
        var2 = (((((data >> 4) - compensation[0]) * ((data >> 4) - compensation[0])) >> 12) * compensation[2]) >> 14
        return (((var1 + var2) * 5 + 128) >> 8) / 100
