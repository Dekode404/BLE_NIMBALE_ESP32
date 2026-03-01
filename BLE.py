import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient


class BLETool:

    def __init__(self, root):
        self.root = root
        self.root.title("Professional BLE Desktop Tool")

        self.devices = []
        self.client = None

        # Persistent asyncio loop (FIXES event loop closed error)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        # ================= UI =================
        ttk.Button(root, text="Scan Devices", command=self.start_scan).pack(pady=5)

        self.device_list = tk.Listbox(root, width=70)
        self.device_list.pack()

        ttk.Button(root, text="Connect", command=self.connect_selected).pack(pady=5)

        self.tree = ttk.Treeview(root)
        self.tree.pack(fill="both", expand=True)

        ttk.Button(root, text="Open Characteristic", command=self.open_characteristic).pack(pady=5)

        self.log = tk.Text(root, height=10)
        self.log.pack(fill="both", expand=True)

    # ================= Async Scheduler =================
    def run_async(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    # ================= Scan =================
    def start_scan(self):
        self.device_list.delete(0, tk.END)
        self.run_async(self.scan())

    async def scan(self):
        devices = await BleakScanner.discover(timeout=5.0)
        self.devices = devices

        self.root.after(0, lambda: self.device_list.delete(0, tk.END))

        for idx, d in enumerate(devices):
            name = d.name if d.name else "Unknown"
            entry = f"{idx}: {name} ({d.address})"
            self.root.after(0, lambda e=entry: self.device_list.insert(tk.END, e))

    # ================= Connect =================
    def connect_selected(self):
        selection = self.device_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select device first")
            return

        device = self.devices[selection[0]]
        self.run_async(self.connect(device))

    async def connect(self, device):
        self.client = BleakClient(device.address)
        await self.client.connect()

        if not self.client.is_connected:
            self.root.after(0, lambda: self.log.insert(tk.END, "Connection failed\n"))
            return

        self.root.after(0, lambda: self.log.insert(tk.END, f"Connected to {device.name}\n"))
        self.root.after(0, lambda: self.tree.delete(*self.tree.get_children()))

        for service in self.client.services:
            service_name = service.description or "Custom Service"

            service_node = self.tree.insert(
                "", "end",
                text=service_name,
                values=(service.uuid, "")
            )

            for char in service.characteristics:
                char_name = char.description or "Custom Characteristic"
                properties = ", ".join(char.properties)

                self.tree.insert(
                    service_node,
                    "end",
                    text=char_name,
                    values=(char.uuid, properties)
                )

    # ================= Characteristic Window =================
    def open_characteristic(self):
        selected = self.tree.focus()
        if not selected:
            return

        item = self.tree.item(selected)
        values = item.get("values")

        if not values:
            return

        uuid = values[0]
        properties = values[1]

        char_window = tk.Toplevel(self.root)
        char_window.title(f"Characteristic {uuid}")

        ttk.Label(char_window, text=f"UUID: {uuid}").pack()

        # READ
        read_btn = ttk.Button(
            char_window,
            text="Read",
            command=lambda: self.run_async(self.read_char(uuid))
        )
        read_btn.pack(pady=5)

        if "read" not in properties:
            read_btn.state(["disabled"])

        # WRITE
        ttk.Label(char_window, text="Write Value:").pack()
        write_entry = ttk.Entry(char_window, width=40)
        write_entry.pack()

        format_var = tk.StringVar(value="ascii")

        ttk.Radiobutton(char_window, text="ASCII",
                        variable=format_var, value="ascii").pack()
        ttk.Radiobutton(char_window, text="HEX",
                        variable=format_var, value="hex").pack()

        write_btn = ttk.Button(
            char_window,
            text="Write",
            command=lambda: self.run_async(
                self.write_char(uuid, write_entry.get(), format_var.get())
            )
        )
        write_btn.pack(pady=5)

        if "write" not in properties:
            write_btn.state(["disabled"])

        # NOTIFY
        sub_btn = ttk.Button(
            char_window,
            text="Subscribe",
            command=lambda: self.run_async(self.subscribe(uuid))
        )
        sub_btn.pack(pady=5)

        unsub_btn = ttk.Button(
            char_window,
            text="Unsubscribe",
            command=lambda: self.run_async(self.unsubscribe(uuid))
        )
        unsub_btn.pack(pady=5)

        if "notify" not in properties:
            sub_btn.state(["disabled"])
            unsub_btn.state(["disabled"])

    # ================= BLE Operations =================
    async def read_char(self, uuid):
        value = await self.client.read_gatt_char(uuid)

        try:
            decoded = value.decode()
        except:
            decoded = value.hex()

        self.root.after(0, lambda:
            self.log.insert(tk.END, f"[READ] {uuid} → {decoded}\n"))

    async def write_char(self, uuid, value, fmt):
        if fmt == "ascii":
            data = value.encode()
        else:
            data = bytes.fromhex(value)

        await self.client.write_gatt_char(uuid, data)

        self.root.after(0, lambda:
            self.log.insert(tk.END, f"[WRITE] {uuid} → {value}\n"))

    async def subscribe(self, uuid):
        await self.client.start_notify(uuid, self.notification_handler)

        self.root.after(0, lambda:
            self.log.insert(tk.END, f"[SUBSCRIBE] {uuid}\n"))

    async def unsubscribe(self, uuid):
        await self.client.stop_notify(uuid)

        self.root.after(0, lambda:
            self.log.insert(tk.END, f"[UNSUBSCRIBE] {uuid}\n"))

    # Thread-safe notification handler
    def notification_handler(self, sender, data):
        try:
            decoded = data.decode()
        except:
            decoded = data.hex()

        self.root.after(0, lambda:
            self.log.insert(tk.END, f"[NOTIFY] {sender} → {decoded}\n"))


# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = BLETool(root)
    root.mainloop()