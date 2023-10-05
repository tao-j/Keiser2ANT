import random
import time
import asyncio
from ant_tx import AntPlusTx

from ble_tx import BLE_Tx
from util import *

# from keiser import KeiserBLEListener


class MockListener(DataSrc):
    async def loop(self, debug=False):
        init_t = time.time()
        wheel_count = CountGenerator()
        crank_count = CountGenerator()
        interval = 0.25
        while True:
            await asyncio.sleep(interval)
            this_t = time.time() - init_t

            rev = interval * 1.1
            wheel_count.add(rev * 2, this_t)
            crank_count.add(rev * 1, this_t)
            self.power = random.randint(120, 133)

            self.cr, self.cev = crank_count.get()
            self.wr, self.wev = wheel_count.get()
            self.cadence = crank_count.rpm

            # power events
            self.power_event_counts += 1
            self.cum_power += self.power

            if debug:
                print(
                    wheel_count.get(),
                    crank_count.get(),
                    self.power,
                    self.cadence,
                    this_t,
                )


class BLEConv:
    def __init__(self, data_src) -> None:
        self.data_src = data_src

    def get_wr(self):
        return uint32(self.data_src.wr)

    def get_cr(self):
        return uint16(self.data_src.cr)

    def get_wev(self):
        return uint16(self.data_src.wev)

    def get_cev(self):
        return uint16(self.data_src.cev)

    def get_power(self):
        return uint16(self.data_src.power)


class ANTConv:
    def __init__(self, data_src) -> None:
        self.data_src = data_src

    def get_event_count(self):
        return uint8(self.data_src.power_event_counts)

    def get_cum_power(self):
        return uint16(self.data_src.cum_power)

    def get_cadence(self):
        return uint8(self.data_src.cadence)

    def get_power(self):
        return uint16(self.data_src.power)

    def get_cum_rev_count(self):
        return uint16(self.data_src.wr)

    def get_event_time_ms(self):
        return uint16(self.data_src.wev)


async def main():
    ble_tx = BLE_Tx()
    await ble_tx.setup()
    ant_tx = AntPlusTx()

    dl = MockListener()
    # dl = KeiserBLEListener(bike_id=15)
    ble_bike_data = BLEConv(dl)
    ant_bike_data = ANTConv(dl)

    dl_task = asyncio.create_task(dl.loop(debug=True))
    ble_tx_task = asyncio.create_task(ble_tx.loop(bike_data=ble_bike_data))
    ant_tx_task = asyncio.create_task(ant_tx.loop(bike_data=ant_bike_data))

    try:
        await dl_task
        await ble_tx_task
        await ant_tx_task
    except asyncio.exceptions.CancelledError:
        print("Exiting")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
