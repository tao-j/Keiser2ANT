import asyncio
import sys
import time

from util import *
from ant_tx import AntPlusTx
from keiser import KeiserBLEListener


class BikeDataByIntegration:
    def __init__(self):
        # last feed readings to be sent
        self.power = 0
        self.cadence = 0
        self.speed = 0

        # power events
        self.power_event_counts = 0
        self.cum_power = 0

        # speed
        self.init_time = time.time()
        self.last_feed_time = self.init_time
        self.cum_rev = 0
        self.cum_rev_count = 0
        self.event_time_ms = 0

    def get_event_count(self):
        return uint8(self.power_event_counts)

    def get_cadence(self):
        return uint8(self.cadence)

    def get_power(self):
        return uint16(self.power)

    def get_cum_power(self):
        return uint16(self.cum_power)

    def get_event_time_ms(self):
        return uint16(self.event_time_ms)

    def get_cum_rev_count(self):
        return uint16(self.cum_rev_count)

    def power_to_speed(self, power):
        """
        power in watts
        speed in m/s
        """
        Cd = 0.9
        A = 0.5
        rho = 1.225
        Crr = 0.0045
        F_gravity = 75 * 9.81

        # Define the power equations
        coeff_P_drag = 0.5 * Cd * A * rho  # * v**3
        coeff_P_roll = Crr * F_gravity  # * v

        # P_drag v^3 + P_roll v + (-power) = 0
        p = coeff_P_roll / coeff_P_drag
        q = -power / coeff_P_drag

        delta = p**3 / 27 + q**2 / 4
        cubic_root = lambda x: x ** (1.0 / 3) if x > 0 else -((-x) ** (1.0 / 3))
        u = cubic_root(-q / 2 + delta ** (1.0 / 2))
        v = cubic_root(-q / 2 - delta ** (1.0 / 2))

        return u + v

    def feed(self, power, cadence):
        """
        feed instantaneous power/cadence readings and infer bike speed
        also update the cumulative power and cadence
        """
        speed = self.power_to_speed(power)
        # print(f"speed: {self.speed} m/s")

        now = time.time()
        dt = now - self.last_feed_time
        self.last_feed_time = now

        # speed events
        # set wheel to 700c*25 or ~2096mm
        WHEEL_CIRCUMFERENCE = 2.096
        self.cum_rev += (speed + self.speed) / 2 * dt / WHEEL_CIRCUMFERENCE
        diff = self.cum_rev - self.cum_rev_count
        if diff >= 1:
            self.event_time_ms = now * 1024 - (
                now * 1024 - self.event_time_ms
            ) / diff * (diff - int(diff))
            self.cum_rev_count = int(self.cum_rev)

        # power events
        self.power_event_counts += 1
        self.cum_power += power

        self.cadence = cadence
        self.power = power
        self.speed = speed


async def main(bike_id: int):
    ant_tx = AntPlusTx()
    kl = KeiserBLEListener(bike_id=bike_id)

    bike_data = BikeDataByIntegration()
    keiser_rx_task = asyncio.create_task(kl.loop())
    ant_tx_task = asyncio.create_task(ant_tx.loop(kl, bike_data))

    try:
        await keiser_rx_task
        await ant_tx_task
    except asyncio.exceptions.CancelledError:
        print("Exiting--------------------------------------")
        for chan in ant_tx.chans:
            chan.close()
        ant_tx.node.stop()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        bike_id = int(sys.argv[1])
    else:
        bike_id = 1

    asyncio.run(main(bike_id))
