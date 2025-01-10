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

## Laborplatte mit ESP + Sensoren
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

### initial configuration
- Installation requires that the ESP device is connected with a cable to a computer
    - Later updates can be installed wirelessly

- Board mit PC verbinden
    - am Board BOOT gedrückt halten plus kurz RST drücken, danach BOOT loslassen
    - select laborplatte.yaml --> select COM-Port of the ESP-Device --> install

## ESPHome
- https://esphome.io/guides/getting_started_hassio
- ESPHome: allows to write configurations + turn microcontrollers into smart home devices
    - reads a YAML configuration file, creates custom firmware, can install it directly on the device
    - Any devices/sensors defined in ESPHome configuration will automatically appear in Home Assistant's user interface
- Add ESPHome Addon (ESPHome Device Builder) to HA 
    - `https://<your_ha_url>/hassio/addon/5c53de3b_esphome/info`
- Start Addon > Open Web Interface

### Setting up the new ESPHome Device
- Add new device
    - Name: Laborplatte
    - enter wlan ssid and wpa key
    - Skip
    - select ESP32-S3

- select the right ESP32 Platform: [ESP32 Platform — ESPHome](https://esphome.io/components/esp32.html#configuration-variables)
    - [BPI-Leaf-S3 — PlatformIO latest documentation](https://docs.platformio.org/en/latest/boards/espressif32/bpi_leaf_s3.html#configuration)
    - `board: bpi_leaf_s3` --> geht nicht, also `board: esp32-s3-devkitc-1`

### Creating the yaml configuration

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
    sda: GPIO1
    scl: GPIO0
    scan: true
  - id: bus_b
    sda: GPIO5
    scl: GPIO6
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
    i2c_id: multiplex0channel0
    address: 0x77
    update_interval: 60s
    temperature:
      name: "BME680 Temperature"
      oversampling: 16x
    pressure:
      name: "BME680 Pressure"
    humidity:
      id: "humidity"
      name: "BME680 Humidity"
    gas_resistance:
      id: "gas_resistance"
      name: "BME680 Gas Resistance"
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