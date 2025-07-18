import os
import sys
import time
import RPi.GPIO as GPIO
from loguru import logger

import const
from sx1280 import SX128XLT

lora: SX128XLT = None

txPower = 10

freq = 2445000000
offset = 0
bandwidth = const.LORA_BW_0400
spreading_factor = const.LORA_SF7
code_rate = const.LORA_CR_4_5

SPI_BUS = 0       # SPI0
SPI_CS = 0        # Chip Select 0 (GPIO8)
BUSY_GPIO = 22    # GPIO22 (Physical Pin 15)
RESET_GPIO = 17   # GPIO17 (Physical Pin 11)
DIO1_GPIO = 27    # GPIO27 (Physical Pin 13) for ranging interrupt




buff = "Hello World 1234567890"


def init():
    global lora

    # configure RPi GPIO
    GPIO.setmode(GPIO.BCM)
    # GPIO.setup(DIO1_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # GPIO.add_event_detect(DIO1_GPIO, GPIO.FALLING, callback=interrupt_callback)
    #GPIO.add_event_detect(27, GPIO.RISING, callback=interrupt_callbackRise)
    print("Test")

    # initialise the SX1280 module
    lora = SX128XLT(SPI_BUS, SPI_CS, 8, BUSY_GPIO, pin_nreset = RESET_GPIO, pin_dio1 = DIO1_GPIO)

    # setup the LoRa configuration
    lora.setupLoRa(freq, offset, spreading_factor, bandwidth, code_rate)
    lora.setBufferBaseAddress(0, 1)

    # debug configuration values
    lora.printModemSettings()
    lora.printOperatingSettings()
    # lora.printRegisters(0x900, 0x9FF)

    logger.info("~~~ LoRa SX1280 Transmitter is Ready ~~~")

def interrupt_callback(channel):
    logger.info("interrupt")
    print(f"Interrupt detected on pin {channel}")

def interrupt_callbackRise(channel):
    logger.info("interrupt riseing")
    print(f"Rising Interrupt detected on pin {channel}")

def loop():
    global lora

    startMs = time.time()

    txPacketL = lora.transmit(buff, 10000, txPower, const.NO_WAIT)

    if txPacketL > 0:
        endMs = time.time()

        logger.info(f"TX: {buff} ~ in {endMs - startMs}ms")
    else:
        logger.error("Transmit failed")

    time.sleep(2)


if __name__ == "__main__":
    try:
        init()
        while True:
            loop()
    except KeyboardInterrupt:
        logger.warning("Interrupted")
        GPIO.cleanup()
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
    except Exception as e:
        print(f"An error occurred: {e}")
    except:
        GPIO.cleanup()
        logger.error("Unexpected error:", sys.exc_info()[0])