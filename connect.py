import tkinter as tk
from tkinter import messagebox, ttk
import serial
import serial.tools.list_ports
import time
import threading

class SmartPillBoxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Pill Box Controller")
        self.esp32 = None
        self.running = True

        # Create Widgets
        self.create_widgets()

        # Populate available serial ports
        self.populate_ports()

        # Start log listener in a separate thread
        self.log_thread = threading.Thread(target=self.listen_serial, daemon=True)
        self.log_thread.start()

    def create_widgets(self):
        # Frame for Connection
        connection_frame = tk.LabelFrame(self.root, text="Connection", padx=10, pady=10)
        connection_frame.pack(padx=10, pady=5, fill="x")

        # Serial Port Selection
        tk.Label(connection_frame, text="Select Port:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.port_var = tk.StringVar()
        self.port_menu = ttk.Combobox(connection_frame, textvariable=self.port_var, state="readonly")
        self.port_menu.grid(row=0, column=1, padx=5, pady=5)

        # Refresh Ports Button
        refresh_button = tk.Button(connection_frame, text="Refresh Ports", command=self.populate_ports)
        refresh_button.grid(row=0, column=2, padx=5, pady=5)

        # Baud Rate Entry
        tk.Label(connection_frame, text="Baud Rate:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.baud_entry = tk.Entry(connection_frame, width=10)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Connect/Disconnect Button
        self.connect_button = tk.Button(connection_frame, text="Connect", command=self.connect_to_esp32)
        self.connect_button.grid(row=1, column=2, padx=5, pady=5)

        # Frame for Controls
        control_frame = tk.LabelFrame(self.root, text="Controls", padx=10, pady=10)
        control_frame.pack(padx=10, pady=5, fill="x")

        # Set Current Time
        tk.Label(control_frame, text="Set Current Time (HH:MM):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.time_entry = tk.Entry(control_frame, width=15)
        self.time_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.set_time_button = tk.Button(control_frame, text="Update Time", command=self.set_time, state=tk.DISABLED)
        self.set_time_button.grid(row=0, column=2, padx=5, pady=5)

        # Add Single Pill Time
        tk.Label(control_frame, text="Add Single Pill Time (HH:MM):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.pill_time_entry = tk.Entry(control_frame, width=15)
        self.pill_time_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.add_pill_button = tk.Button(control_frame, text="Add Pill Time", command=self.add_pill_time, state=tk.DISABLED)
        self.add_pill_button.grid(row=1, column=2, padx=5, pady=5)

        # Set Entire Schedule
        tk.Label(control_frame, text="Set Entire Schedule (e.g., 08:00 12:30 18:00):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.schedule_entry = tk.Entry(control_frame, width=40)
        self.schedule_entry.grid(row=2, column=1, padx=5, pady=5, columnspan=1, sticky="w")
        self.set_schedule_button = tk.Button(control_frame, text="Set Schedule", command=self.set_schedule, state=tk.DISABLED)
        self.set_schedule_button.grid(row=2, column=2, padx=5, pady=5)

        # Reset Alarm Button
        self.reset_alarm_button = tk.Button(control_frame, text="Reset Alarm", command=self.reset_alarm, state=tk.DISABLED)
        self.reset_alarm_button.grid(row=3, column=1, padx=5, pady=5)

        # Frame for Logs
        log_frame = tk.LabelFrame(self.root, text="Logs", padx=10, pady=10)
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # Communication Log
        tk.Label(log_frame, text="Communication Log:").pack(anchor="w")
        self.text_area = tk.Text(log_frame, width=80, height=10, state=tk.DISABLED)
        self.text_area.pack(pady=5)

        # Pill Taken Log
        tk.Label(log_frame, text="Pill Taken Log:").pack(anchor="w")
        columns = ("Pill Time", "Taken At")
        self.log_table = ttk.Treeview(log_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.log_table.heading(col, text=col)
            self.log_table.column(col, width=150, anchor="center")
        self.log_table.pack(pady=5, fill="x")

        # Exit Button
        exit_button = tk.Button(self.root, text="Exit", command=self.close_app)
        exit_button.pack(pady=10)

    def populate_ports(self):
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports]
        self.port_menu['values'] = available_ports
        if available_ports:
            self.port_menu.current(0)
        else:
            self.port_menu.set("No ports available")

    def connect_to_esp32(self):
        if self.esp32 and self.esp32.is_open:
            self.disconnect_serial()
            return

        port = self.port_var.get()
        baudrate = self.baud_entry.get()

        if not port or port == "No ports available":
            messagebox.showerror("Connection Error", "No available serial ports.")
            return

        try:
            self.esp32 = serial.Serial(port=port, baudrate=int(baudrate), timeout=1)
            time.sleep(2)  # Allow ESP32 to initialize
            self.log_message(f"Connected to {port} at {baudrate} baud.")
            self.connect_button.config(text="Disconnect")
            self.enable_controls(True)
            self.send_initial_connection()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.esp32 = None

    def disconnect_serial(self):
        if self.esp32 and self.esp32.is_open:
            self.esp32.close()
            self.log_message("Disconnected from serial port.")
        self.esp32 = None
        self.connect_button.config(text="Connect")
        self.enable_controls(False)

    def enable_controls(self, enable=True):
        state = tk.NORMAL if enable else tk.DISABLED
        self.set_time_button.config(state=state)
        self.add_pill_button.config(state=state)
        self.set_schedule_button.config(state=state)
        self.reset_alarm_button.config(state=state)

    def send_initial_connection(self):
        pass

    def set_time(self):
        current_time = self.time_entry.get().strip()
        if self.validate_time_format(current_time):
            command = f"SET_TIME {current_time}"
            self.send_command(command)
        else:
            messagebox.showerror("Input Error", "Please enter time in HH:MM format.")

    def add_pill_time(self):
        pill_time = self.pill_time_entry.get().strip()
        if self.validate_time_format(pill_time):
            command = f"ADD_PILL {pill_time}"
            self.send_command(command)
            self.pill_time_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Input Error", "Please enter pill time in HH:MM format.")

    def set_schedule(self):
        schedule = self.schedule_entry.get().strip()
        times = schedule.split()
        if all(self.validate_time_format(t) for t in times):
            formatted_times = ' '.join(times)
            command = f"SET_SCHEDULE {formatted_times}"
            self.send_command(command)
            self.schedule_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Input Error", "Please enter all times in HH:MM format, separated by spaces.")

    def reset_alarm(self):
        command = "RESET_ALARM"
        self.send_command(command)

    def send_command(self, command):
        if self.esp32 and self.esp32.is_open:
            try:
                self.esp32.write((command + "\n").encode())
                self.log_message(f"Sent: {command}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send command: {e}")
        else:
            messagebox.showerror("Connection Error", "ESP32 is not connected.")

    def listen_serial(self):
        while self.running:
            if self.esp32 and self.esp32.is_open:
                try:
                    if self.esp32.in_waiting > 0:
                        line = self.esp32.readline().decode().strip()
                        if line:
                            self.handle_serial_input(line)
                except Exception as e:
                    self.log_message(f"Serial read error: {e}")
                    self.disconnect_serial()
            time.sleep(0.1)

    def handle_serial_input(self, line):
        self.log_message(f"Received: {line}")
        if line.startswith("LOG_PILL_TAKEN"):
            parts = line.split()
            if len(parts) == 2:
                pill_time = parts[1]
                taken_at = time.strftime("%Y-%m-%d %H:%M:%S")
                self.log_table.insert("", "end", values=(pill_time, taken_at))
        elif line.startswith("Buzzer Off"):
            self.log_message("Alarm successfully reset.")
        else:
            self.log_message(line)

    def log_message(self, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{message}\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

    def validate_time_format(self, time_str):
        if len(time_str) != 5 or time_str[2] != ':':
            return False
        try:
            h, m = map(int, time_str.split(':'))
            return 0 <= h < 24 and 0 <= m < 60
        except:
            return False

    def close_app(self):
        self.running = False
        if self.esp32 and self.esp32.is_open:
            self.esp32.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartPillBoxGUI(root)
    root.mainloop()
