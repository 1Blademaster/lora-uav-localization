import spidev
import RPi.GPIO as GPIO
import time

# Pins
NSS = 8
NRESET = 17
BUSY = 27

# SX1280 opcodes
SET_STANDBY = 0x80
SET_PACKET_TYPE = 0x8A
SET_RF_FREQUENCY = 0x86
SET_MOD_PARAMS = 0x8B
SET_PKT_PARAMS = 0x8C
WRITE_BUFFER = 0x0E
SET_TX = 0x83

PACKET_TYPE_LORA = 0x01
STDBY_RC = 0x00

FREQ_HZ = 2445000000
FREQ_STEP = 198.364

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
spi.mode = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(NSS, GPIO.OUT)
GPIO.setup(NRESET, GPIO.OUT)
GPIO.setup(BUSY, GPIO.IN)

def NSS_LOW(): GPIO.output(NSS, GPIO.LOW)
def NSS_HIGH(): GPIO.output(NSS, GPIO.HIGH)

def checkBusy():
    while GPIO.input(BUSY) == GPIO.HIGH:
        time.sleep(0.001)

def sendCommand(opcode, data=[]):
    checkBusy()
    NSS_LOW()
    spi.xfer2([opcode] + data)
    NSS_HIGH()
    checkBusy()

def resetDevice():
    print("Reset...")
    GPIO.output(NRESET, GPIO.LOW)
    time.sleep(0.002)
    GPIO.output(NRESET, GPIO.HIGH)
    time.sleep(0.025)
    checkBusy()

def setStandby():
    sendCommand(SET_STANDBY, [STDBY_RC])

def setPacketType():
    sendCommand(SET_PACKET_TYPE, [PACKET_TYPE_LORA])

def setRfFrequency(freq_hz):
    freq_temp = int(freq_hz / FREQ_STEP)
    data = [
        (freq_temp >> 24) & 0xFF,
        (freq_temp >> 16) & 0xFF,
        (freq_temp >> 8) & 0xFF,
        freq_temp & 0xFF
    ]
    sendCommand(SET_RF_FREQUENCY, data)

def setModulationParams():
    SF7 = 0x06
    BW_812KHZ = 0x06
    CR_4_5 = 0x01
    sendCommand(SET_MOD_PARAMS, [SF7, BW_812KHZ, CR_4_5])

def setPacketParams():
    preambleLen = [0x00, 0x0C]  # 12 symbols
    header = 0x00  # Explicit
    payloadLen = 5  # "HELLO"
    crcOn = 0x01
    iq = 0x00
    sendCommand(SET_PKT_PARAMS, preambleLen + [header, payloadLen, crcOn, iq])

def writePayload(data):
    payload = [0x00] + [ord(x) for x in data]
    sendCommand(WRITE_BUFFER, payload)

def tx():
    sendCommand(SET_TX, [0x00, 0x00, 0x00])  # no timeout

resetDevice()
setStandby()
setPacketType()
setRfFrequency(FREQ_HZ)
setModulationParams()
setPacketParams()

print("Transmitting 'HELLO' every 5 seconds...")
while True:
    writePayload("HELLO")
    tx()
    print("Sent!")
    time.sleep(1)
