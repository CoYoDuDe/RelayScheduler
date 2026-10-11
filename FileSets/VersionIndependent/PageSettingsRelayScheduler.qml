import QtQuick 2
import com.victron.velib 1.0

MbPage {
    id: root
    title: qsTr("RelayScheduler")
    property string prefix: "com.victronenergy.settings/Settings/RelayScheduler"
    property VBusItem active: VBusItem { bind: root.prefix + "/Enabled" }
    property VBusItem selectedRelay: VBusItem { bind: root.prefix + "/RelayNumber" }
    property VBusItem switchable: VBusItem { bind: "com.victronenergy.system/SwitchableOutput/0/State" }
    property string stateBind: selectedRelay.valid && selectedRelay.value > 0 ? "com.victronenergy.system/" + (switchable.valid ? "SwitchableOutput/" : "Relay/") + (selectedRelay.value - 1) + "/State" : ""
    model: VisibleItemModel {
        MbSwitch { name: qsTr("Zeitsteuerung aktiv"); bind: root.prefix + "/Enabled"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbItemValue {
            description: qsTr("Relaiszustand")
            item.bind: root.stateBind
            item.text: item.valid ? (item.value === 1 ? qsTr("Ein (geschlossen)") : item.value === 0 ? qsTr("Aus (offen)") : qsTr("Unbekannt")) : qsTr("Kein Relais gewählt")
        }
        MbItemValue { description: qsTr("Status"); item.bind: "com.coyodude.relayscheduler/Status/State" }
        MbItemValue { description: qsTr("Auslöser"); item.bind: "com.coyodude.relayscheduler/Status/Source" }
        MbItemValue { description: qsTr("Restlaufzeit [s]"); item.bind: "com.coyodude.relayscheduler/Status/RemainingSeconds" }
        MbItemValue { description: qsTr("Hinweis"); item.bind: "com.coyodude.relayscheduler/Status/Error" }
        MbItemOptions {
            description: qsTr("Jetzt schalten")
            bind: "com.coyodude.relayscheduler/Control/Command"
            enabled: root.active.valid && root.active.value === 1
            possibleValues: [
                MbOption { description: qsTr("Befehl wählen"); value: -1 },
                MbOption { description: qsTr("Aus"); value: 0 },
                MbOption { description: qsTr("Ein (mit Laufzeit)"); value: 1 }
            ]
            writeAccessLevel: User.AccessUser
        }
        MbItemOptions {
            description: qsTr("GX-Relais")
            bind: root.prefix + "/RelayNumber"
            possibleValues: [
                MbOption { description: qsTr("Keines ausgewählt"); value: 0 },
                MbOption { description: qsTr("Relais 1"); value: 1 },
                MbOption { description: qsTr("Relais 2"); value: 2 },
                MbOption { description: qsTr("Relais 3"); value: 3 },
                MbOption { description: qsTr("Relais 4"); value: 4 },
                MbOption { description: qsTr("Relais 5"); value: 5 },
                MbOption { description: qsTr("Relais 6"); value: 6 }
            ]
            writeAccessLevel: User.AccessInstaller
        }
        MbEditBox { description: qsTr("Bezeichnung"); item.bind: root.prefix + "/Label"; maximumLength: 32; writeAccessLevel: User.AccessInstaller }
        MbEditBox {
            description: qsTr("Manuelle Laufzeit [min]"); item.bind: root.prefix + "/ManualMinutes"; maximumLength: 4; writeAccessLevel: User.AccessInstaller
            function editTextToValue() { var n = Number(_editText); return n >= 1 && n <= 1440 && n === Math.floor(n) ? n : null }
        }
        MbEditBox {
            description: qsTr("Maximale Laufzeit [min]"); item.bind: root.prefix + "/MaximumMinutes"; maximumLength: 4; writeAccessLevel: User.AccessInstaller
            function editTextToValue() { var n = Number(_editText); return n >= 1 && n <= 1440 && n === Math.floor(n) ? n : null }
        }
        MbSubMenu { description: qsTr("Wochenplan 1"); subpage: Component { PageSettingsRelaySchedulerPlan { slot: 1 } } }
        MbSubMenu { description: qsTr("Wochenplan 2"); subpage: Component { PageSettingsRelaySchedulerPlan { slot: 2 } } }
        MbSubMenu { description: qsTr("Wochenplan 3"); subpage: Component { PageSettingsRelaySchedulerPlan { slot: 3 } } }
        MbSubMenu { description: qsTr("Wochenplan 4"); subpage: Component { PageSettingsRelaySchedulerPlan { slot: 4 } } }
        MbSubMenu { description: qsTr("Hardwareschalter"); subpage: Component { PageSettingsRelaySchedulerSwitch {} } }
        MbItemValue { description: qsTr("Lokale Venus-Zeit"); item.bind: "com.coyodude.relayscheduler/Status/Clock" }
        MbItemText { text: qsTr("Relais im Venus-Menü auf Manuell stellen. Pläne starten nur bei aktivierter Zeitsteuerung."); wrapMode: Text.WordWrap }
    }
}
