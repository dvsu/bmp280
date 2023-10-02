# Bosch BMP280

Python-based driver for Bosch BMP280 digital pressure sensor.

## Usage

```python
import sys
import json
from smbus2 import SMBus
from dataclasses import asdict
from bmp280 import BMP280

# I2C bus 1
bus = SMBus(1)
sensor = BMP280(bus)

while True:
    try:
        print(json.dumps(asdict(sensor.get_measurement()), indent=2))

    except KeyboardInterrupt:
        sys.exit(1)

```

Example output

`get_measurement()`

```json
{
  "sensor": {
    "maker": "Bosch Sensortec",
    "model": "BMP280",
    "serial": null,
    "version": null
  },
  "measurements": [
    {
      "name": "temperature", 
      "unit": "C",
      "value": 27.95,
      "timestamp": "2023-10-01T01:23:45Z"
    }
  ]
}
```
