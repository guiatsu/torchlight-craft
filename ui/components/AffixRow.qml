import QtQuick
import QtQuick.Layouts

Item {
    id: root
    required property var entry
    property bool selected: false
    signal activated(string instanceId)
    implicitHeight: rowSurface.implicitHeight
    implicitWidth: 340

    Rectangle {
        id: rowSurface
        anchors.fill: parent
        implicitHeight: rowLayout.implicitHeight + 18
        radius: 6
        color: root.selected ? "#1B3443" : "#111D28"
        border.color: root.selected ? "#5CC8D5" : "#263B49"
        border.width: root.selected ? 1.3 : 1

        RowLayout {
            id: rowLayout
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            anchors.topMargin: 8
            anchors.bottomMargin: 8
            spacing: 10

            TierBadge { tier: root.entry.tierId || "T?"; category: root.entry.category || "Basic" }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3

                Text {
                    Layout.fillWidth: true
                    text: root.entry.name || "Unknown affix"
                    color: "#E7EDF0"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }

                Text {
                    Layout.fillWidth: true
                    text: root.entry.value || root.entry.tierRange || "Value not entered"
                    color: "#91A5B0"
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
            }

            Text {
                visible: root.selected
                text: "EDITING"
                color: "#69D3DF"
                font.pixelSize: 9
                font.weight: Font.Bold
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.activated(root.entry.id)
        }
    }
}
