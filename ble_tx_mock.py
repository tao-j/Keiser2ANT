import random
import time
import asyncio

from ble_tx import BLE_Tx
from util import *

# from keiser import KeiserBLEListener


class CountGenerator:
    """Generates discrete count data and closest event time from continuous value

    Note that in real world, when the count up event happens, an interrupt is triggered, then the precise event time is recorded. However here, the event time is an approximation with the assumption that the value increases steadily.
    """

    def __init__(self) -> None:
        self.val_float = 0
        self.val_int = 0
        self.event_time_ms = 0
        self.notify = False

    def add(self, inc, now):
        self.val_float += inc
        self.round(now)

    def set(self, val, now):
        self.val_float = val
        self.round(now)

    def get(self):
        return self.val_int, self.event_time_ms

    def round(self, now):
        diff = self.val_float - self.val_int
        if diff >= 1:
            self.event_time_ms = (
                now * 1024
                - (now * 1024 - self.event_time_ms) * (diff - int(diff)) / diff
            )

            self.val_int = int(self.val_float)
            # self.notify = True
        # else:
        #     self.notify = False


class MockListener:
    def __init__(self) -> None:
        self.cr = 0
        self.cev = 0
        self.wr = 0
        self.wev = 0
        self.power = 0

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

            if debug:
                print(wheel_count.get(), crank_count.get(), self.power, this_t)


class Mock2BLE:
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


async def main():
    ble_tx = BLE_Tx()
    await ble_tx.setup()
    dl = MockListener()
    # dl = KeiserBLEListener(bike_id=15)
    bike_data = Mock2BLE(dl)

    dl_task = asyncio.create_task(dl.loop(debug=True))
    ble_tx_task = asyncio.create_task(ble_tx.loop(bike_data=bike_data))

    try:
        await ble_tx_task
        await dl_task
    except asyncio.exceptions.CancelledError:
        print("Exiting")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
