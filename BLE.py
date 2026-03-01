import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "MY BLE DEVICE"
MANUFACTURER_UUID = "00002a29-0000-1000-8000-00805f9b34fb"


async def find_device():
    print("Scanning for device...")
    devices = await BleakScanner.discover(timeout=5.0)

    for d in devices:
        if d.name == DEVICE_NAME:
            print(f"Found device: {d.name} ({d.address})")
            return d

    return None


async def main():
    device = await find_device()

    if device is None:
        print("Device not found.")
        return

    async with BleakClient(device.address) as client:
        print("Connected:", client.is_connected)

        # Read Manufacturer Name characteristic
        value = await client.read_gatt_char(MANUFACTURER_UUID)

        manufacturer_name = value.decode("utf-8")
        print("Manufacturer Name:", manufacturer_name)


if __name__ == "__main__":
    asyncio.run(main())