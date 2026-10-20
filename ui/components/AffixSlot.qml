import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

Item {
    id: root
    required property var slot
    required property string group
    required property string selectedInstanceId
    signal addRequested(string group, int index)
    signal editRequested(string instanceId)
    implicitHeight: 68
    implicitWidth: 300

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusSmall
        color: occupied ? (selected ? "#203A47" : Theme.surfaceRaised) : "#0C1B25"
        border.color: occupied ? (selected ? Theme.accent : Theme.borderSoft) : "#38505B"
        border.width: selected ? 1.5 : 1

        readonly property bool occupied: root.slot.kind === "affix"
        readonly property bool selected: occupied && root.slot.affix.id === root.selectedInstanceId

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
                category: root.slot.affix.category || "Basic"
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    Layout.fillWidth: true
                    text: parent.parent.parent.occupied ? root.slot.affix.name : "Empty " + root.group + " slot"
                    color: parent.parent.parent.occupied ? Theme.text : Theme.textSecondary
                    font.pixelSize: Theme.bodySize
                    font.weight: parent.parent.parent.occupied ? Font.Medium : Font.DemiBold
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Text {
                    visible: parent.parent.parent.occupied
                    Layout.fillWidth: true
                    text: root.slot.affix.value || root.slot.affix.tierRange || ""
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

            Text {
                visible: parent.parent.occupied && parent.parent.selected
                text: "EDITING"
                color: Theme.accent
                font.pixelSize: 9
                font.weight: Font.Bold
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

        HoverHandler { id: slotHover }
        ToolTip.visible: slotHover.hovered && root.slot.kind === "affix" && root.slot.affix.tierAmbiguous
        ToolTip.text: "This saved tier label matches multiple catalog records. Resolve it in the affix selector."
        ToolTip.delay: 450
    }
}
