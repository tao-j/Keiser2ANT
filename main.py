import asyncio
import sys
import time

from util import *
from ant_tx import AntPlusTx
from keiser import KeiserBLEListener



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
