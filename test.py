import spidev
import RPi.GPIO as GPIO
import time

# Example GPIO pins
NSS_PIN = 8      # CE0
RESET_PIN = 17   # Or any GPIO
BUSY_PIN = 22    # Any GPIO
DIO1_PIN = 27    # Any GPIO

# SPI init
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI0, CS0
spi.max_speed_hz = 1000000  # Start slow, up to 18 MHz is supported

# GPIO init
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.OUT)
GPIO.setup(BUSY_PIN, GPIO.IN)
GPIO.setup(DIO1_PIN, GPIO.IN)
GPIO.setup(NSS_PIN, GPIO.OUT)

# Reset the radio
GPIO.output(RESET_PIN, GPIO.LOW)
time.sleep(0.01)
GPIO.output(RESET_PIN, GPIO.HIGH)
time.sleep(0.01)

def busy_wait():
    while GPIO.input(BUSY_PIN) == GPIO.HIGH:
        time.sleep(0.001)

# Send command helper
def send_command(opcode, data=[]):
    busy_wait()
    GPIO.output(NSS_PIN, GPIO.LOW)
    # spi.xfer2([opcode] + data)
    spi.writebytes([opcode])
    spi.writebytes(data)
    GPIO.output(NSS_PIN, GPIO.HIGH)
    busy_wait()

# Example: Set to Standby mode
STDBY_RC = 0x00
send_command(0x80, [STDBY_RC])  # 0x80 = SetStandby
print('Send standby command')

# Example: Set packet type to LoRa
PACKET_TYPE_LORA = 0x01
send_command(0x8A, [PACKET_TYPE_LORA])  # 0x8A = SetPacketType
print('Set packet type')

# Example: Set RF frequency to 2.4GHz (in Hz, value is Freq * 2^25 / 32e6)
# For 2.45GHz: reg_value = int(2.45e9 * (2**25) / 32e6)
rf_freq = int(2.45e9 * (2**25) / 32e6)
freq_bytes = [(rf_freq >> 24) & 0xFF, (rf_freq >> 16) & 0xFF, (rf_freq >> 8) & 0xFF, rf_freq & 0xFF]
send_command(0x86, freq_bytes)  # 0x86 = SetRfFrequency
print('Set frequency')

# === KEY FIX: MODEM PARAMS ===
# Spreading Factor = SF7 → 0x06
# BW = 812kHz → 0x06
# CR = 4/5 → 0x01
send_command(0x8B, [0x06, 0x06, 0x01])  # SetModulationParams
print('Set modulation parameters')

# === KEY FIX: PACKET PARAMS ===
# Preamble = 12 symbols
# Header = explicit
# Payload length = 20 bytes max
# CRC on
# Standard IQ
send_command(0x8C, [
    0x00, 0x0C,  # preamble length MSB, LSB
    0x00,        # implicit(1)/explicit(0)
    0x14,        # payload length
    0x01,        # CRC on
    0x00         # Standard IQ
])
print('Set packet parameters')

# Write message into buffer
send_command(0x0E, [0x00] + list(b'HELLO'))  # 0x0E = WriteBuffer

# Transmit buffer (0x83 = SetTx, with timeout)
send_command(0x83, [0x00, 0x00, 0x00])  # PeriodBase, PeriodBaseCount

print("Message sent!")
