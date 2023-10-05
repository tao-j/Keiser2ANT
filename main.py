import asyncio
import sys

from tx.ant import ANTTx
from tx.ble import BLETx
from tx.conv import ANTConv, BLEConv
from bike.keiser import KeiserBike
from bike.sim import SimCrankPowerEncoder


async def main(bike_id: int, mock: bool):
    ant_tx = ANTTx()
    ble_tx = BLETx()
    await ble_tx.setup()

    src = SimCrankPowerEncoder() if mock else KeiserBike(bike_id=bike_id)

    ant_bike_data = ANTConv(src)
    ble_bike_data = BLEConv(src)

    try:
        async with asyncio.TaskGroup() as g:
            g.create_task(src.loop())
            g.create_task(ant_bike_data.loop())
            g.create_task(ant_tx.loop(bike_data=ant_bike_data))
            g.create_task(ble_bike_data.loop())
            g.create_task(ble_tx.loop(bike_data=ble_bike_data))

    except asyncio.exceptions.CancelledError:
        print("Cancelled by user")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        bike_id = int(sys.argv[1])
        mock = False
    else:
        bike_id = 0
        mock = True

    asyncio.run(main(bike_id, mock))
