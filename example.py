import sys
import json
from smbus2 import SMBus
from dataclasses import asdict
from bmp280 import BMP280

bus = SMBus(1)
sensor = BMP280(bus)


while True:
    try:
        print(json.dumps(asdict(sensor.get_measurement()), indent=2))

    except KeyboardInterrupt:
        sys.exit(1)