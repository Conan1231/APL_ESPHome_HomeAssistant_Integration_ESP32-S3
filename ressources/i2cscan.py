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
