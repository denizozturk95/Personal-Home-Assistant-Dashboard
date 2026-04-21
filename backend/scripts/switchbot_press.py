import asyncio
import sys
from bleak import BleakClient

bot = "E6:55:84:06:3E:96" # mac addresss

async def press():
  async with BleakClient(bot) as client:
    await client.write_gatt_char(
        "cba20002-224d-11e6-9fb8-0002a5d5c51b",
        bytearray([0x57, 0x01, 0x00])
    )

def main() -> int:
    asyncio.run(press())
    return 0


if __name__ == "__main__":
    sys.exit(main())
