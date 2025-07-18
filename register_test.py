import spidev
import RPi.GPIO as GPIO
import time

# === Hardware pin numbers ===
NSS = 8        # SPI chip select CE0
NRESET = 17    # Reset pin
RFBUSY = 22    # Busy pin

# === SX1280 register and commands ===
REG_RFFrequency23_16 = 0x906
REG_RFFrequency15_8 = 0x907
REG_RFFrequency7_0 = 0x908

RADIO_WRITE_REGISTER = 0x18
RADIO_READ_REGISTER = 0x19
RADIO_SET_RFFREQUENCY = 0x86
RADIO_SET_PACKETTYPE = 0x8A

FREQ_STEP = 198.364
PACKET_TYPE_LORA = 0x01

# === SPI setup ===
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI0, CE0
spi.max_speed_hz = 8000000
spi.mode = 0

# === GPIO setup ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(NSS, GPIO.OUT)
GPIO.setup(NRESET, GPIO.OUT)
GPIO.setup(RFBUSY, GPIO.IN)

def setStandby():
    STDBY_RC = 0x00
    writeCommand(0x80, [STDBY_RC])

# === Control NSS line ===
def NSS_LOW():
    GPIO.output(NSS, GPIO.LOW)

def NSS_HIGH():
    GPIO.output(NSS, GPIO.HIGH)

# === Busy wait ===
def checkBusy():
    timeout = 0
    while GPIO.input(RFBUSY) == GPIO.HIGH:
        time.sleep(0.001)
        timeout += 1
        if timeout > 10:
            print("ERROR - Busy Timeout!")
            break

# === Reset chip ===
def resetDevice():
    print("Reset device")
    time.sleep(0.01)
    GPIO.output(NRESET, GPIO.LOW)
    time.sleep(0.002)
    GPIO.output(NRESET, GPIO.HIGH)
    time.sleep(0.025) 
    checkBusy()

# === Write register ===
def writeRegisters(address, buffer):
    addr_h = (address >> 8) & 0xFF
    addr_l = address & 0xFF

    checkBusy()
    NSS_LOW()
    spi.xfer2([RADIO_WRITE_REGISTER, addr_h, addr_l] + buffer)
    NSS_HIGH()
    checkBusy()

def writeRegister(address, value):
    writeRegisters(address, [value])

# === Read register ===
def readRegisters(address, size):
    addr_h = (address >> 8) & 0xFF
    addr_l = address & 0xFF

    checkBusy()
    NSS_LOW()
    spi.xfer2([RADIO_READ_REGISTER, addr_h, addr_l, 0xFF])
    result = spi.readbytes(size)
    NSS_HIGH()
    checkBusy()
    return result

def readRegister(address):
    return readRegisters(address, 1)[0]

# === Write command ===
def writeCommand(opcode, buffer):
    checkBusy()
    NSS_LOW()
    # spi.xfer2([opcode] + buffer)
    spi.writebytes([opcode])
    spi.writebytes(buffer)
    NSS_HIGH()
    checkBusy()

# === Set packet type ===
def setPacketType(packet_type):
    writeCommand(RADIO_SET_PACKETTYPE, [packet_type])

# === Set RF frequency ===
def setRfFrequency(freq_hz, offset=0):
    freq_hz += offset
    freq_temp = int(freq_hz / FREQ_STEP)
    buffer = [
        (freq_temp >> 16) & 0xFF,
        (freq_temp >> 8) & 0xFF,
        freq_temp & 0xFF
    ]
    writeCommand(RADIO_SET_RFFREQUENCY, buffer)
    writeCommand(RADIO_SET_RFFREQUENCY, buffer)

# === Get frequency back ===
def getFreqInt():
    Msb = readRegister(REG_RFFrequency23_16)
    Mid = readRegister(REG_RFFrequency15_8)
    Lsb = readRegister(REG_RFFrequency7_0)
    freq_raw = (Msb << 16) + (Mid << 8) + Lsb
    freq_hz = freq_raw * FREQ_STEP
    return int(freq_hz)

# === Print registers ===
def printRegisters(start, end):
    print("Reg    0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F")
    addr = start
    while addr <= end:
        print(f"0x{addr:03X}  ", end="")
        for i in range(16):
            value = readRegister(addr)
            print(f"{value:02X} ", end="")
            addr += 1
        print()

# === Check device ===
def checkDevice():
    reg1 = readRegister(REG_RFFrequency7_0) # 69
    new = (reg1 + 1) & 0xFF # 70
    writeRegister(REG_RFFrequency7_0, new)
    reg2 = readRegister(REG_RFFrequency7_0)
    writeRegister(REG_RFFrequency7_0, reg1)  # Restore
    print(reg1, reg2, new)
    return reg2 == new

# === Setup ===
def begin():
    GPIO.output(NSS, GPIO.HIGH)
    GPIO.output(NRESET, GPIO.HIGH)
    resetDevice()
    setStandby()

    setPacketType(PACKET_TYPE_LORA)

    if checkDevice():
        print("Device found")
        return True
    else:
        print("No device responding")
        return False

# === Main ===
if __name__ == "__main__":
    print("2_Register_Test Starting")

    if begin():
        while True:
            resetDevice()
            print("Registers at reset")
            printRegisters(0x0900, 0x09FF)
            print()

            freq = getFreqInt()
            print(f" Frequency at reset {freq} Hz")

            print(f"Change Frequency to 2445000000 Hz")
            setPacketType(PACKET_TYPE_LORA)
            setRfFrequency(2445000000)

            freq = getFreqInt()
            print(f"      Frequency now {freq} Hz")
            printRegisters(0x0900, 0x090F)
            print()
            time.sleep(5)
    else:
        print("Exiting...")

    spi.close()
    GPIO.cleanup()
