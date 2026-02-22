#include <stdio.h>
#include "nvs_flash.h"
#include "esp_log.h"
#include "esp_nimble_hci.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "services/gap/ble_svc_gap.h"

/*
 * This callback is executed once the BLE Host and Controller
 * are fully synchronized and ready to operate.
 * Advertising should be started from here.
 */
void ble_app_on_sync(void)
{
    ble_addr_t addr;

    /*
     * Generate a random static BLE address.
     * 1 → BLE_ADDR_RANDOM (static random address)
     * This avoids using the public MAC address.
     */
    ble_hs_id_gen_rnd(1, &addr);

    /* Set the generated random address as the device identity address */
    ble_hs_id_set_rnd(addr.val);

    /*
     * Define 128-bit UUID for iBeacon.
     * Here it is filled with 0x11 just for testing.
     * In real applications, use a proper UUID.
     */
    uint8_t uuid128[16];
    memset(uuid128, 0x11, sizeof(uuid128));

    /*
     * Configure iBeacon advertising payload:
     * uuid128  → 128-bit Proximity UUID
     * 2        → Major value
     * 10       → Minor value
     * -50      → Measured RSSI at 1 meter (calibration value)
     */
    ble_ibeacon_set_adv_data(uuid128, 2, 10, -50);

    /*
     * Advertising parameters:
     * Zero initialization = default settings:
     * - Undirected advertising
     * - General discoverable mode
     * - Connectable (if supported by payload)
     */
    struct ble_gap_adv_params adv_params = (struct ble_gap_adv_params){0};

    /*
     * Start advertising:
     * BLE_OWN_ADDR_RANDOM → Use random static address
     * NULL                → No direct advertising target
     * BLE_HS_FOREVER      → Advertise indefinitely
     */
    ble_gap_adv_start(BLE_OWN_ADDR_RANDOM, NULL, BLE_HS_FOREVER, &adv_params, NULL, NULL);
}

/*
 * NimBLE host task.
 * This runs the BLE host stack inside a FreeRTOS task.
 * It handles GAP/GATT events internally.
 */
void host_task(void *param)
{
    nimble_port_run(); // Start NimBLE event loop
}

/*
 * Main application entry point.
 * Initializes NVS, BLE controller, and NimBLE host stack.
 */
void app_main(void)
{
    /* Required for BLE (used internally for storage) */
    nvs_flash_init();

    /* Initialize BLE controller + HCI transport */
    esp_nimble_hci_init();

    /* Initialize NimBLE host stack */
    nimble_port_init();

    /* Register sync callback (called when BLE stack is ready) */
    ble_hs_cfg.sync_cb = ble_app_on_sync;

    /* Create FreeRTOS task for NimBLE host */
    nimble_port_freertos_init(host_task);
}