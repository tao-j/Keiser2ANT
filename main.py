import asyncio
import sys

from tx.ant import AntPlusTx
from tx.ble import BLETx
from tx.conv import ANTConv, BLEConv
from bike.keiser import KeiserBike
from bike.sim import SimBike


async def main(bike_id: int, mock: bool):
    ble_tx = BLETx()
    await ble_tx.setup()
    ant_tx = AntPlusTx()

    src = SimBike() if mock else KeiserBike(bike_id=bike_id)

    ble_bike_data = BLEConv(src)
    ant_bike_data = ANTConv(src)
    src_task = asyncio.create_task(src.loop(debug=True))
    ble_tx_task = asyncio.create_task(ble_tx.loop(bike_data=ble_bike_data))
    ant_tx_task = asyncio.create_task(ant_tx.loop(bike_data=ant_bike_data))

    try:
        await src_task
        await ble_tx_task
        await ant_tx_task
    except asyncio.exceptions.CancelledError:
        print("Closing ANT+ Channels..... ")
        for chan in ant_tx.chans:
            chan.close()
        ant_tx.node.stop()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        bike_id = int(sys.argv[1])
        mock = False
    else:
        bike_id = 0
        mock = True

    asyncio.run(main(bike_id, mock))
