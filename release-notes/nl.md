# Wat is er nieuw

## 0.3.44
- ↑ op de eerste stap van een fase zet die stap aan het eind van de fase erboven (bijvoorbeeld van Main naar Pre), en ↓ op de laatste stap zet hem aan het begin van de fase eronder. De pijltjes zijn alleen nog grijs helemaal bovenaan Pre en helemaal onderaan Post.

## 0.3.33
- Pre, Main en Post zijn nu elk een eigen blok, met de knop om een stap toe te voegen in het blok waar hij bij hoort ("Stap toevoegen aan Main").
- Als je een stap met ↑ of ↓ verplaatst, schuift de pagina mee. De stap blijft onder je muis staan en licht even op, zodat je meteen verder kunt klikken.
- Per ongeluk een stap verwijderd met ✕? Tien seconden lang zet de knop "Ongedaan maken" hem terug op dezelfde plek.

## 0.3.22
- Grote bestanden worden nu in stukken van 5 MB geüpload. Uploads via een reverse proxy of tunnel met een groottelimiet (zoals Zoraxy of Cloudflare) blijven niet meer hangen. Een stuk dat mislukt, wordt vanzelf opnieuw geprobeerd.

## 0.3.11
- Een upload die vastloopt, stopt nu na een minuut zonder voortgang en zegt waarom (vaak een reverse proxy of tunnel met een groottelimiet, of een volle schijf), in plaats van eindeloos te wachten.

## 0.3.0
- Alleen beheerders kunnen nu pakketten verwijderen. Bewerkers kunnen ze nog wel maken en aanpassen.

## 0.2.99
- Opgelost: de dagelijkse melding kon door de firewall van de ontvanger worden geweigerd, omdat hij zich als Python-script voordeed. Hij meldt zich nu als PSADT Frontend.
- De GitHub-pagina heeft een nieuwe README met screenshots, en de wiki heeft nu een uitgebreide handleiding met een pagina voor elk scherm.

## 0.2.88
- De exportteller telt elk pakket één keer per versie. Opnieuw downloaden, of zowel ZIP als .intunewin, telt niet meer dubbel. Een nieuwe versie telt wel. Het pakket telt mee voor degene die het als eerste downloadde.

## 0.2.77
- Knoppen en geselecteerde tabbladen hebben zachtere kleuren en donkere tekst, zodat ze bij elke dagkleur goed leesbaar zijn.

## 0.2.66
- De achtergrond heeft nu dezelfde zachte gloed als My Audiobook Collection, en de kleuren van de hele app veranderen elke nacht een beetje.
- Anonieme dagelijkse melding, net als in My Audiobook Collection: één keer per dag laat de app de maker weten dat hij draait (versie, Docker/LXC, aantal dagen, een willekeurige id). Er wordt niets over je pakketten, bestanden of gebruikers verstuurd. Uitzetten kan met PSADT_USAGE_OPTOUT=1 op de server.

## 0.2.55
- Bij het downloaden van een pakket zie je nu wat er gebeurt: eerst "Pakket wordt gebouwd…", dan een voortgangsbalk en tot slot de bestandsnaam als het klaar is.
- Zijn de downloadknoppen vergrendeld, dan staat eronder dat je eerst de problemen uit de controle moet oplossen.

## 0.2.44
- De downloadknoppen controleren het pakket vlak voor het downloaden nog een keer. Klopt er iets niet, dan blijf je op de pagina en zie je wat je moet oplossen, in plaats van een pagina met een technische foutmelding.

## 0.2.33
- De pagina Pakketten telt elke geslaagde download: in totaal, door jou en per gebruiker.
- Nieuwe detectieregel "MSIX-pakket": vindt een app die voor alle gebruikers is geïnstalleerd, met Get-AppxProvisionedPackage of met DISM. Een deel van de naam is genoeg.
- Registersleutels hebben knoppen om met één klik HKLM, HKCU, HKEY_CLASSES_ROOT of HKU te kiezen.
- Bijwerken via de System-pagina toont nu een bewegende voortgangsbalk met percentage, en de pagina laadt zichzelf opnieuw als het klaar is.
- Opgelost: na een update bleef de oude versie op de achtergrond draaien, waardoor sommige pagina's leeg bleven en nieuwe opties (zoals winget) werden geweigerd. De app wordt nu altijd herstart.

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
