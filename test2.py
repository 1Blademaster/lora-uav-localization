import spidev
import RPi.GPIO as GPIO
import time

# Example GPIO pins
NSS_PIN = 8      # CE0
RESET_PIN = 17   # Or any GPIO
BUSY_PIN = 22    # Any GPIO
DIO1_PIN = 27    # Any GPIO

# Init SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI0, CE0
spi.max_speed_hz = 1000000  # Start slow for debugging

# Init GPIO
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

def send_command(opcode, data=[]):
    busy_wait()
    GPIO.output(NSS_PIN, GPIO.LOW)
    # spi.xfer2([opcode] + data)
    spi.writebytes([opcode])
    spi.writebytes(data)
    GPIO.output(NSS_PIN, GPIO.HIGH)
    busy_wait()

# ======== Basic setup ========

# Set to standby
STDBY_RC = 0x00
send_command(0x80, [STDBY_RC])  # SetStandby
print('Set to standby mode')

# Set packet type to LoRa
PACKET_TYPE_LORA = 0x01
send_command(0x8A, [PACKET_TYPE_LORA])  # SetPacketType
print('Set packet type')

# Set RF frequency — same as TX side!
rf_freq = int(2.45e9 * (2**25) / 32e6)
freq_bytes = [(rf_freq >> 24) & 0xFF, (rf_freq >> 16) & 0xFF, (rf_freq >> 8) & 0xFF, rf_freq & 0xFF]
send_command(0x86, freq_bytes)  # SetRfFrequency
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

# ======== IRQ mapping ========
# Enable RxDone IRQ on DIO1
# 0x08 = RX_DONE IRQ mask
# 0x01 = DIO1 mask
send_command(0x8D, [0x08, 0x00, 0x00, 0x00, 0x08])  # SetDioIrqParams
print('Set Dio params')

# ======== Start RX ========
# SetRx command: opcode 0x82
# Timeout = 0xFFFFFF means RX forever
send_command(0x82, [0xFF, 0xFF, 0xFF])  # Infinite RX
print('Starting infinite rx')

print("Receiver ready, waiting for packets...")

try:
    while True:
        if GPIO.input(DIO1_PIN) == GPIO.HIGH:
            print("IRQ: Packet received!")

            # 1) Get buffer status (to know payload length)
            spi.xfer2([0x13, 0x00])  # GetRxBufferStatus
            busy_wait()
            result = spi.readbytes(2)
            payload_len = result[0]
            buffer_ptr = result[1]
            print(f"Payload length: {payload_len}, pointer: {buffer_ptr}")

            # 2) ReadBuffer command (0x1E)
            spi.xfer2([0x1E, buffer_ptr, 0x00] + [0x00]*payload_len)
            busy_wait()
            rx_data = spi.readbytes(payload_len)
            print("Received:", bytes(rx_data).decode('utf-8', errors='ignore'))

            # 3) Clear IRQ
            send_command(0x02, [0xFF, 0xFF])  # ClearIrqStatus

            # 4) Go back to RX for next packet
            send_command(0x82, [0xFF, 0xFF, 0xFF])

        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
    spi.close()
    print("Receiver stopped.")
