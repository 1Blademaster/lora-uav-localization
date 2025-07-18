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



def init():
    global lora

    # configure RPi GPIO
    GPIO.setmode(GPIO.BCM)

    # initialise the SX1280 module
    lora = SX128XLT(SPI_BUS, SPI_CS, 8, BUSY_GPIO, pin_nreset = RESET_GPIO, pin_dio1 = DIO1_GPIO)
    logger.info("init done")
    # setup the LoRa configuration
    lora.setupLoRa(freq, offset, spreading_factor, bandwidth, code_rate)
    logger.info("init lora half done")
    lora.setBufferBaseAddress(1, 0)
    logger.info("init lora done")
    # debug configuration values
    lora.printModemSettings()
    lora.printOperatingSettings()

    logger.info("~~~ LoRa SX1280 Receiver is Ready ~~~")
    

def loop():
    global lora

    # wait for the packet to arrive with 60s timeout
    rxPacket = lora.receive(60, const.WAIT_RX)

    if len(rxPacket) > 0:
        # read RSSI value and SNR value
        packetRSSI = lora.readPacketRSSI()
        packetSNR = lora.readPacketSNR()

        logger.info(f"Received packet with RSSI {packetRSSI} and SNR {packetSNR}")
        logger.info(f"Received packet: {rxPacket}")


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