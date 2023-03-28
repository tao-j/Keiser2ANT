"""
Example for a BLE 4.0 Server using a GATT dictionary of services and
characteristics
"""

import logging
import asyncio
import threading

from typing import Any, Dict

from bless import (  # type: ignore
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions
        )

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=__name__)
trigger: asyncio.Event = asyncio.Event()


def read_request(
        characteristic: BlessGATTCharacteristic,
        **kwargs
        ) -> bytearray:
    logger.debug(f"Reading {characteristic.value}")
    return characteristic.value


def write_request(
        characteristic: BlessGATTCharacteristic,
        value: Any,
        **kwargs
        ):
    characteristic.value = value
    logger.debug(f"Char value set to {characteristic.value}")
    if characteristic.value == b'\x0f':
        logger.debug("Nice")
        trigger.set()


async def run(loop):
    trigger.clear()

    # Instantiate the server
    gatt: Dict = {
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD": {
                "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B": {
                    "Properties": (GATTCharacteristicProperties.read |
                                   GATTCharacteristicProperties.write |
                                   GATTCharacteristicProperties.indicate),
                    "Permissions": (GATTAttributePermissions.readable |
                                    GATTAttributePermissions.writeable),
                    "Value": None
                }
            },
            "00001816-0000-1000-8000-00805f9b34fb": {
                "00002a5b-0000-1000-8000-00805f9b34fb": { # CSC Measurement
                    "Properties": GATTCharacteristicProperties.notify |
                                   GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x00\x00\x00\x00')
                },
                "00002a5c-0000-1000-8000-00805f9b34fb": { # CSC Feature
                    "Properties": GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x69')
                },
                "00002a5d-0000-1000-8000-00805f9b34fb": { # Sensor Location
                    "Properties": GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x0d')
                },
            },
            "00001818-0000-1000-8000-00805f9b34fb": { # Cycling Power Service
                "00002a63-0000-1000-8000-00805f9b34fb": { # Cycling Power Measurement
                    "Properties": (GATTCharacteristicProperties.notify |
                                   GATTCharacteristicProperties.read),
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x08\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x08\x00')
                },
                # "00002a64-0000-1000-8000-00805f9b34fb": { # Cycling Power Vector
                #     "Properties": GATTCharacteristicProperties.read,
                #     "Permissions": GATTAttributePermissions.readable,
                #     "Value": bytearray(b'\x00\x00\x00\x00')
                # },
                "00002a65-0000-1000-8000-00805f9b34fb": { # Cycling Power Feature
                    "Properties": GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x08\x00\x00\x00')
                },
                "00002a5d-0000-1000-8000-00805f9b34fb": { # Sensor Location
                    "Properties": GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x0d')
                },
            }
        }
    # https://github.com/zacharyedwardbull/pycycling/blob/master/pycycling/cycling_power_service.py
    my_service_name = "Bike Power Service"
    server = BlessServer(name=my_service_name, loop=loop)
    server.read_request_func = read_request
    server.write_request_func = write_request

    for service in gatt:
        await server.add_new_service(service)
        for characteristic in gatt[service]:
            await server.add_new_characteristic(
                    service,
                    characteristic,
                    gatt[service][characteristic]["Properties"],
                    gatt[service][characteristic]["Value"],
                    gatt[service][characteristic]["Permissions"],
                    )
    # await server.add_gatt(gatt)
    await server.start()
    # logger.debug(server.get_characteristic(
        # "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"))
    # logger.debug("Advertising")
    # logger.info("Write '0xF' to the advertised characteristic: " +
    #             "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B")
    # await trigger.wait()
    # await asyncio.sleep(2)
    logger.debug("Updating")
    # server.get_characteristic("51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B").value = (
    #         bytearray(b"i")
    #         )
    server.update_value(
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD",
            "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
            )
    await asyncio.sleep(5000)
    await server.stop()

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))