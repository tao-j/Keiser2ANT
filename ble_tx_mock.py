import random
import time
import asyncio

from ble_tx import BLE_Tx
from keiser import KeiserBLEListener

class MockDataRx:
    def __init__(self) -> None:
        self.rev_float = 0
        self.rev_event = 0
        self.event_time_ms = 0
        self.notify = False

    def add(self, inc, now):
        self.rev_float += inc

        diff = self.rev_float - self.rev_event
        if diff >= 1:
            # print("diff", diff, self.event_time_ms)
            self.event_time_ms = (
                now * 1024
                - (now * 1024 - self.event_time_ms) * (diff - int(diff)) / diff
            )

            self.rev_event = int(self.rev_float)
            self.notify = True
        # else:
        #     self.notify = False

    def get(self):
        return self.rev_event & 0xFFFF, int(self.event_time_ms) & 0xFFFF


class BikeData:
    def __init__(self) -> None:
        self.cr = 0
        self.cev = 0
        self.wr = 0
        self.wev = 0
        self.power = 0

    async def loop(self):
        last_t = time.time()
        wheel_rev_cls = MockDataRx()
        crank_rev_cls = MockDataRx()
        interval = 0.25
        while True:
            await asyncio.sleep(interval)
            this_t = time.time() - last_t

            rev = interval * 1.1
            wheel_rev_cls.add(rev * 2, this_t)
            crank_rev_cls.add(rev * 1, this_t)

            self.cr, self.cev = crank_rev_cls.get()
            self.wr, self.wev = wheel_rev_cls.get()
            self.power = random.randint(120, 133)

            print(wheel_rev_cls.get(), crank_rev_cls.get(), self.power)

class BikeDataKS(BikeData):
    def __init__(self, kl) -> None:
        self.kl = kl
        super().__init__()

    # async def loop(self):
    #     self.

async def main():
    ble_tx = BLE_Tx()
    await ble_tx.setup()
    kl = KeiserBLEListener(bike_id=15)
    bike_data = BikeData()
    # bike_data = BikeDataKS(kl)

    keiser_rx_task = asyncio.create_task(kl.loop())
    ble_tx_task = asyncio.create_task(ble_tx.loop(bike_data=bike_data))
    bike_data_task = asyncio.create_task(bike_data.loop())

    try:
        await ble_tx_task
        await bike_data_task
        await keiser_rx_task
    except asyncio.exceptions.CancelledError:
        print("CancelledError")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
