import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

Dialog {
    id: root
    required property var library
    signal renameRequested(string itemId, string itemName)
    signal deleteRequested(string itemId, string itemName)

    modal: true
    title: "Equipment library"
    anchors.centerIn: Overlay.overlay
    width: Math.min(820, Overlay.overlay ? Overlay.overlay.width - 80 : 820)
    height: Math.min(650, Overlay.overlay ? Overlay.overlay.height - 90 : 650)
    standardButtons: Dialog.NoButton
    background: Rectangle { radius: Theme.radiusMedium; color: Theme.surface; border.color: Theme.border }

    function showLibrary() {
        root.library.refreshLibrary()
        root.open()
    }

    header: Rectangle {
        implicitHeight: 58
        color: Theme.surfaceRaised
        radius: Theme.radiusMedium
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 12
            Text { Layout.fillWidth: true; text: "Saved equipment"; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
            Text { text: root.library.savedCountText; color: Theme.textSecondary; font.pixelSize: Theme.secondarySize }
            ToolButton {
                text: "Close"
                onClicked: root.close()
                contentItem: Image { source: "../../assets/icons/close.svg"; width: 17; height: 17 }
            }
        }
    }

    contentItem: Item {
        ListView {
            id: libraryList
            anchors.fill: parent
            anchors.margins: 14
            clip: true
            spacing: 7
            model: root.library.savedItems
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                required property var modelData
                width: libraryList.width - 10
                height: 78
                radius: Theme.radiusSmall
                color: Theme.surfaceRaised
                border.color: Theme.borderSoft
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 13
                    anchors.rightMargin: 10
                    spacing: 8
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { Layout.fillWidth: true; text: modelData.name; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
                        Text {
                            text: modelData.baseName + " · iLvl " + modelData.itemLevel + " · " + modelData.affixCount + " affixes" + (modelData.priceless ? " · Priceless" : "")
                            color: Theme.textSecondary
                            font.pixelSize: 10
                        }
                    }
                    Button {
                        text: "Open"
                        onClicked: { root.close(); root.library.requestOpenItem(modelData.id) }
                        background: Rectangle { radius: Theme.radiusSmall; color: Theme.accentSoft; border.color: Theme.border }
                        contentItem: Text { text: parent.text; color: Theme.text; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    Button {
                        text: "Duplicate"
                        onClicked: { root.close(); root.library.requestDuplicateItem(modelData.id) }
                        background: Rectangle { radius: Theme.radiusSmall; color: Theme.surface; border.color: Theme.borderSoft }
                        contentItem: Text { text: parent.text; color: Theme.textSecondary; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    Button {
                        text: "Rename"
                        onClicked: { root.close(); root.renameRequested(modelData.id, modelData.name) }
                        background: Rectangle { radius: Theme.radiusSmall; color: Theme.surface; border.color: Theme.borderSoft }
                        contentItem: Text { text: parent.text; color: Theme.textSecondary; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                    Button {
                        text: "Delete"
                        onClicked: { root.close(); root.deleteRequested(modelData.id, modelData.name) }
                        background: Rectangle { radius: Theme.radiusSmall; color: "#302321"; border.color: "#704841" }
                        contentItem: Text { text: parent.text; color: Theme.error; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                }
            }

            ColumnLayout {
                anchors.centerIn: parent
                visible: root.library.savedItems.length === 0
                spacing: 8
                Text { Layout.alignment: Qt.AlignHCenter; text: "Your library is empty"; color: Theme.text; font.pixelSize: 16; font.weight: Font.DemiBold }
                Text { Layout.alignment: Qt.AlignHCenter; text: "Save the current item to keep it here."; color: Theme.textSecondary; font.pixelSize: Theme.secondarySize }
            }
        }
    }

    footer: RowLayout {
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        Text { Layout.fillWidth: true; text: "JSON data is stored in the application data folder."; color: Theme.textMuted; font.pixelSize: 10 }
        Button {
            text: "Done"
            onClicked: root.close()
            background: Rectangle { radius: Theme.radiusSmall; color: Theme.accentSoft; border.color: Theme.border }
            Layout.preferredHeight: 36
            contentItem: Text { text: parent.text; color: Theme.text; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        }
    }
}
