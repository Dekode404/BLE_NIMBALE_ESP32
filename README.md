# ESP32 NimBLE iBeacon (ESP-IDF v5.x)

This project demonstrates how to configure an ESP32 as an iBeacon advertiser using the NimBLE BLE stack in ESP-IDF v5.x.

The firmware initializes the BLE controller and host stack, generates a random static address, configures an iBeacon payload, and advertises indefinitely.

## Features

- Uses NimBLE (BLE only) stack
- Random static BLE address
- Custom 128-bit UUID
- Configurable:
  - Major value
  - Minor value
  - Measured RSSI (Tx Power)
- Advertises indefinitely
- FreeRTOS-based host task

## Project Structure

```
BLE_NIMBLE_ESP32/
│
├── main/
│   ├── main.c
│   └── CMakeLists.txt
│
├── CMakeLists.txt
└── README.md
```

## Requirements

- ESP-IDF v5.x
- ESP32 board
- NimBLE enabled
- Bluetooth enabled in menuconfig

## Configuration (IMPORTANT)

Run:

```bash
idf.py menuconfig
```

Go to:

Component config → Bluetooth

Enable:

- [x] Enable Bluetooth
- [x] Host → NimBLE - BLE only

Disable:

- [ ] Bluedroid

## Dependencies

Your `main/CMakeLists.txt` must contain:

```cmake
idf_component_register(SRCS "main.c"
                      INCLUDE_DIRS "."
                      REQUIRES bt nvs_flash)
```

## How It Works

1. **NVS Initialization**  
   BLE stack internally uses NVS for storage.

   ```c
   nvs_flash_init();
   ```

2. **Controller + HCI Initialization**

   ```c
   esp_nimble_hci_init();
   ```

   Initializes BLE controller and HCI transport layer.

3. **NimBLE Host Initialization**

   ```c
   nimble_port_init();
   ```

   Initializes BLE host stack.

4. **Sync Callback**  
   Once the BLE stack is synchronized:
   - A random static address is generated
   - iBeacon advertising data is configured
   - Advertising starts

## iBeacon Parameters Used

| Parameter        | Value                    |
| ---------------- | ------------------------ |
| UUID             | 0x11 repeated (16 bytes) |
| Major            | 2                        |
| Minor            | 10                       |
| Measured RSSI    | -50 dBm                  |
| Advertising Mode | Undirected               |
| Duration         | Infinite                 |

## Advertising Flow

```
app_main()
    ↓
NVS init
    ↓
BLE controller init
    ↓
NimBLE host init
    ↓
Sync callback
    ↓
Set random address
    ↓
Set iBeacon payload
    ↓
Start advertising forever
```

## Build & Flash

```bash
idf.py build
idf.py flash monitor
```

## Testing the Beacon

Use any BLE scanner app:

- nRF Connect
- LightBlue
- BLE Scanner

You should see the ESP32 advertising as an iBeacon.

## Customization

To change UUID:

```c
memset(uuid128, 0x11, sizeof(uuid128));
```

Replace with your own 16-byte UUID.

To change Major / Minor:

```c
ble_ibeacon_set_adv_data(uuid128, MAJOR, MINOR, RSSI);
```

## Notes

- This example assumes `ble_ibeacon_set_adv_data()` is available.
- If using pure NimBLE without helper functions, you must manually build the manufacturer-specific advertising payload.
- Always calibrate the Measured RSSI value properly for production.

## License

For educational and development use.
