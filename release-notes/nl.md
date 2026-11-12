# Wat is er nieuw

## 0.2.22
- Detectieregel "MSI ProductCode": kies een MSI (al geüpload, of blader op je pc) en de ProductCode wordt voor je ingevuld. Ter controle zie je de productnaam en versie.
- Na een update laadt de browser nu altijd meteen de nieuwe versie, in plaats van de oude pagina uit zijn cache te tonen.

## 0.2.11
- Elk bestandsveld in een stap heeft nu een knop Bladeren: kies een bestand op je pc en het wordt in één keer geüpload en geselecteerd.
- Run EXE kan nu ook programma's starten die al op elke Windows-pc staan, zoals winget, msiexec, PowerShell en cmd. Uploaden is dan niet nodig. winget wordt automatisch gevonden, ook als Intune als SYSTEM installeert.
- De app heeft nu altijd een donker ontwerp, met meer kleur en diepte.

## 0.2.0
- Wijzigingen in een pakket worden nu automatisch opgeslagen, een moment nadat je ze maakt. Er gaat niets meer verloren als de pagina herlaadt of de app herstart voor een update.
- Wil je de pagina verlaten terwijl er nog iets wordt opgeslagen, dan waarschuwt je browser eerst.

## 0.1.99
- Als er een nieuwere versie is, zien beheerders een oranje stip bij Systeem en een melding bovenaan elke pagina.
- Op de Systeem-pagina staat een knop "Nu controleren", en de app zoekt elke 15 minuten naar nieuwe versies in plaats van elk uur.

## 0.1.88
- Argumenten, paden en code in een stap gebruiken nu de volle breedte, zodat lange opdrachten goed leesbaar zijn.
- Onder de argumenten klik je op {Files} of op een van je geüploade bestanden om het volledige pad in te voegen, zodat je het niet hoeft te typen.

## 0.1.77
- In de argumenten van een stap kun je {Files} schrijven voor de map Files van het pakket op de pc. Bijvoorbeeld: --msix-path "{Files}\app.msix".

## 0.1.66
- Gebruikers hebben nu een volledige naam naast hun loginnaam. Vul die in bij het aanmaken van een gebruiker; iedereen kan zijn eigen naam wijzigen onder zijn account.
- Bij nieuwe pakketten wordt jouw volledige naam ingevuld als scriptauteur.
- Tijdens het uploaden zie je per bestand een voortgangsbalk.
- De knop "Syntax controleren" werkt weer op Proxmox-containers. Kan de controle niet draaien, dan legt de melding nu uit dat het een serverprobleem is en geen fout in je pakket.

## 0.1.55
- Als er een update klaarstaat, laat de Systeem-pagina nu eerst zien wat er nieuw is.
- Deze notities zijn in gewone taal geschreven, in het Engels, Nederlands en Duits.

## 0.1.44
- Iedereen kiest zijn eigen taal. Je keuze wordt bij je account bewaard, dus die gaat mee naar elke computer.

## 0.1.33
- Het tabblad Export controleert je pakket voordat je het downloadt. Rode punten moet je eerst oplossen; oranje punten zijn tips.
- Je kiest zelf hoe lang geüploade installatiebestanden op de server blijven: altijd, direct na een download, of een aantal dagen.
- Je kiest de standaardmap waar het installatielog op de pc komt. Elk pakket kan een eigen map gebruiken.
- Nieuw icoon en een frisser, rustiger uiterlijk.
- MSIX- en APPX-bestanden kun je nu uploaden.

## 0.1.22
- De app is er in het Engels, Nederlands en Duits. Kies je taal onderaan het menu.
- Containers op Proxmox kunnen zichzelf bijwerken: ga naar Systeem en klik op "Installeren".

## 0.1.11
- De installatie op Proxmox kon halverwege stoppen. Dat is opgelost.

## 0.1.0
- Installeren op Proxmox met één commando, net als de community-helperscripts.
