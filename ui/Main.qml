import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: mainWindow
    width: 1500
    height: 940
    minimumWidth: 1080
    minimumHeight: 720
    visible: true
    title: "Torchlight Craft Planner"
    color: "#09131D"
    property var appController: controller
    property bool closeApproved: false

    background: Rectangle {
        color: "#09131D"
        Rectangle {
            anchors.fill: parent
            opacity: 0.78
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#101B25" }
                GradientStop { position: 0.47; color: "#0A1621" }
                GradientStop { position: 1.0; color: "#10273A" }
            }
        }
        Rectangle { width: 540; height: 360; x: parent.width * 0.42; y: -160; radius: 220; color: "#173348"; opacity: 0.16 }
        Rectangle { width: 700; height: 440; x: parent.width * 0.62; y: parent.height * 0.60; radius: 260; color: "#244D65"; opacity: 0.12 }
    }

    header: Rectangle {
        implicitHeight: 70
        color: "#0B141D"
        border.color: "#233440"
        border.width: 1
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 26
            anchors.rightMargin: 26
            spacing: 12

            Image { source: "../assets/icons/planner-mark.svg"; width: 34; height: 34; fillMode: Image.PreserveAspectFit }
            ColumnLayout {
                spacing: 1
                Text { text: "Torchlight Craft Planner"; color: "#E9EDEF"; font.pixelSize: 15; font.weight: Font.DemiBold }
                Text { text: "ITEM EDITOR · VERSION 0.1"; color: "#8095A0"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1.1 }
            }

            Rectangle { Layout.fillWidth: true; color: "transparent" }

            RowLayout {
                spacing: 7
                Rectangle { width: 7; height: 7; radius: 4; color: "#70C8B2" }
                Text { text: "LOCAL WORKSPACE"; color: "#9BAEB5"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 1 }
            }

            Button {
                id: libraryButton
                Layout.preferredHeight: 38
                Layout.preferredWidth: 112
                text: "Library"
                onClicked: { mainWindow.appController.refreshLibrary(); libraryDialog.open() }
                background: Rectangle { radius: 5; color: "#14232E"; border.color: "#354B57" }
                contentItem: RowLayout {
                    spacing: 7
                    Image { source: "../assets/icons/library.svg"; width: 15; height: 15 }
                    Text { text: libraryButton.text; color: "#DCE5E9"; font.pixelSize: 11; font.weight: Font.DemiBold }
                }
            }
            Button {
                id: newButton
                Layout.preferredHeight: 38
                Layout.preferredWidth: 96
                text: "New item"
                onClicked: mainWindow.appController.requestNewItem()
                background: Rectangle { radius: 5; color: "#14232E"; border.color: "#354B57" }
                contentItem: RowLayout {
                    spacing: 7
                    Image { source: "../assets/icons/new.svg"; width: 14; height: 14 }
                    Text { text: newButton.text; color: "#DCE5E9"; font.pixelSize: 11; font.weight: Font.DemiBold }
                }
            }
            Button {
                id: saveButton
                Layout.preferredHeight: 38
                Layout.preferredWidth: 104
                text: "Save item"
                onClicked: mainWindow.appController.saveCurrent()
                background: Rectangle { radius: 5; color: "#D6A340"; border.color: "#F0C76A" }
                contentItem: RowLayout {
                    spacing: 7
                    Image { source: "../assets/icons/save.svg"; width: 15; height: 15 }
                    Text { text: saveButton.text; color: "#17212A"; font.pixelSize: 11; font.weight: Font.Bold }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 11

        ItemEditor {
            Layout.fillWidth: true
            Layout.fillHeight: true
            controller: mainWindow.appController
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            spacing: 8
            Rectangle { width: 6; height: 6; radius: 3; color: "#8C73C8" }
            Text { text: "TIER KEY"; color: "#8196A1"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
            Text { text: "Basic"; color: "#CEAA68"; font.pixelSize: 10 }
            Text { text: "·"; color: "#5C707B" }
            Text { text: "Advanced"; color: "#C398DC"; font.pixelSize: 10 }
            Text { text: "·"; color: "#5C707B" }
            Text { text: "Ultimate"; color: "#A7B4E7"; font.pixelSize: 10 }
            Text { Layout.fillWidth: true; text: "Catalog entries are community reference data; SS14 compatibility is unverified."; color: "#718793"; font.pixelSize: 10; horizontalAlignment: Text.AlignRight; elide: Text.ElideRight }
            Text { text: mainWindow.appController.isDirty ? "Unsaved changes" : "All changes saved"; color: mainWindow.appController.isDirty ? "#D9B66D" : "#78B9A9"; font.pixelSize: 10; font.weight: Font.Medium }
        }
    }

    Rectangle {
        id: noticeBanner
        z: 4
        visible: mainWindow.appController.noticeText.length > 0
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 58
        width: Math.min(parent.width - 48, 650)
        height: 44
        radius: 6
        color: mainWindow.appController.noticeKind === "error" ? "#382622" : mainWindow.appController.noticeKind === "warning" ? "#38311F" : "#17352F"
        border.color: mainWindow.appController.noticeKind === "error" ? "#88584A" : mainWindow.appController.noticeKind === "warning" ? "#887040" : "#477E70"
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 8
            spacing: 10
            Text { Layout.fillWidth: true; text: mainWindow.appController.noticeText; color: "#E6EAEB"; font.pixelSize: 11; wrapMode: Text.WordWrap; elide: Text.ElideRight }
            ToolButton {
                text: "Close"
                onClicked: mainWindow.appController.dismissNotice()
                contentItem: Image { source: "../assets/icons/close.svg"; width: 16; height: 16 }
            }
        }
    }

    Dialog {
        id: unsavedDialog
        modal: true
        closePolicy: Popup.NoAutoClose
        title: "Unsaved changes"
        anchors.centerIn: Overlay.overlay
        width: 430
        standardButtons: Dialog.NoButton
        background: Rectangle { radius: 8; color: "#121F29"; border.color: "#51636D" }
        contentItem: ColumnLayout {
            spacing: 10
            Text { text: "This equipment has edits that are not saved."; color: "#E3EAED"; font.pixelSize: 14; font.weight: Font.DemiBold }
            Text { Layout.fillWidth: true; text: "Save them before continuing, discard the changes, or return to the editor."; color: "#9BADB5"; font.pixelSize: 12; wrapMode: Text.WordWrap }
        }
        footer: RowLayout {
            spacing: 8
            Button {
                id: cancelUnsavedButton
                text: "Cancel"
                onClicked: { unsavedDialog.close(); mainWindow.appController.resolveUnsaved("cancel") }
                background: Rectangle { radius: 4; color: "#17252F"; border.color: "#394E59" }
                Layout.preferredHeight: 36
                contentItem: Text { text: cancelUnsavedButton.text; color: "#D8E0E3"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
            Item { Layout.fillWidth: true }
            Button {
                id: discardUnsavedButton
                text: "Discard"
                onClicked: { unsavedDialog.close(); mainWindow.appController.resolveUnsaved("discard") }
                background: Rectangle { radius: 4; color: "#352522"; border.color: "#72483F" }
                Layout.preferredHeight: 36
                contentItem: Text { text: discardUnsavedButton.text; color: "#E7AA9B"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
            Button {
                id: saveContinueButton
                text: "Save & continue"
                onClicked: { unsavedDialog.close(); mainWindow.appController.resolveUnsaved("save") }
                background: Rectangle { radius: 4; color: "#D1A047"; border.color: "#E9C46E" }
                Layout.preferredHeight: 36
                contentItem: Text { text: saveContinueButton.text; color: "#18222B"; font.pixelSize: 11; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }
    }

    Dialog {
        id: libraryDialog
        modal: true
        title: "Equipment library"
        anchors.centerIn: Overlay.overlay
        width: Math.min(mainWindow.width - 80, 820)
        height: Math.min(mainWindow.height - 90, 650)
        standardButtons: Dialog.NoButton
        background: Rectangle { radius: 8; color: "#101C26"; border.color: "#4A5B65" }
        header: Rectangle {
            implicitHeight: 58
            color: "#13222D"
            radius: 8
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 12
                Text { Layout.fillWidth: true; text: "Saved equipment"; color: "#E6ECEF"; font.pixelSize: 18; font.weight: Font.DemiBold }
                Text { text: mainWindow.appController.savedCountText; color: "#91A5AF"; font.pixelSize: 11 }
                ToolButton {
                    text: "Close"
                    onClicked: libraryDialog.close()
                    contentItem: Image { source: "../assets/icons/close.svg"; width: 17; height: 17 }
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
                model: mainWindow.appController.savedItems
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                delegate: Rectangle {
                    id: savedRow
                    required property var modelData
                    width: libraryList.width - 10
                    height: 78
                    radius: 6
                    color: "#17242E"
                    border.color: "#2C414D"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 13
                        anchors.rightMargin: 10
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { Layout.fillWidth: true; text: modelData.name; color: "#E5ECEF"; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
                            Text {
                                text: modelData.baseName + " · iLvl " + modelData.itemLevel + " · " + modelData.affixCount + " affixes" + (modelData.priceless ? " · Priceless" : "")
                                color: "#8EA3AD"
                                font.pixelSize: 10
                            }
                        }
                        Button {
                            id: openSavedButton
                            text: "Open"
                            onClicked: { libraryDialog.close(); mainWindow.appController.requestOpenItem(modelData.id) }
                            background: Rectangle { radius: 4; color: "#263B47"; border.color: "#4A6674" }
                            contentItem: Text { text: openSavedButton.text; color: "#DCE9EC"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                        Button {
                            id: duplicateSavedButton
                            text: "Duplicate"
                            onClicked: { libraryDialog.close(); mainWindow.appController.requestDuplicateItem(modelData.id) }
                            background: Rectangle { radius: 4; color: "#17252E"; border.color: "#394E59" }
                            contentItem: Text { text: duplicateSavedButton.text; color: "#CAD5D9"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                        Button {
                            id: renameSavedButton
                            text: "Rename"
                            onClicked: { mainWindow.renameTargetId = modelData.id; renameField.text = modelData.name; libraryDialog.close(); renameDialog.open() }
                            background: Rectangle { radius: 4; color: "#17252E"; border.color: "#394E59" }
                            contentItem: Text { text: renameSavedButton.text; color: "#CAD5D9"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                        Button {
                            id: deleteSavedButton
                            text: "Delete"
                            onClicked: { mainWindow.deleteTargetId = modelData.id; mainWindow.deleteTargetName = modelData.name; libraryDialog.close(); deleteDialog.open() }
                            background: Rectangle { radius: 4; color: "#302321"; border.color: "#704841" }
                            contentItem: Text { text: deleteSavedButton.text; color: "#E4A99D"; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                }

                ColumnLayout {
                    anchors.centerIn: parent
                    visible: mainWindow.appController.savedItems.length === 0
                    spacing: 8
                    Text { Layout.alignment: Qt.AlignHCenter; text: "Your library is empty"; color: "#E1E9EC"; font.pixelSize: 16; font.weight: Font.DemiBold }
                    Text { Layout.alignment: Qt.AlignHCenter; text: "Save the current item to keep it here."; color: "#91A5AE"; font.pixelSize: 12 }
                }
            }
        }
        footer: RowLayout {
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            Text { Layout.fillWidth: true; text: "JSON data is stored in the application data folder."; color: "#80959F"; font.pixelSize: 10 }
            Button {
                id: doneLibraryButton
                text: "Done"
                onClicked: libraryDialog.close()
                background: Rectangle { radius: 4; color: "#263B47"; border.color: "#4B6674" }
                Layout.preferredHeight: 36
                contentItem: Text { text: doneLibraryButton.text; color: "#E2EAEC"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }
    }

    property string renameTargetId: ""
    property string deleteTargetId: ""
    property string deleteTargetName: ""

    Dialog {
        id: renameDialog
        modal: true
        title: "Rename equipment"
        anchors.centerIn: Overlay.overlay
        width: 420
        standardButtons: Dialog.NoButton
        background: Rectangle { radius: 8; color: "#121F29"; border.color: "#50626C" }
        contentItem: ColumnLayout {
            spacing: 8
            Text { text: "Equipment name"; color: "#9CB0B9"; font.pixelSize: 11 }
            TextField {
                id: renameField
                Layout.fillWidth: true
                maximumLength: 80
                selectByMouse: true
                color: "#E9EFF1"
                background: Rectangle { radius: 5; color: "#0A141D"; border.color: renameField.activeFocus ? "#5BC2CD" : "#2D434E" }
            }
        }
        footer: RowLayout {
            Item { Layout.fillWidth: true }
            Button { text: "Cancel"; onClicked: renameDialog.close() }
            Button {
                id: saveRenameButton
                text: "Save name"
                onClicked: { mainWindow.appController.renameSavedItem(mainWindow.renameTargetId, renameField.text); renameDialog.close() }
                background: Rectangle { radius: 4; color: "#D1A047"; border.color: "#E9C46E" }
                Layout.preferredHeight: 36
                contentItem: Text { text: saveRenameButton.text; color: "#18222B"; font.pixelSize: 11; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }
    }

    Dialog {
        id: deleteDialog
        modal: true
        title: "Delete saved equipment?"
        anchors.centerIn: Overlay.overlay
        width: 430
        standardButtons: Dialog.NoButton
        background: Rectangle { radius: 8; color: "#121F29"; border.color: "#6E504A" }
        contentItem: Text { text: "Delete “" + mainWindow.deleteTargetName + "” from your local library? This cannot be undone."; color: "#D9E1E4"; font.pixelSize: 12; wrapMode: Text.WordWrap }
        footer: RowLayout {
            Item { Layout.fillWidth: true }
            Button { text: "Cancel"; onClicked: deleteDialog.close() }
            Button {
                id: confirmDeleteButton
                text: "Delete item"
                onClicked: { mainWindow.appController.deleteSavedItem(mainWindow.deleteTargetId); deleteDialog.close() }
                background: Rectangle { radius: 4; color: "#5A302A"; border.color: "#98584B" }
                Layout.preferredHeight: 36
                contentItem: Text { text: confirmDeleteButton.text; color: "#F0D2CB"; font.pixelSize: 11; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }
    }

    Connections {
        target: mainWindow.appController
        function onConfirmUnsaved() { unsavedDialog.open() }
        function onCloseConfirmed() {
            mainWindow.closeApproved = true
            mainWindow.close()
        }
    }

    onClosing: function(close) {
        if (mainWindow.appController.isDirty && !mainWindow.closeApproved) {
            close.accepted = false
            mainWindow.appController.requestClose()
        }
    }
}
