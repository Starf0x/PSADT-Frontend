# Was ist neu

## 0.3.33
- Pre, Main und Post sind jetzt jeweils ein eigener Block, mit der Schaltfläche zum Hinzufügen im zugehörigen Block ("Schritt zu Main hinzufügen").

## 0.3.22
- Große Dateien werden jetzt in Stücken von 5 MB hochgeladen. Uploads über einen Reverse Proxy oder Tunnel mit Größenlimit (etwa Zoraxy oder Cloudflare) bleiben nicht mehr hängen. Ein fehlgeschlagenes Stück wird automatisch erneut gesendet.

## 0.3.11
- Ein hängender Upload bricht jetzt nach einer Minute ohne Fortschritt ab und nennt den Grund (oft ein Reverse Proxy oder Tunnel mit Größenlimit oder eine volle Festplatte), statt endlos zu warten.

## 0.3.0
- Nur Administratoren können jetzt Pakete löschen. Bearbeiter können sie weiterhin anlegen und ändern.

## 0.2.99
- Behoben: Die tägliche Meldung konnte von der Firewall des Empfängers abgelehnt werden, weil sie sich als Python-Skript ausgab. Sie meldet sich jetzt als PSADT Frontend.
- Die GitHub-Seite hat eine neue README mit Screenshots, und das Wiki enthält jetzt eine ausführliche Anleitung mit einer Seite für jeden Bildschirm.

## 0.2.88
- Der Exportzähler zählt jedes Paket einmal pro Version. Erneutes Herunterladen oder ZIP und .intunewin zählen nicht mehr doppelt. Eine neue Version zählt. Das Paket zählt für die Person, die es zuerst heruntergeladen hat.

## 0.2.77
- Schaltflächen und ausgewählte Reiter haben sanftere Farben und dunkle Schrift, damit sie bei jeder Tagesfarbe gut lesbar bleiben.

## 0.2.66
- Der Hintergrund hat jetzt denselben sanften Schimmer wie My Audiobook Collection, und die Farben der ganzen App ändern sich jede Nacht ein wenig.
- Anonyme tägliche Meldung wie in My Audiobook Collection: einmal am Tag meldet die App ihrem Autor, dass sie läuft (Version, Docker/LXC, Tage, eine zufällige ID). Über Pakete, Dateien oder Benutzer wird nichts gesendet. Abschaltbar mit PSADT_USAGE_OPTOUT=1 auf dem Server.

## 0.2.55
- Beim Herunterladen eines Pakets siehst du jetzt, was passiert: zuerst "Paket wird erstellt…", dann einen Fortschrittsbalken und am Ende den Dateinamen.
- Sind die Download-Schaltflächen gesperrt, steht darunter, dass zuerst die Probleme aus der Prüfung zu beheben sind.

## 0.2.44
- Die Download-Schaltflächen prüfen das Paket direkt vor dem Download noch einmal. Stimmt etwas nicht, bleibst du auf der Seite und siehst, was zu beheben ist, statt einer Seite mit technischer Fehlermeldung.

## 0.2.33
- Die Seite Pakete zählt jeden erfolgreichen Download: insgesamt, von dir und pro Benutzer.
- Neue Erkennungsregel "MSIX-Paket": findet eine für alle Benutzer installierte App, mit Get-AppxProvisionedPackage oder mit DISM. Ein Teil des Namens genügt.
- Registrierungsschlüssel haben Schaltflächen für HKLM, HKCU, HKEY_CLASSES_ROOT und HKU.
- Das Update über die Seite System zeigt jetzt einen animierten Fortschrittsbalken mit Prozentangabe, und die Seite lädt sich danach selbst neu.
- Behoben: Nach einem Update lief die alte Version im Hintergrund weiter, wodurch manche Seiten leer blieben und neue Optionen (wie winget) abgelehnt wurden. Die App wird jetzt immer neu gestartet.

## 0.2.22
- Erkennungsregel "MSI ProductCode": MSI wählen (bereits hochgeladen oder auf dem PC durchsuchen), der ProductCode wird automatisch eingetragen. Produktname und Version werden zur Kontrolle angezeigt.
- Nach einem Update lädt der Browser jetzt immer sofort die neue Version, statt die alte Seite aus dem Cache zu zeigen.

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
