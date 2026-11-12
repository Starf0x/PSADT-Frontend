# Was ist neu

## 0.2.11
- Jedes Dateifeld in einem Schritt hat jetzt eine Schaltfläche Durchsuchen: Datei auf dem PC wählen, sie wird in einem Schritt hochgeladen und ausgewählt.
- Run EXE kann jetzt auch Programme starten, die auf jedem Windows-PC vorhanden sind, etwa winget, msiexec, PowerShell und cmd. Kein Hochladen nötig. winget wird automatisch gefunden, auch wenn Intune als SYSTEM installiert.
- Die App verwendet jetzt immer ein dunkles Design mit mehr Farbe und Tiefe.

## 0.2.0
- Änderungen an einem Paket werden jetzt kurz nach der Eingabe automatisch gespeichert. Beim Neuladen der Seite oder einem Neustart für ein Update geht nichts mehr verloren.
- Wenn Sie die Seite verlassen, während noch gespeichert wird, warnt Ihr Browser zuerst.

## 0.1.99
- Wenn eine neuere Version verfügbar ist, sehen Administratoren einen orangen Punkt bei System und einen Hinweis oben auf jeder Seite.
- Auf der Systemseite gibt es die Schaltfläche „Jetzt prüfen“, und die App sucht alle 15 Minuten statt stündlich nach neuen Versionen.

## 0.1.88
- Argumente, Pfade und Code in einem Schritt nutzen jetzt die volle Breite, damit lange Befehle gut lesbar sind.
- Unter den Argumenten klicken Sie auf {Files} oder eine hochgeladene Datei, um den vollständigen Pfad einzufügen, ohne ihn zu tippen.

## 0.1.77
- In den Argumenten eines Schritts können Sie {Files} für den Ordner Files des Pakets auf dem PC schreiben. Zum Beispiel: --msix-path "{Files}\app.msix".

## 0.1.66
- Benutzer haben jetzt einen vollständigen Namen neben dem Anmeldenamen. Er wird beim Anlegen eingetragen; jeder kann seinen Namen im eigenen Konto ändern.
- Neue Pakete tragen Ihren vollständigen Namen als Skriptautor ein.
- Beim Hochladen sehen Sie für jede Datei einen Fortschrittsbalken.
- Die Schaltfläche „Syntax prüfen“ funktioniert wieder auf Proxmox-Containern. Kann die Prüfung nicht laufen, erklärt die Meldung jetzt, dass es ein Serverproblem ist und kein Fehler in Ihrem Paket.

## 0.1.55
- Wenn ein Update bereitsteht, zeigt die Systemseite jetzt zuerst, was neu ist.
- Diese Hinweise sind in einfacher Sprache geschrieben, auf Englisch, Niederländisch und Deutsch.

## 0.1.44
- Jeder wählt seine eigene Sprache. Die Auswahl wird mit Ihrem Konto gespeichert und gilt auf jedem Computer.

## 0.1.33
- Der Tab Export prüft Ihr Paket vor dem Herunterladen. Rote Punkte müssen zuerst behoben werden; orange Punkte sind Tipps.
- Sie legen fest, wie lange hochgeladene Installationsdateien auf dem Server bleiben: immer, direkt nach dem Herunterladen oder einige Tage.
- Sie wählen den Standardordner für das Installationsprotokoll auf dem PC. Jedes Paket kann einen eigenen Ordner nutzen.
- Neues Symbol und ein frischeres, ruhigeres Aussehen.
- MSIX- und APPX-Dateien können jetzt hochgeladen werden.

## 0.1.22
- Die App gibt es auf Englisch, Niederländisch und Deutsch. Wählen Sie die Sprache unten im Menü.
- Container auf Proxmox können sich selbst aktualisieren: unter System auf „Installieren“ klicken.

## 0.1.11
- Die Installation auf Proxmox konnte mittendrin abbrechen. Das ist behoben.

## 0.1.0
- Installation auf Proxmox mit einem Befehl, wie bei den Community-Helper-Skripten.
