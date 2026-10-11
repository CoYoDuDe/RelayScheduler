import QtQuick 2
import com.victron.velib 1.0

MbPage {
    id: root
    title: qsTr("Hardwareschalter")
    property string prefix: "com.victronenergy.settings/Settings/RelayScheduler"
    model: VisibleItemModel {
        MbSwitch { name: qsTr("Schalter angeschlossen"); bind: root.prefix + "/SwitchEnabled"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbItemOptions {
            description: qsTr("GPIO (BCM, Belegung prüfen)"); bind: root.prefix + "/GpioBcm"
            possibleValues: [
                MbOption { description: qsTr("Keiner"); value: -1 },
                MbOption { description: qsTr("BCM 4 / Pin 7"); value: 4 },
                MbOption { description: qsTr("BCM 12 / Pin 32"); value: 12 },
                MbOption { description: qsTr("BCM 18 / Pin 12"); value: 18 },
                MbOption { description: qsTr("BCM 20 / Pin 38"); value: 20 },
                MbOption { description: qsTr("BCM 25 / Pin 22"); value: 25 }
            ]
            writeAccessLevel: User.AccessInstaller
        }
        MbEditBox { description: qsTr("GPIO-Chip (auto oder gpiochipN)"); item.bind: root.prefix + "/GpioChip"; maximumLength: 16; writeAccessLevel: User.AccessInstaller; function editTextToValue() { return /^(auto|gpiochip[0-9]+)$/.test(_editText) ? _editText : null } }
        MbItemOptions {
            description: qsTr("Schalterart"); bind: root.prefix + "/SwitchMode"
            possibleValues: [ MbOption { description: qsTr("Rastend (An/Aus)"); value: "maintained" }, MbOption { description: qsTr("Taster (umschalten)"); value: "toggle" } ]
            writeAccessLevel: User.AccessInstaller
        }
        MbItemOptions {
            description: qsTr("Eingangswiderstand"); bind: root.prefix + "/InputBias"
            possibleValues: [ MbOption { description: qsTr("Pull-up (Schalter nach GND)"); value: "pull_up" }, MbOption { description: qsTr("Pull-down (externe Beschaltung)"); value: "pull_down" } ]
            writeAccessLevel: User.AccessInstaller
        }
        MbSwitch { name: qsTr("Aktiv bei LOW"); bind: root.prefix + "/ActiveLow"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbEditBox {
            description: qsTr("Entprellzeit [ms]"); item.bind: root.prefix + "/DebounceMs"; maximumLength: 4; writeAccessLevel: User.AccessInstaller
            function editTextToValue() { var n = Number(_editText); return n >= 20 && n <= 1000 && n === Math.floor(n) ? n : null }
        }
        MbItemValue { description: qsTr("Eingang"); item.bind: "com.coyodude.relayscheduler/Status/Gpio" }
        MbItemValue { description: qsTr("Schalter (0/1, -1 unbekannt)"); item.bind: "com.coyodude.relayscheduler/Status/Switch" }
        MbItemText { text: qsTr("Nur spannungsfreier Kontakt! Keine 12/24 V am GPIO. Beim Start wird die Schalterstellung nur eingelesen. Nach Menü-Aus erst Schalter Aus, dann An."); wrapMode: Text.WordWrap }
    }
}
