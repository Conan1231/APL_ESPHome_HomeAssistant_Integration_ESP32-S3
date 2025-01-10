# APL: ESPHome/HomeAssistant
- Aufgabe: YAML-Beschreibung für die Laborplatte für die Kompatibilität mit ESPHome und Integration in HA
    - Sensoren als Sensoren in HA
    - Taster&Co als Taster in HA
    - falls geht Display

- Vorrausetzung:
    - bestehende Home Assistant Instanz
- verwendete Home Assistant Installation
    - VM in Proxmox with OS Version: Home Assistant OS 14.1
    - Home Assistant Core: 2024.12.4

# Laborplatte mit ESP + Sensoren
![laborplatte mit sensoren](laborplatte.jpeg)
- **ESP**: BPI-Leaf-S3: basic development board equipped with ESP32-S3R2 chip
    - with a TCA9548A I²C Multiplexer
**I2C - Clients:**
- OLED Display 128x64
- Rotary Encoder
    - 5 Tasten
    - Drehrad decrease/increase einer Zahl
    - MPR121
        - 12 Touch-Tasten
        - simple test py script geht nicht
            - Datei "mpr121_simpletest_mux.py", Zeile 17, in <module> 
            - ValueError: IO16 in Benutzung
    - ST25DV16k
        - https://www.st.com/en/nfc/st25dv16k.html
        - NFC Tag
    - BME680
        - https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors/bme680/
        - Temperatur, Luftdruck, Feuchtigkeit
        - Raumluftqualität: VOC (volatile organic compounds)
    - SGP40
        - Raumluftqualität: VOC (volatile organic compounds)
    - SCD41
        - CO2 Sensor
    - PCF8523
        - https://www.nxp.com/docs/en/data-sheet/PCF8523.pdf
        - Real-Time Clock (RTC)
    - TSL2591
        - https://cdn-shop.adafruit.com/datasheets/TSL25911_Datasheet_EN_v1.pdf
        - Umgebungslicht (Lux)
    - APDS9960
        - https://www.mouser.de/datasheet/2/678/V02-4191EN_DS_APDS-9960_2015-11-13-909346.pdf
        - Digital Proximity, Ambient Light, RGB and Gesture Sensor
        - Gesten: links, rechts, hoch, runter, Abstand

## initial configuration
- Installation requires that the ESP device is connected with a cable to a computer
    - Later updates can be installed wirelessly

- Board mit PC verbinden
    - am Board BOOT gedrückt halten plus kurz RST drücken, danach BOOT loslassen
    - select laborplatte.yaml --> select COM-Port of the ESP-Device --> install

# ESPHome
- https://esphome.io/guides/getting_started_hassio
- ESPHome: allows to write configurations + turn microcontrollers into smart home devices
    - reads a YAML configuration file, creates custom firmware, can install it directly on the device
    - Any devices/sensors defined in ESPHome configuration will automatically appear in Home Assistant's user interface
- Add ESPHome Addon (ESPHome Device Builder) to HA 
    - `https://<your_ha_url>/hassio/addon/5c53de3b_esphome/info`
- Start Addon > Open Web Interface

## Setting up the new ESPHome Device
- Add new device
    - Name: Laborplatte
    - enter wlan ssid and wpa key
    - Skip
    - select ESP32-S3

- select the right ESP32 Platform: [ESP32 Platform — ESPHome](https://esphome.io/components/esp32.html#configuration-variables)
    - [BPI-Leaf-S3 — PlatformIO latest documentation](https://docs.platformio.org/en/latest/boards/espressif32/bpi_leaf_s3.html#configuration)
    - `board: bpi_leaf_s3` --> geht nicht, also `board: esp32-s3-devkitc-1`

## Creating the yaml in ESPHome configuration

### First: Fixing the I2C Connection Problem
- Issue: Finding the right SDA and SCL GPIO Pins
    - [i2c.arduino:096]: Results from i2c bus scan:
    - [i2c.arduino:098]: Found no i2c devices!

#### Troubleshooting and Debugging with Circuit-Python
- Flash the ESP32-S3 with Circuit-Python Firmware
- Board mit PC verbinden
    - Website aufrufen (Online ESP-Tool): https://adafruit.github.io/Adafruit_WebSerial_ESPTool/
    - am Board BOOT gedrückt halten plus kurz RST drücken, danach BOOT loslassen und connect im ESPTool drücken!
    - Choose File > `CP-Bootloaderv20.1+CPv9.2/combined.bin` > Program
    - Reset the Device: RST drücken
- Flash the new firmware
    - copy `adafruit-circuitpython-bpi_leaf_s3-de_DE-9.2.0.uf2` into the root-Verzeichnis

- Delete all existing files from `CIRCUITPY (E:)`
    - copy the python-scripts (e.g. "i2cscan.py") to root

#### prepare IDE
**Code with Mu**
    - [Download Mu](https://codewith.mu/en/download)
- select Mode: CircuitPython
- Thema: Darkmode aktivieren
- open Folder E: --> `code.py`
    - Seriell -> im Seriell-Window `Strg+D` to reload script

#### i2c testen + script
- testing the script: `i2cscan.py`
```py
import time
import board
import adafruit_tca9548a

def print_i2c_device(bus, addr, name):
    if len(bus)==1:
      if(bus[0] == -1):
          print(f"x/{addr:#0{4}x} {name}")
      else:
          print(f"{bus[0]}/{addr:#0{4}x} {name}")
    else:
      print(f"{bus}/{addr:#0{4}x} {name}")

# To use default I2C bus (most boards)
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
TCA9548A = False
try:
    while True:
        addr_dict = {}
        addr_main = {}
        if not i2c.try_lock():
            print("can't lock i2c")
            time.sleep(2)
            continue
        addrs = i2c.scan()
        i2c.unlock()
        for addr in addrs:
            addr_dict[addr] = []
            addr_dict[addr].append(-1)
            addr_main[addr] = []
            addr_main[addr].append(-1)

        print(f"I2C addresses - direct: {[hex(device_address) for device_address in addrs]}")


        if 0x70 in addrs:
            TCA9548A = True;

        if TCA9548A:
            mux = adafruit_tca9548a.PCA9546A(i2c)
            for channel in range(4):
                if mux[channel].try_lock():
                    addrs_mux = mux[channel].scan()
                    temp = addrs_mux.copy()
                    for addr in temp:
                        if(addr in addr_main):
                            addrs_mux.remove(addr)
                    print(f"I2C addresses - Bus {channel} : {[hex(device_address) for device_address in addrs_mux]}")
                    mux[channel].unlock()
                    for addr in addrs_mux:
                        if not(addr in addr_main):
                            if addr in addr_dict:
                                addr_dict[addr].append(channel)
                            else:
                                addr_dict[addr] = []
                                addr_dict[addr].append(channel)
        addr_sorted=(sorted(addr_dict.items(), key=lambda item: item[1]))
        for addr in addr_sorted:
            if addr[0] == 0x10:
                print_i2c_device(addr[1], addr[0], "PA1010d")
            elif addr[0] == 0x12:
                print_i2c_device(addr[1], addr[0], "PMSA003I")
            elif addr[0] == 0x23:
                print_i2c_device(addr[1], addr[0], "BH1750")
            elif addr[0] == 0x29:
                print_i2c_device(addr[1], addr[0], "TSL2591 or VL53L4CD")
            elif addr[0] == 0x2D:
                print_i2c_device(addr[1], addr[0], "ST25DV16k (Control)")
            elif addr[0] == 0x33:
                print_i2c_device(addr[1], addr[0], "MLX90640")
            elif addr[0] == 0x36:
                print_i2c_device(addr[1], addr[0], "MAX1704x")
            elif addr[0] == 0x39:
                print_i2c_device(addr[1], addr[0], "APDS9960 or AS7341")
            elif addr[0] == 0x3C:
                print_i2c_device(addr[1], addr[0], "SH1107 128x64-oled")
            elif addr[0] == 0x49:
                print_i2c_device(addr[1], addr[0], "seesaw ANO")
            elif addr[0] == 0x4A:
                print_i2c_device(addr[1], addr[0], "BNO08x")
            elif addr[0] == 0x53:
                print_i2c_device(addr[1], addr[0], "ENS160 or LTR390 or ST25DV16k (system memory)")
            elif addr[0] == 0x57:
                print_i2c_device(addr[1], addr[0], "ST25DV16k (user memory)")
            elif addr[0] == 0x59:
                print_i2c_device(addr[1], addr[0], "SGP40")
            elif addr[0] == 0x5A:
                print_i2c_device(addr[1], addr[0], "MPR121")
            elif addr[0] == 0x60:
                print_i2c_device(addr[1], addr[0], "seesaw Neopixel")
            elif addr[0] == 0x62:
                print_i2c_device(addr[1], addr[0], "SCD4x")
            elif addr[0] == 0x68:
                print_i2c_device(addr[1], addr[0], "PCF8523")
            elif addr[0] == 0x69:
                print_i2c_device(addr[1], addr[0], "ICM20X")
            elif addr[0] == 0x70:
                print_i2c_device(addr[1], addr[0], "TCA9548A")
            elif addr[0] == 0x77:
                print_i2c_device(addr[1], addr[0], "BME680")
        break
        time.sleep(2)
except Exception as ex:
    print(ex)
finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
    if TCA9548A:
        try:
            mux[0].unlock()
        except:
            print()
			
print(f"SDA pin: {board.SDA}")
print(f"SCL pin: {board.SCL}")
```
 **i2cscan.py Ausgabe:**
 ---
```py
I2C addresses - direct: ['0x3c', '0x70']
I2C addresses - Bus 0 : ['0x29', '0x39', '0x49', '0x59', '0x5a', '0x62', '0x68', '0x77']
I2C addresses - Bus 1 : []
I2C addresses - Bus 2 : ['0x2d', '0x53', '0x57']
I2C addresses - Bus 3 : []
x/0x70 TCA9548A
x/0x3c SH1107 128x64-oled
0/0x68 PCF8523
0/0x29 TSL2591 or VL53L4CD
0/0x39 APDS9960 or AS7341
0/0x77 BME680
0/0x5a MPR121
0/0x62 SCD4x
0/0x59 SGP40
0/0x49 seesaw ANO
2/0x53 ENS160 or LTR390 or ST25DV16k (system memory)
2/0x2d ST25DV16k (Control)
2/0x57 ST25DV16k (user memory)

SDA pin: board.IO15
SCL pin: board.IO16
```

> **Yay the right GPIO-Pins are IO15 and IO16**

### Implementing the Sensor-Configuration

```yaml
esphome:
  name: laborplatte
  friendly_name: Laborplatte

esp32:
  board: esp32-s3-devkitc-1
  framework:
    type: arduino

# Enable logging
logger:

# Enable Home Assistant API
api:
  encryption:
    key: "XXXX"

ota:
  - platform: esphome
    password: "XXXX"

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

  # Enable fallback hotspot (captive portal) in case wifi connection fails
  ap:
    ssid: "Laborplatte Fallback Hotspot"
    password: "XXXX"

captive_portal:

i2c:
  - id: bus_a
    sda: 15
    scl: 16
    scan: true

tca9548a:
  - address: 0x70
    id: multiplex0
    i2c_id: bus_a
    channels:
      - bus_id: multiplex0channel0
        channel: 0
      - bus_id: multiplex0channel1
        channel: 1
      - bus_id: multiplex0channel2
        channel: 2
      - bus_id: multiplex0channel3
        channel: 3


sensor:
  - platform: bme680
    temperature:
      name: "Temperature Channel 0"
    humidity:
      name: "Humidity Channel 0"
    pressure:
      name: "Pressure Channel 0"
    gas_resistance:
      name: "Gas Resistance Channel 0"
    address: 0x77
    i2c_id: multiplex0channel0
```

### Connecting the ESP device to Home Assistant
- prerequisites:
    - device is initialized with the yaml
    - device is online
- device should be now automatically discovered
    - Settings > Devices & services > Add Integration "ESPHome"
- HA: create new dashboard
    - raw configuration editor
```yaml
views:
  - title: Home
    sections:
      - type: grid
        cards:
          - type: heading
            heading: Sensoren
            heading_style: title
          - type: entities
            entities:
              - entity: sensor.laborplatte_bme680_gas_resistance
                name: BME680 Gas Resistance
              - entity: sensor.laborplatte_bme680_humidity
                name: BME680 Humidity
              - entity: sensor.laborplatte_bme680_pressure
                name: BME680 Pressure
              - entity: sensor.laborplatte_bme680_temperature
                name: BME680 Temperature
            title: Laborplatte
    cards: []
```