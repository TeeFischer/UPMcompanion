import tkinter as tk
from tkinter import filedialog
import csv
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys


class SerialControlGUI:
    def __init__(self, send_command, try_connecting, current_port, list_com_ports, plot, load_data, pos_data, time_data
                 , cycle_info):
        self.plot = plot
        self.figure = plot.fig
        self.ax = plot.ax
        self.data = load_data
        self.pos_data = pos_data
        self.time_data = time_data
        self.cycle_info = cycle_info
        self.send_command = send_command

        self.last_data = None    # speichert die zuletzt angezeigt Zeile, um Dopplungen zu erkennen
        self.counter = 0         # speichert wie oft die letzte Zeile gesendet wurde
        self.slider_value = 100  # speichert den Wert der Plotspanne

        self.connection_status = ""  # Variable, um den aktuellen Verbindungsstatus zu speichern

        def on_closing():
            print("Fenster wird geschlossen. Beende das Skript...")
            sys.exit()  # Beendet das Skript

        self.root = tk.Tk()

        # if window is closed, end programm execution
        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        # Alle GUI-Elemente jetzt innerhalb der __init__ Methode erstellen

        # Fenster erstellen mit Titel
        self.root.title("Arduino Steuerung mit Kommunikation")

        # Frame erstellen, in dem alles was links vom Plot liegen soll auftaucht
        frame_left = tk.Frame(self.root)

        # Frame für die horizontale Anordnung von Verbindungsstatus und Button (verbinden Befehl)
        frame_connection = tk.Frame(frame_left)

        self.label_connection = tk.Label(frame_connection, text="Arduino Getrennt")

        button_connect = tk.Button(frame_connection, text="Verbinden", command=lambda: try_connecting())

        # Liste der Optionen, die im Dropdown angezeigt werden
        port_optionen = list_com_ports()

        # Variable, die den aktuell ausgewählten Wert hält
        self.auswahl = tk.StringVar(self.root)
        self.auswahl.set(current_port)  # setze die Auswahl auf den derzeitigen Port

        # Erstelle das Dropdown-Menü (OptionMenu)
        dropdown = tk.OptionMenu(frame_connection, self.auswahl, *port_optionen)

        # Text-Widget für die Anzeige der Kommunikation
        self.text_box = tk.Text(frame_left, height=15, width=50, wrap=tk.WORD)

        # Frame für die horizontale Anordnung von PrintOut Funktionen
        frame_printout = tk.Frame(frame_left)

        # Erstellen von Variablen für die Checkbuttons
        self.duplikats = tk.IntVar()
        self.loads = tk.IntVar()
        self.debug = tk.IntVar()

        # Erstellen von Checkbuttons
        self.checkbutton1 = tk.Checkbutton(frame_printout, text="Duplikate", variable=self.duplikats)
        self.checkbutton2 = tk.Checkbutton(frame_printout, text="WaagenWerte", variable=self.loads)
        self.checkbutton3 = tk.Checkbutton(frame_printout, text="Debug", variable=self.debug)

        # Eingabefeld für benutzerdefinierten Befehl
        label_custom = tk.Label(frame_left, text="Geben Sie einen benutzerdefinierten Befehl ein:")

        # Frame für die horizontale Anordnung von Entry und Button (custom Befehl)
        frame_command = tk.Frame(frame_left)

        self.entry_command = tk.Entry(frame_command, width=50)  # Eingabefeld für den Befehl

        button_custom = tk.Button(frame_command, text="Befehl senden", command=self.send_user_command)

        # Frame für die horizontale Anordnung von Entry und Button (custom Befehl)
        frame_buttons = tk.Frame(frame_left)

        # Buttons zum Senden von Befehlen
        button_home = tk.Button(frame_buttons, text="Maschine Homen", command=lambda: self.send_command('h'))
        button_clEstop = tk.Button(frame_buttons, text="Lösche E-Stop", command=lambda: self.send_command('e'))
        button_cal = tk.Button(frame_buttons, text="Waage kalibrieren", command=lambda: self.send_command('r'))
        button_tare = tk.Button(frame_buttons, text="Waage tarieren", command=lambda: self.send_command('t'))
        button_scale = tk.Button(frame_buttons, text="Waage auslesen", command=lambda: self.send_command('a'))
        button_press = tk.Button(frame_buttons, text="Pressversuch (Weggest.)", command=lambda: self.send_command('p'))
        button_rel = tk.Button(frame_buttons, text="Bewege relativ um X", command=lambda: self.send_command('m'))
        button_fast = tk.Button(frame_buttons, text="Absolute Bewegung zu X", command=lambda: self.send_command('f'))

        # Erstelle einen Canvas für den matplotlib-Plot
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)  # matplotlib-Plot in Tkinter Canvas einbinden

        # Starte das Update des Graphen
        self.root.after(100, lambda: self.update_graph(100, self.slider_value))

        # Frame für die horizontale Anordnung von Slider und Co
        frame_slider = tk.Frame(self.root)

        # Erstelle einen Slider
        slider = tk.Scale(frame_slider, from_=self.slider_value, to=1, orient="horizontal", length=400, command=self.set_slider_value)
        slider.set(self.slider_value)

        # Erstelle ein Label zur Anzeige des Werts
        self.slider_label = tk.Label(frame_slider, text="Plotspanne: alles", width=20)

        # Erstelle einen Button zum export der Plotdaten
        button_export = tk.Button(frame_slider, text="-> Export", command=self.export_data)

        # Packing Befehle (definieren die Anordnung der GUI Elemente)
        frame_left.grid(row=0, column=0, padx=10)
        frame_connection.pack(pady=0)
        self.label_connection.pack(side=tk.LEFT, padx=5)
        dropdown.pack(side=tk.LEFT, padx=5)
        button_connect.pack(side=tk.LEFT, pady=0)
        self.text_box.pack(pady=5)
        frame_printout.pack(pady=0)
        self.checkbutton1.pack(side=tk.LEFT, padx=10)
        self.checkbutton2.pack(side=tk.LEFT, padx=10)
        self.checkbutton3.pack(side=tk.LEFT, padx=10)
        label_custom.pack(pady=2)
        frame_command.pack(pady=5)  # Custom command
        self.entry_command.pack(side=tk.LEFT, padx=5)
        button_custom.pack(side=tk.LEFT, pady=0)

        frame_buttons.pack(pady=5)
        button_home.grid(row=0, column=0, padx=10)
        button_clEstop.grid(row=0, column=1, padx=10)
        button_cal.grid(row=1, column=0, padx=10)
        button_tare.grid(row=1, column=1, padx=10)
        button_scale.grid(row=2, column=0, padx=10)
        button_press.grid(row=2, column=1, padx=10)
        button_rel.grid(row=3, column=0, padx=10)
        button_fast.grid(row=3, column=1, padx=10)
        self.canvas.get_tk_widget().grid(row=0, column=1, padx=10)
        frame_slider.grid(row=1, column=1, pady=10)
        slider.grid(row=0, column=1, padx=10)
        self.slider_label.grid(row=0, column=0, padx=10)
        button_export.grid(row=0, column=2, padx=10)

    def set_slider_value(self, val):
        if int(val) != 100:
            self.slider_label.config(text="Plotspanne: " + val + " Minuten")
        else:
            self.slider_label.config(text="Plotspanne: alles")
        self.slider_value = int(val)

    def update_connection_status(self, new_status, current_port):
        # Überprüfen, ob der Status der Gleiche ist
        if self.connection_status != new_status:
            # Zeige den neuen Status an
            self.label_connection.config(text=new_status)

            self.auswahl.set(current_port)  # setze die Auswahl auf den derzeitigen Port

            # Aktualisieren des gespeicherten Status
            self.connection_status = new_status

    def start_gui(self):
        # Dies startet die GUI in der SerialControlGUI-Klasse
        self.root.mainloop()

    def send_user_command(self, event=None):
        user_command = self.entry_command.get()
        self.send_command(user_command)
        self.entry_command.delete(0, tk.END)  # Löscht den gesamten Text im Entry-Feld

    def display_incoming_data(self, data):
        if data != self.last_data or self.duplikats.get():
            # Neue Zeile hinzufügen, wenn der Inhalt anders ist
            self.counter = 1  # Zähler zurücksetzen, da neue Daten empfangen wurden
            self.text_box.insert(tk.END, f"Empfangen: {data}\n")
            self.text_box.yview(tk.END)  # Automatisches Scrollen nach unten
            self.last_data = data  # Aktuelle Daten speichern
        else:
            # Die Zeile zählt nur hoch, wenn der Inhalt gleich bleibt
            self.counter += 1
            # Zeile aktualisieren, um den neuen Zähler anzuzeigen
            self.update_last_line()

    def update_last_line(self):
        """Aktualisiert die letzte Zeile mit dem neuen Zähler"""
        # Den Text aus der Textbox lesen
        lines = self.text_box.get("1.0", tk.END).strip().split("\n")

        if lines:
            # Die letzte Zeile bearbeiten, um den Zähler hinzuzufügen
            last_line = lines[-1]
            new_last_line = f"\nEmpfangen ({self.counter}): {last_line.split(': ', 1)[1]}\n"

            # Die letzte Zeile in der Textbox ersetzen
            self.text_box.delete(f"{len(lines)}.0", tk.END)  # Löschen der letzten Zeile
            self.text_box.insert(tk.END, new_last_line)  # Neue Zeile mit Zähler

    def display_send_data(self, data):
        self.text_box.insert(tk.END, f"Gesendet: {data}\n")
        self.text_box.yview(tk.END)  # Automatisches Scrollen nach unten

    # Funktion zum Aktualisieren des Graphen
    def update_graph(self, delay=0, spanne=100):
        if spanne == 100:
            plot_data = self.data
        else:
            plot_range = spanne*10*60  #eingestellteSpanne*10hz Messfrequenz*60 Sekunden
            # Wenn weniger als plot_range Werte vorhanden sind, wähle nur so viele wie möglich
            if len(self.data) < plot_range:
                plot_range = len(self.data)
            plot_data = list(self.data)[-plot_range:]

        self.plot.update(plot_data)  # Plottet die ausgewählten Daten
        self.canvas.draw()           # Canvas aktualisieren
        if not delay == 0:
            self.root.after(delay, lambda: self.update_graph(delay, self.slider_value))  # Alle 10 ms erneut aufrufen

    def export_data(self):
        print("Export gestartet")

        # Neues Toplevel-Fenster erstellen
        export_window = tk.Toplevel(self.root)
        export_window.title("Daten exportieren")

        # Label und Optionen für die Auswahl der zu exportierenden Daten
        label = tk.Label(export_window, text="Wählen Sie die Daten aus, die exportiert werden sollen:")
        label.pack(padx=10, pady=10)

        # Funktion für den Button
        def on_export_button_click():
            result = self.save_as_csv()  # Export ausführen und Rückmeldung erhalten

            # Erfolgs- oder Fehlermeldung
            if "Export erfolgreich" in result:
                success_label = tk.Label(export_window, text=result, fg="green")
                success_label.pack(padx=10, pady=10)

                # Fenster nach einer kurzen Verzögerung schließen
                export_window.after(2000, export_window.destroy)  # Schließt das Fenster nach 2 Sekunden
            else:
                error_label = tk.Label(export_window, text=result, fg="red")
                error_label.pack(padx=10, pady=10)

        # Button zum Starten des Exports
        save_button = tk.Button(export_window, text="CSV exportieren", command=on_export_button_click)
        save_button.pack(padx=10, pady=10)

    def export_data_old(self):
        print("Export started")
        # Neues Toplevel-Fenster erstellen
        export_window = tk.Toplevel(self.root)
        export_window.title("Daten exportieren")

        # Label und Optionen für die Auswahl der zu exportierenden Daten
        label = tk.Label(export_window, text="Wählen Sie die Daten aus, die exportiert werden sollen:")
        label.pack(padx=10, pady=10)

        # Eine Checkliste oder weitere Optionen hinzufügen, um die Auswahl zu treffen
        # Hier als Beispiel: Ein Button zum Speichern der CSV
        save_button = tk.Button(export_window, text="CSV exportieren", command=self.save_as_csv)
        save_button.pack(padx=10, pady=10)

    # Funktion zum Speichern der Daten als CSV, gibt zusätzlich eine Erfolg- oder Fehlermeldung zurück
    def save_as_csv(self):
        try:
            # Kopiere die deques in Listen, um sicherzustellen, dass die originalen deques nicht verändert werden
            pos_data_list = list(self.pos_data)
            data_list = list(self.data)
            time_list = list(self.time_data)
            cycle_list = list(self.cycle_info)

            save_data = list(zip(time_list, pos_data_list, data_list))  # Zusammenfügen der Daten

            # Dialog zum Speichern der Datei öffnen
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Dateien", "*.csv")])

            if file_path:
                # CSV-Datei speichern
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Zeit [in ms]", "Weg [in mm]", "Kraft [in gramms]", "Info"])  # Header hinzufügen

                    cycle_index = 0
                    for row in save_data:
                        time_value = row[0]
                        info = ' '  # Standardwert (leerer Platz)

                        while cycle_index < len(cycle_list) and cycle_list[cycle_index][2] <= time_value:
                            cycle_index += 1

                        if cycle_index > 0:
                            info = f"Cycle {int(cycle_list[cycle_index - 1][0])}: {cycle_list[cycle_index - 1][1]}"

                        writer.writerow(list(row) + [info])

                return "Export erfolgreich!"  # Erfolgreich abgeschlossen
            else:
                return "Export abgebrochen."  # Falls der Benutzer den Dialog abbricht
        except Exception as e:
            return f"Fehler: {str(e)}"  # Gibt die Fehlermeldung zurück
