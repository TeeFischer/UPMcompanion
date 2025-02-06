# UPMcompanion
GUI zum anzeigen und vereinfachen der seriellen Kommunikation mit einem Arduino auf dem UPMmaster läuft

Python Umgebung vorbereiten
-	„pip install pyserial“ oder mit Python Packages Tab
-	„pip install matplotlib“


Weitere Hinweise
-	Sorge dafür, dass der COM-Port nicht von einem anderen Programm genutzt wird  
  o	Und auch nur eine Serielle Port instanz im Code genutzt wird (deshalb global ser)
- zum export in exe
  - pip install pyinstaller
  - pyinstaller --onefile main.py

TODO: (bzw. Bugs)
-	Daten Export, Datensatz auswählbar gestalten
-	(known Bug) Checkbuttons funktionieren nicht
-	(known Bug) Verbindungsbutton (oben im Fenster) funktioniert nicht
