import matplotlib.pyplot as plt


class LiveGraph:
    def __init__(self, x_name, y_name):

        # Erstelle ein matplotlib-Plot
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Live Data")
        self.ax.set_xlabel(x_name)
        self.ax.set_ylabel(y_name)

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

        # Plottet die übergebenen Daten
        self.ax.plot(data)
