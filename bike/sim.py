import time, asyncio, random

from . import *


class SimBike(Bike):
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
