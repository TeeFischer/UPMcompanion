import serial
import threading
import re
import time
import serial.tools.list_ports
from collections import deque
import struct
import zlib

from gui import SerialControlGUI  # eigene gui.py Datei
from graph import LiveGraph

# Seriellen Port einmal öffnen
ser = None
current_port = None
BAUD_RATE = 115200
backup_port = 'COM10'

startup = False

is_loads_checked = False
is_debug_checked = False

# Event zur Steuerung des Thread-Abbruchs vom Serial-Thread
stop_event = threading.Event()

# Datenpuffer der endlos viele Werte halten kann
loadcell_data = deque()
position_data = deque()
time_data = deque()
cycle_info = deque()

lost_lines = 0

# Funktion zum Erkennen eines verfügbaren Arduinos
def find_com_port():
    global current_port
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Hier können weitere Prüfungen erfolgen, ob der Port der richtige ist
        if 'Arduino' in port.description:  # Falls der Arduino im Gerätenamen auftaucht
            current_port = port.device
            return current_port  # Gibt den COM-Port zurück
    print(f"Fallback to {backup_port}")
    return backup_port  # Falls kein passender Port gefunden wurde


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
    except serial.SerialException as e:
        arduino_connected(False, e)


def check_loads():
    """Hilfsfunktion, die den Wert von gui.loads.get() sicher im Haupt-Thread abruft."""
    global is_loads_checked
    
    # print(gui.loads.get())
    is_loads_checked = gui.loads.get() == "1"
    return is_loads_checked


def check_debug():
    """Hilfsfunktion, die den Wert von gui.debug.get() sicher im Haupt-Thread abruft."""
    global is_debug_checked
    
    # print(gui.loads.get())
    is_debug_checked = gui.debug.get() == "1"
    return is_debug_checked


def extract_load_cell_value(data_string):
    """Extrahiert den Load_cell-Wert aus einem String"""
    global lost_lines

    # Gültigkeit prüfen
    if not data_string.startswith("<") or not data_string.endswith(">"):
        lost_lines += 1
        print(f"Ungültige Zeile in extract_load_cell_value N°{lost_lines}:{data_string}")
        return None
    
    # Start- und Endzeichen entfernen
    data_string = data_string[1:-1]
    

    try:
        # Split in Nutzdaten und Prüfsumme
        *data_parts, checksum_hex = data_string.split(",")
        if len(data_parts) != 3:
            print("Ungültiger Dateninhalt")
            return None

        data_payload = ",".join(data_parts)
        received_checksum = int(checksum_hex, 16)

        # Prüfsumme berechnen
        calculated_checksum = zlib.crc32(data_payload.encode('utf-8'))

        if received_checksum != calculated_checksum:
            print("Prüfsummenfehler!")
            return None

        # Werte extrahieren
        load = float(data_parts[0])
        position = float(data_parts[1])
        timestamp = int(data_parts[2])

        return load, position, timestamp

    except Exception as e:
        print(f"Fehler beim Parsen: {e}")
        return None


def extract_cycle_value(data_string):
    """Extrahiert die Zyklus-Info aus einem String"""
    # (data_string)
    if "Press cycle:" in data_string:
        try:
            cycle_match = re.search(r"Press cycle:\s*([\d.]+)", data_string)
            time_match = re.search(r"Time:\s*([\d.]+)", data_string)
            temp_match = re.search(r"Temp:\s*([\d.]+)", data_string)
            hum_match = re.search(r"Hum:\s*([\d.]+)", data_string)

            cycle_number = float(cycle_match.group(1)) if cycle_match else None
            time_value = float(time_match.group(1)) if time_match else None
            temperature_value = float(temp_match.group(1)) if temp_match else float('nan')
            humidity_value = float(hum_match.group(1)) if hum_match else float('nan')

            cycle_speed = "Slow" if "Slow" in data_string else "Fast"

            return cycle_number, cycle_speed, time_value, temperature_value, humidity_value
        except ValueError:
            print("Cycle extract: Value Error!")
            # Wenn der Wert nicht umgewandelt werden kann, gib None zurück
            return None
        except IndexError:
            print(f"Error in: {data_string}")
            return None
    print("Cycle: not identified!")
    return None


# Funktion zum Empfangen von Daten vom Arduino, diese Funktion ist eine Endlosschleife, die daher in einem eigenen
# Thread laufen sollte
def read_serial():
    global ser, startup, lost_lines
    try:
        if ser is None or not ser.is_open:  # wenn noch keine Serielle verbindung besteht
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=None)
            print("Connection opened")
        while not stop_event.is_set():
            if ser.in_waiting > 1000:
                print(f"Queue: {ser.in_waiting}")  #Debugging: Das hier zeigt den Empfangsbuffer auf der PC Seite
            
            arduino_connected(True)

            if ser.in_waiting > 0:
                decoded_data = ser.readline().decode('utf-8', errors='replace').strip()  # Daten empfangen und dekodieren
                # print(f"Empfangene Daten: {decoded_data}")  # Debug-Ausgabe

                # this catches the previously buffered communication which is not from this Arduino instance
                if not startup:
                    try:
                        if decoded_data.startswith("Starting..."):
                            startup = True
                    except Exception as e:
                        print(e)

                elif decoded_data.startswith("<"):
                    # Der String beginnt mit "Load:"
                    try:
                        values = extract_load_cell_value(decoded_data)
                        if values is not None:
                            loadcell_data.append(values[0])  # Neue Daten hinzufügen
                            position_data.append(values[1])  # Neue Daten hinzufügen
                            time_data.append(values[2])  # Neue Daten hinzufügen
                    except ValueError:
                        print("Error: Load Data corrupted")
                        pass  # Wenn keine gültige Zahl empfangen wurde, überspringen

                    gui.root.after(0, check_loads)
                    if is_loads_checked:
                        # gui.display_incoming_data(incoming_data) # diese Zeile wurde ersetzt durch gui.roo.after...,
                        # weil es sonst zu RuntimeErrors kommt
                        gui.root.after(0, gui.display_incoming_data, decoded_data)
                elif decoded_data.startswith("Debug:"):
                    gui.root.after(0, lambda: globals().update({"is_debug_checked": gui.debug.get() == "1"}))
                    if is_debug_checked:
                        gui.root.after(0, gui.display_incoming_data, decoded_data)
                elif decoded_data.startswith("Press cycle:"):
                    cycle_info.append(extract_cycle_value(decoded_data))
                    gui.root.after(0, gui.display_incoming_data, decoded_data)
                elif decoded_data:
                    lost_lines += 1
                    print(f"Ungültige Zeile in decoded_data N°{lost_lines}:{decoded_data}")
                    gui.root.after(0, gui.display_incoming_data, decoded_data)
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
gui = SerialControlGUI(send_command, try_connecting, current_port, list_com_ports, livePlot, loadcell_data,
                       position_data, time_data, cycle_info)

# Starten des Threads für die serielle Kommunikation
SERIAL_PORT = find_com_port()

serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# GUI starten
gui.start_gui()
