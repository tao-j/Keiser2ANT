import usb
import struct
import time

from ant.core import driver, node, message, constants, resetUSB


class AntPlusTx:
    def __init__(self):
        devs = usb.core.find(find_all=True, idVendor=0x0FCF)
        for dev in devs:
            if dev.idProduct in [0x1008, 0x1009]:
                resetUSB.reset_USB_Device()
                time.sleep(1)
                stick = driver.USB2Driver(
                    log=None,
                    debug=False,
                    idProduct=dev.idProduct,
                    bus=dev.bus,
                    address=dev.address,
                )
                try:
                    print("found stick, opening...")
                    stick.open()
                except:
                    print("failed to open stick, trying next")
                    continue
                stick.close()
                break
        else:
            print("No ANT devices available")
            exit(1)
        antnode = node.Node(stick)
        print("Starting ANT node")
        antnode.start()

        SPEED_DEVICE_TYPE = 0x7B  # 8118
        # CADENCE_DEVICE_TYPE = 0x7A # 8102
        # SPEED_CADENCE_DEVICE_TYPE = 0x79  # 8086
        # FITNESS_EQUIPMENT_DEVICE_TYPE = 0x11
        POWER_DEVICE_TYPE = 0x0B
        SENSOR_ID = 3862

        print("Starting CSC/CP with ANT+ ID " + repr(SENSOR_ID))
        net_id = node.Network(constants.NETWORK_KEY_ANT_PLUS, "ZZ:ANT+")
        antnode.setNetworkKey(constants.NETWORK_NUMBER_PUBLIC, net_id)

        self.chans = []

        p_chan = antnode.getFreeChannel()
        p_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        p_chan.setID(POWER_DEVICE_TYPE, SENSOR_ID, 0)
        p_chan.period = 8182
        p_chan.frequency = 57
        p_chan.open()
        self.p_chan = p_chan
        self.chans.append(p_chan)

        c_chan = antnode.getFreeChannel()
        c_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        c_chan.setID(SPEED_DEVICE_TYPE, SENSOR_ID, 0)
        c_chan.period = 8118
        c_chan.frequency = 57
        c_chan.open()
        self.c_chan = c_chan
        self.chans.append(c_chan)

        # f_chan = antnode.getFreeChannel()
        # f_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        # f_chan.setID(FITNESS_EQUIPMENT_DEVICE_TYPE, SENSOR_ID, 0)
        # f_chan.period = 8192
        # f_chan.frequency = 57
        # f_chan.open()
        # self.f_chan = f_chan
        # self.chans.append(f_chan)

        self.node = antnode

    def send_msg(self, chan, payload):
        ant_msg = message.ChannelBroadcastDataMessage(chan.number, data=payload)
        self.node.send(ant_msg)

    async def loop(self, kl, pd):
        if True:
            while True:
                await kl.new_data.wait()
                # await asyncio.sleep(0.25)
                # kl.power = 11
                # kl.cadence = 222
                pd.feed(kl.power, kl.cadence)
                kl.new_data.clear()
                print(
                    f"Ver.{kl.version_minor}:"
                    f"{int(pd.power):3d} W {int(pd.cadence):3d} RPM {pd.cum_rev_count:5d} REV "
                    f"{pd.get_event_time_ms():5d} ms {pd.speed * 3.6 / 1.67:2.1f} mph",
                    end="\r",
                )

                PWR_PAGE_ID = 0x10
                payload = struct.pack(
                    "<BB" + "BB" + "HH",
                    *[
                        PWR_PAGE_ID,
                        pd.get_event_count(),
                        0xFF,  # Pedal power not used
                        pd.get_cadence(),
                        pd.get_cum_power(),
                        pd.get_power(),
                    ],
                )
                self.send_msg(self.p_chan, payload)

                DEFAULT_PAGE_ID = 0x00
                payload = struct.pack(
                    "<B" + "BH" + "HH",
                    DEFAULT_PAGE_ID,
                    0xFF,
                    0xFFFF,
                    pd.get_event_time_ms(),
                    pd.get_cum_rev_count(),
                )
                self.send_msg(self.c_chan, payload)

                # payload = bytearray(b"\x11")  # General Settings Page
                # payload.append(0xFF)
                # payload.append(0xFF)  # Cadence
                # payload.append(int(5 / 0.01) & 0xFF)
                # payload.append(0xFF)
                # payload.append(0x7F)
                # payload.append(int(kl.resistence * 2) & 0xFF)
                # payload.append(0x00)  # flags not used
                # ant_tx.send_f(payload)

                # payload = bytearray(b"\x19")  # FE power
                # payload.append(pd.power_event_counts & 0xFF)
                # payload.append(int(pd.cadence) & 0xFF)  # Cadence
                # payload.append(pd.cum_power & 0xFF)
                # payload.append(pd.cum_power >> 8)
                # payload.append(pd.power & 0xFF)
                # payload.append((pd.power >> 8) & 0x0F)
                # payload.append(0x00)  # flags not used
                # ant_tx.send_f(payload)

        # except asyncio.CancelledError:
        #     print("Exiting: cancelled")
        #     for chan in ant_tx.chans:
        #         chan.close()
        #     ant_tx.node.stop()
