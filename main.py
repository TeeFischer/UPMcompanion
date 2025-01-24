import serial
import threading
import time
import serial.tools.list_ports
from collections import deque
from gui import SerialControlGUI  # eigene gui.py Datei
from graph import LiveGraph

# Seriellen Port und Baudrate definieren
current_port = None
BAUD_RATE = 115200

# Seriellen Port einmal öffnen
ser = None

is_loads_checked = False
is_debug_checked = False

# Event zur Steuerung des Thread-Abbruchs vom Serial-Thread
stop_event = threading.Event()

# Datenpuffer der endlos viele Werte halten kann
loadcell_data = deque()
position_data = deque()


# Funktion zum Erkennen eines verfügbaren Arduinos
def find_com_port():
    global current_port
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Hier können weitere Prüfungen erfolgen, ob der Port der richtige ist
        if 'Arduino' in port.description:  # Falls der Arduino im Gerätenamen auftaucht
            current_port = port.device
            return current_port  # Gibt den COM-Port zurück
    return None  # Falls kein passender Port gefunden wurde


# Funktion zum Auflisten der verfügbaren COM-Ports
def list_com_ports():
    ports = serial.tools.list_ports.comports()

    # Liste der Geräte (port.device) erstellen
    ports_list = [(port.device, port.description) for port in ports]

    # Liste der Tupel nach dem 'device' (port.device) sortieren
    sorted_ports = sorted(ports_list, key=lambda x: int(x[0][3:]) if x[0][3:].isdigit() else float('inf'))

    return sorted_ports


# Funktion zum Senden von Befehlen an den Arduino
def send_command(command):
    global ser
    try:
        if ser is None or not ser.is_open:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.write(command.encode())  # Befehl als Byte senden
        gui.display_send_data(command)
        time.sleep(0.1)  # Kurze Pause, damit der Arduino den Befehl verarbeiten kann
    except serial.SerialException as e:
        arduino_connected(False, e)


def check_loads():
    global is_loads_checked
    """Hilfsfunktion, die den Wert von gui.loads.get() sicher im Haupt-Thread abruft."""
    # print(gui.loads.get())
    is_loads_checked = gui.loads.get() == "1"
    return is_loads_checked


def check_debug():
    global is_debug_checked
    """Hilfsfunktion, die den Wert von gui.loads.get() sicher im Haupt-Thread abruft."""
    # print(gui.loads.get())
    is_debug_checked = gui.debug.get() == "1"
    return is_debug_checked


def extract_load_cell_value(data_string):
    """Extrahiert den Load_cell-Wert aus einem String"""
    if "Load_cell:" in data_string:
        try:
            # Extrahiere den Wert nach "Load_cell: " und konvertiere ihn in eine float-Zahl
            load_cell_value = float(data_string.split("Load_cell:")[1].split()[0])
            position_value = float(data_string.split("Position:")[1].split()[0])
            return load_cell_value, position_value
        except ValueError:
            # Wenn der Wert nicht umgewandelt werden kann, gib None zurück
            return None
    return None


# Funktion zum Empfangen von Daten vom Arduino, diese Funktion ist eine Endlosschleife, die daher in einem eigenen
# Thread laufen sollte
def read_serial():
    global ser
    try:
        if ser is None or not ser.is_open:  # wenn noch keine Serielle verbindung besteht
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        while not stop_event.is_set():
            arduino_connected(True)

            if ser.in_waiting > 0:
                incoming_data = ser.readline().decode('utf-8',
                                                      errors='ignore').strip()  # Daten empfangen und dekodieren

                if incoming_data.startswith("Load_cell:"):
                    # Der String beginnt mit "Load_cell:"
                    try:
                        values = extract_load_cell_value(incoming_data)
                        if values is not None:
                            loadcell_data.append(values[0])  # Neue Daten hinzufügen
                            position_data.append(values[1])  # Neue Daten hinzufügen
                    except ValueError:
                        print("Error: Load Data corrupted")
                        pass  # Wenn keine gültige Zahl empfangen wurde, überspringen

                    gui.root.after(0, check_loads)
                    if is_loads_checked:
                        # gui.display_incoming_data(incoming_data) # diese Zeile wurde ersetzt durch gui.roo.after...,
                        # weil es sonst zu RuntimeErrors kommt
                        gui.root.after(0, gui.display_incoming_data, incoming_data)
                elif incoming_data.startswith("Debug:"):
                    gui.root.after(0, lambda: globals().update({"is_debug_checked": gui.debug.get() == "1"}))
                    if is_debug_checked:
                        gui.root.after(0, gui.display_incoming_data, incoming_data)
                elif incoming_data:
                    gui.root.after(0, gui.display_incoming_data, incoming_data)
            time.sleep(0.01)  # Kurze Pause, damit GUI responsive bleibt
    except serial.SerialException as e:
        arduino_connected(False, e)


# Funktion zum Verbindungsaufbau
def try_connecting():
    global ser
    try:
        if ser.is_open:
            arduino_connected(True)
        else:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            stop_event.clear()  # Lösche das Event
            serial_thread.start()

    except serial.SerialException as e:
        arduino_connected(False, e)


# Funktion um Feedback in GUI und print Befehlen zu geben, wie der Verbindungsstatus ist
def arduino_connected(connected, exception=None):
    global current_port
    global SERIAL_PORT
    if connected:
        current_port = SERIAL_PORT
        gui.update_connection_status(f"Arduino Verbunden", current_port)
    else:
        current_port = None
        gui.update_connection_status(f"Arduino Getrennt", current_port)
        gui.display_incoming_data(f"System: Fehler beim Verbinden mit dem Arduino: {exception}")
        print(f"Fehler beim Verbinden mit dem Arduino: {exception}")


# Live Graphen erstellen
livePlot = LiveGraph("Zeit", "Kraft [in gramm]")

# GUI erstellen
gui = SerialControlGUI(send_command, try_connecting, current_port, list_com_ports, livePlot, loadcell_data, position_data)

# Starten des Threads für die serielle Kommunikation
SERIAL_PORT = find_com_port()

serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# GUI starten
gui.start_gui()
