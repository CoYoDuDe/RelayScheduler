import QtQuick 2
import com.victron.velib 1.0

MbPage {
    id: root
    property int slot: 1
    title: qsTr("Wochenplan %1").arg(slot)
    property string prefix: "com.victronenergy.settings/Settings/RelayScheduler/Plan" + slot
    property VBusItem stopMode: VBusItem { bind: root.prefix + "/StopMode" }
    function validTime(s) { return /^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(s) }
    model: VisibleItemModel {
        MbSwitch { name: qsTr("Plan aktiv"); bind: root.prefix + "/Enabled"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbEditBox { description: qsTr("Startzeit (HH:MM)"); item.bind: root.prefix + "/Start"; maximumLength: 5; writeAccessLevel: User.AccessInstaller; function editTextToValue() { return root.validTime(_editText) ? _editText : null } }
        MbItemOptions {
            description: qsTr("Ausschalten")
            bind: root.prefix + "/StopMode"
            possibleValues: [ MbOption { description: qsTr("Nach Laufzeit"); value: "duration" }, MbOption { description: qsTr("Zur Uhrzeit"); value: "time" } ]
            writeAccessLevel: User.AccessInstaller
        }
        MbEditBox {
            description: qsTr("Laufzeit [min]"); item.bind: root.prefix + "/Minutes"; maximumLength: 4
            show: root.stopMode.value !== "time"; writeAccessLevel: User.AccessInstaller
            function editTextToValue() { var n = Number(_editText); return n >= 1 && n <= 1440 && n === Math.floor(n) ? n : null }
        }
        MbEditBox { description: qsTr("Ausschaltzeit (HH:MM)"); item.bind: root.prefix + "/End"; maximumLength: 5; show: root.stopMode.value === "time"; writeAccessLevel: User.AccessInstaller; function editTextToValue() { return root.validTime(_editText) ? _editText : null } }
        MbSwitch { name: qsTr("Montag"); bind: root.prefix + "/Monday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbSwitch { name: qsTr("Dienstag"); bind: root.prefix + "/Tuesday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbSwitch { name: qsTr("Mittwoch"); bind: root.prefix + "/Wednesday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbSwitch { name: qsTr("Donnerstag"); bind: root.prefix + "/Thursday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbSwitch { name: qsTr("Freitag"); bind: root.prefix + "/Friday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbSwitch { name: qsTr("Samstag"); bind: root.prefix + "/Saturday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbSwitch { name: qsTr("Sonntag"); bind: root.prefix + "/Sunday"; valueTrue: 1; valueFalse: 0; writeAccessLevel: User.AccessInstaller }
        MbItemText { text: qsTr("Die maximale Laufzeit begrenzt auch diesen Plan. Frühere Ausschaltzeiten liegen am nächsten Tag."); wrapMode: Text.WordWrap }
    }
}
