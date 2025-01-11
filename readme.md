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

- Inside the ESPHome Dashboard should be a new YAML-Configuration for "Laborplatte"
    - select EDIT
    - it should look like something like this
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
```

## Initial configuration
- Installation requires that the ESP device is connected with a cable to a computer
    - Later updates can be installed wirelessly

- Board mit PC verbinden
    - am Board BOOT gedrückt halten plus kurz RST drücken, danach BOOT loslassen
    - select laborplatte.yaml --> select COM-Port of the ESP-Device --> install

## Creating the yaml in ESPHome configuration
1. Define the I²C bus in the configuration
    - to find out the correct GPIO-Pins: look at Troubleshooting below
```yaml
i2c:
  sda: GPIOXX
  scl: GPIOXX
  scan: true
  id: bus_a
```

### Implementing the sensor configuration
- Just edit: laborplatte.yaml
- Starting with the I2C definition:

---
**TCA9548A Multiplexer** is an 4-channel I2C multiplexer that allows you to connect multiple I2C devices with the same address to a single I2C bus
- Configuration Variables
    - **address** (*Required*, int): The I2C address of the TCA9548A. Default is 0x70.
    - **id** (*Required*, string): Identifier for the multiplexer.
    - **i2c_id** (*Required*, string): ID of the I2C bus the multiplexer is connected to.
    - **channels** (*Required*, list): List of channel configurations:
    - **bus_id** (*Required*, string): Unique identifier for the channel
    * **channel** (*Required*, int): Channel number (0-7)
```yaml
...

i2c:
  - id: bus_a
    sda: 15
    scl: 16
    scan: true

# TCA9548A Multiplexer
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
```
---
**BME680 - Air Quality Sensor**
- (Channel 0, Address 0x77)
- [ESPHome - BME680](https://esphome.io/components/sensor/bme680.html#bme680-temperature-pressure-humidity-gas-sensor)
```yaml
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
**SGP40 - Gas Sensor**
- Volatile Organic Compound (VOC) Sensor
- [ESPHome - SGP40](https://esphome.io/components/sensor/sgp4x.html) 
- Sensor measures Total VOCs (TVOCs) in indoor environments
- VOC: organic chemicals that easily evaporate into the air at room temperature
- VOC Index Scale:
    - 0-100: Excellent air quality
    - 100-200: Good air quality  
    - 200-300: Moderate air quality
    - 300-400: Poor air quality
    - 400-500: Very poor air quality
- Common VOC Sources:
    - Cleaning products
    - Paints and varnishes  
    - Air fresheners
    - New furniture
    - Carpeting
    - Cooking activities
    - Personal care products
- Sensor calibration:
    - SGP40 requires several hours of initial runtime to establish accurate baseline readings through self-calibration algorithms. For best results, allow the sensor to calibrate in its intended operating environment

```yaml
  - platform: sgp4x
    voc:
      name: "VOC Index"
    i2c_id: multiplex0channel0
```

### Adding the Input Controls
- gesture and capacitive touch sensors

**MPR121 Touch Sensor**
- Capacitive Touch Sensor
- [MPR121 - ESPHome](https://esphome.io/components/binary_sensor/mpr121.html)

```yaml

```


**APDS9960 Sensor**
- RGB and gesture sensor
- [APDS9960 - ESPHome](https://esphome.io/components/sensor/apds9960.html)

```yaml

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

# Troubleshooting
- Fixing the I2C Connection Problem
- Issue: Finding the right SDA and SCL GPIO Pins
    - [i2c.arduino:096]: Results from i2c bus scan:
    - [i2c.arduino:098]: Found no i2c devices!

## Debugging with Circuit-Python
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

### prepare IDE
Code with Mu
    - [Download Mu](https://codewith.mu/en/download)
- select Mode: CircuitPython
- theme: activate darkmode
- open Folder E: --> `code.py`
    - serial -> inside the serial window `Strg+D` to reload script

### i2c testen + script
- testing the script: `i2cscan.py`
```py
...
print(f"SDA pin: {board.SDA}")
print(f"SCL pin: {board.SCL}")
```
 **i2cscan.py Ausgabe:**

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

Finally: the correct GPIO-Pins for SDA and SCL are **IO15** and **IO16**