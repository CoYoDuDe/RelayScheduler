# RelayScheduler

Entwicklungsstand: geprüftes Grundgerüst. Die reale Schalter-/Heizungsabnahme steht noch aus; vor Verwendung an der eigenen Anlage prüfen.

## Deutsch

Schaltet ein manuelles GX-Relais per Wochenplan, Venus-Menü oder zusätzlichem Schalter. Für Heizungs-Steuerkontakte und ähnliche Anwendungen.

- Vier Wochenpläne: Wochentage, Startzeit und Laufzeit oder Ausschaltzeit.
- Manuell einschalten; maximale Laufzeit begrenzt jede Einschaltung.
- Rastender Schalter: Menü-Aus bleibt wirksam. Erneut per Schalter einschalten: erst Aus, dann An. Menü-Ein funktioniert auch bei ausgeschaltetem Schalter.
- Optional Taster, einstellbarer GPIO, Eingangswiderstand und Entprellung.
- Status, Restlaufzeit und Fehler im Venus-Menü. Unabhängige Laufzeitwache bei Dienstausfall.
- Relaiszustand direkt aus Venus: Aus = Kontakt offen, Ein = Kontakt geschlossen; unabhängig von Zeitplan oder Schalterstellung.

**Voraussetzungen:** Venus OS mit klassischer GUI, SetupHelper, manuelles GX-Relais, Python-D-Bus/GLib und libgpiod 2 (`libgpiod.so.3`). Ein GPIO-Schalter benötigt einen Raspberry Pi und einen freien Eingang. Keine Unterstützung der neuen GUI v2 zugesichert.

**Installation:** In SetupHelper ein Paket hinzufügen: `RelayScheduler`, GitHub-Benutzer `CoYoDuDe`, Zweig `main`. Herunterladen und installieren. Unter **Einstellungen → RelayScheduler** Relais wählen und konfigurieren. Erstinstallation und alle Zeitpläne sind ausgeschaltet. Aktualisieren und deinstallieren ebenfalls über SetupHelper; persönliche Einstellungen bleiben erhalten. Deaktivieren oder Deinstallieren beendet eine durch das Addon beaufsichtigte Einschaltung.

**Schalter:** Nur einen spannungsfreien Kontakt zwischen freiem GPIO und GND anschließen. Standard: Pull-up, aktiv bei Verbindung nach GND. Niemals Fahrzeugspannung an den GPIO legen. BCM-Nummer und physische Pin-Nummer unterscheiden sich. Die im Menü angebotenen GPIOs müssen für das jeweilige Gerät geprüft werden; belegte Leitungen werden nicht übernommen. Bei GPIO-/Relaisfehlern: Ursache beheben, Addon aus- und wieder einschalten.

**Heizung:** Das Relais ersetzt ausschließlich den originalen Ein-/Aus-Steuerkontakt. Stromversorgung und Nachlauf bleiben beim Heizgerät. Nach Neustart löst ein bereits eingeschalteter Schalter keine neue Einschaltung aus; ausgefallene Zeitplanstarts werden nicht nachgeholt. Zeitpläne nutzen die lokale Venus-Zeit. Einträge werden pro Datum/Startminute einmal ausgeführt; bei einem erkannten Uhrsprung wird die betroffene Minute ausgelassen.

## English

Controls one manual GX relay using four weekly schedules, the classic Venus menu or a physical switch. Select weekdays, start time and duration or stop time. Every activation has a maximum runtime and an independent service watchdog.

A maintained switch uses edges: GUI Off overrides a switch left On. Switch Off then On to restart. GUI On also works with the switch Off. Optional push button, configurable free GPIO, input bias and debounce.

Requires SetupHelper, classic Venus GUI, a manual GX relay, Python D-Bus/GLib and libgpiod 2 (`libgpiod.so.3`). GPIO input requires a Raspberry Pi. GUI v2 is not supported. Add `RelayScheduler`, owner `CoYoDuDe`, branch `main` in SetupHelper; download/install and configure under **Settings → RelayScheduler**. Factory settings and schedules are disabled. Update/uninstall through SetupHelper; personal settings are retained.

Use a voltage-free switch between a verified free GPIO and GND only. Never connect vehicle voltage to GPIO. For heaters, switch only the original control contact and retain the heater power supply and after-run. A switch already On at startup does not trigger heating. Missed schedules are not replayed; schedules use local Venus time.
