import matplotlib.pyplot as plt


class LiveGraph:
    def __init__(self, x_name, y_name):

        # Erstelle ein matplotlib-Plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Live Data")
        self.ax.set_xlabel(x_name)
        self.ax.set_ylabel(y_name)
        self.ax.grid(True)

    def update(self, data):
        # Speichern der aktuellen Titel und Achsenbeschriftungen
        current_title = self.ax.get_title()
        current_xlabel = self.ax.get_xlabel()
        current_ylabel = self.ax.get_ylabel()

        # Löschen des Plot-Inhalts
        self.ax.clear()

        # Wiederherstellung von Titel und Achsenbeschriftungen
        self.ax.set_title(current_title)
        self.ax.set_xlabel(current_xlabel)
        self.ax.set_ylabel(current_ylabel)
        self.ax.grid(True)

        if len(data) > 0:
            y_min_cutoff = -10000
            y_min = min(data)  # Untergrenze fix
            if y_min < y_min_cutoff:
                y_min = y_min_cutoff
            y_max = max(data) * 1.1  # etwas Puffer nach oben
            self.ax.set_ylim(bottom=y_min, top=y_max)
        else:
            # Wenn keine positiven Werte vorhanden sind (z. B. am Anfang), setze feste Achse
            self.ax.set_ylim(0, 1)

        # Plottet die übergebenen Daten
        self.ax.plot(data)
