import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

def read_reg(addr):
    val = spi.xfer2([(addr << 1) & 0x7E, 0])
    return val[1]

print("Testing MFRC522...")

version = read_reg(0x37)

print("Version register:", hex(version))

if version in [0x91, 0x92]:
    print("✅ RFID module detected!")
else:
    print("❌ RFID NOT detected")
