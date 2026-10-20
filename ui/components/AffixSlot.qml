import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

Item {
    id: root
    required property var slot
    required property string group
    required property string selectedInstanceId
    required property string selectedGroup
    required property int selectedSlotIndex
    signal addRequested(string group, int index)
    signal editRequested(string instanceId)
    implicitHeight: 66
    implicitWidth: 300

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusSmall
        color: selected ? "#203A47" : occupied ? Theme.surfaceRaised : "#0C1B25"
        border.color: selected ? Theme.accent : occupied ? Theme.borderSoft : "#38505B"
        border.width: selected ? 1.5 : 1

        readonly property bool occupied: root.slot.kind === "affix"
        readonly property bool selected: occupied
            ? root.slot.affix.id === root.selectedInstanceId
            : root.group === root.selectedGroup && root.slot.index === root.selectedSlotIndex

        Rectangle {
            visible: parent.occupied
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 1
            anchors.topMargin: 6
            anchors.bottomMargin: 6
            width: 2
            radius: 1
            color: Theme.tierBorder(root.slot.affix.tierLabel)
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 10

            Item {
                visible: !parent.parent.occupied
                width: 24
                height: 24
                Rectangle { width: 14; height: 2; radius: 1; color: Theme.accent; anchors.centerIn: parent }
                Rectangle { width: 2; height: 14; radius: 1; color: Theme.accent; anchors.centerIn: parent }
            }

            TierBadge {
                visible: parent.parent.occupied
                tier: root.slot.affix.tierAmbiguous ? "T?" : root.slot.affix.tierLabel || "T?"
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    Layout.fillWidth: true
                    text: parent.parent.parent.occupied
                          ? (root.slot.affix.tierRange || root.slot.affix.value || root.slot.affix.name)
                          : "Empty " + root.group + " slot"
                    color: parent.parent.parent.occupied ? Theme.text : Theme.textSecondary
                    font.pixelSize: Theme.bodySize
                    font.weight: parent.parent.parent.occupied ? Font.Medium : Font.DemiBold
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Text {
                    visible: parent.parent.parent.occupied
                             && root.slot.affix.value.length > 0
                             && root.slot.affix.tierRange.length > 0
                             && root.slot.affix.value !== root.slot.affix.tierRange
                    Layout.fillWidth: true
                    text: "Current value: " + root.slot.affix.value
                    color: Theme.textSecondary
                    font.pixelSize: Theme.secondarySize
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Text {
                    visible: !parent.parent.parent.occupied
                    text: "Click to add"
                    color: Theme.textMuted
                    font.pixelSize: 10
                }
            }

            Rectangle {
                visible: parent.parent.occupied
                width: 19
                height: 19
                radius: 10
                color: "#101B24"
                border.color: parent.parent.selected ? "#48B9FF" : "#40515B"
                border.width: parent.parent.selected ? 2 : 1
                Rectangle {
                    anchors.centerIn: parent
                    width: 9
                    height: 9
                    radius: 5
                    color: "#48B9FF"
                    visible: parent.parent.parent.selected
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                if (parent.occupied) root.editRequested(root.slot.affix.id)
                else root.addRequested(root.group, root.slot.index)
            }
        }

        Accessible.role: occupied ? Accessible.RadioButton : Accessible.Button
        Accessible.name: occupied
            ? root.group + " slot " + (root.slot.index + 1) + ": " + root.slot.affix.name
            : "Add " + root.group + " in slot " + (root.slot.index + 1)
        Accessible.checked: selected

        HoverHandler { id: slotHover }
        ToolTip.visible: slotHover.hovered && root.slot.kind === "affix" && root.slot.affix.tierAmbiguous
        ToolTip.text: "This saved tier label matches multiple catalog records. Resolve it in the affix selector."
        ToolTip.delay: 450
    }
}
