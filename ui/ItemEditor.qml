import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

RowLayout {
    id: root
    required property var controller
    spacing: 16

    Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.minimumWidth: 405
        Layout.preferredWidth: 0.92
        color: "#101B25"
        border.color: "#2D414D"
        border.width: 1
        radius: 10

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 13

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Rectangle {
                    width: 72; height: 72; radius: 8
                    color: "#172938"
                    border.color: "#4B5360"
                    Image { anchors.fill: parent; anchors.margins: 1; source: "../assets/icons/weapon-sigil.svg"; fillMode: Image.PreserveAspectFit }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    TextField {
                        id: nameField
                        Layout.fillWidth: true
                        text: root.controller.itemName
                        placeholderText: "Equipment name"
                        placeholderTextColor: "#748B96"
                        color: "#F0F2F1"
                        font.pixelSize: 19
                        font.weight: Font.DemiBold
                        selectByMouse: true
                        maximumLength: 80
                        onTextEdited: root.controller.setItemName(text)
                        background: Rectangle { color: "transparent"; border.width: 0 }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Text { text: "Item Level " + root.controller.itemLevel; color: "#B1C1C7"; font.pixelSize: 12; font.weight: Font.Medium }
                        Rectangle { width: 1; height: 14; color: "#43535B" }
                        Text { text: root.controller.baseSubcategory; color: "#8A9EA8"; font.pixelSize: 12 }
                    }
                }

                Rectangle {
                    visible: root.controller.priceless
                    radius: 4
                    color: "#473A21"
                    border.color: "#C89C48"
                    implicitWidth: pricelessLabel.implicitWidth + 16
                    implicitHeight: 24
                    Text { id: pricelessLabel; anchors.centerIn: parent; text: "PRICELESS"; color: "#EBCB82"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
                }
            }

            BaseSelector { Layout.fillWidth: true; controller: root.controller }

            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                ColumnLayout {
                    Layout.preferredWidth: 154
                    spacing: 5
                    Text { text: "ITEM LEVEL"; color: "#8398A5"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1.1 }
                    SpinBox {
                        id: itemLevelSpin
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        from: 1
                        to: 100
                        value: root.controller.itemLevel
                        editable: true
                        validator: IntValidator { bottom: 1; top: 100 }
                        onValueModified: root.controller.setItemLevel(value)
                        palette.text: "#ECF2F4"
                        palette.buttonText: "#EAF1F3"
                        palette.mid: "#70848D"
                        background: Rectangle { radius: 5; color: "#0C1720"; border.color: itemLevelSpin.activeFocus ? "#64C5D1" : "#324652" }
                    }
                }

                Rectangle { width: 1; height: 42; color: "#30434F"; Layout.alignment: Qt.AlignBottom }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    Text { text: "ITEM STATE"; color: "#8398A5"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1.1 }
                    CheckBox {
                        id: pricelessCheck
                        text: "Priceless"
                        checked: root.controller.priceless
                        onToggled: root.controller.setPriceless(checked)
                        spacing: 8
                        indicator: Rectangle {
                            implicitWidth: 19; implicitHeight: 19
                            x: pricelessCheck.leftPadding
                            y: parent.height / 2 - height / 2
                            radius: 4
                            color: pricelessCheck.checked ? "#B58A3C" : "#15232D"
                            border.color: pricelessCheck.checked ? "#E2BF6D" : "#536873"
                            Image { anchors.centerIn: parent; visible: pricelessCheck.checked; source: "../assets/icons/check.svg"; width: 13; height: 13 }
                        }
                        contentItem: Text {
                            text: pricelessCheck.text
                            color: "#E1E8EA"
                            font.pixelSize: 13
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: pricelessCheck.indicator.width + pricelessCheck.spacing
                        }
                    }
                    Text { text: "Rarity: " + root.controller.rarityLabel + " · independent field"; color: "#8196A0"; font.pixelSize: 10 }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#243641" }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    Text { text: "Equipment affixes"; color: "#E7ECEF"; font.pixelSize: 16; font.weight: Font.DemiBold }
                    Text { Layout.fillWidth: true; text: root.controller.slotLimitText; color: "#849BA6"; font.pixelSize: 10; elide: Text.ElideRight }
                }
                Text { text: root.controller.isDirty ? "UNSAVED" : "SAVED"; color: root.controller.isDirty ? "#E5BE72" : "#78C9B3"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
            }

            ScrollView {
                id: affixScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                ColumnLayout {
                    width: affixScroll.availableWidth
                    spacing: 14

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 7
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Prefix"; color: "#DDE7EB"; font.pixelSize: 13; font.weight: Font.DemiBold }
                            Text { Layout.fillWidth: true; text: root.controller.prefixCountLabel; color: "#869BA5"; font.pixelSize: 11 }
                            Text { text: root.controller.prefixHeaderHint; color: "#728893"; font.pixelSize: 10 }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Repeater {
                                model: root.controller.prefixAffixes
                                delegate: AffixRow {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    entry: modelData
                                    selected: root.controller.selectedInstanceId === modelData.id
                                    onActivated: (instanceId) => root.controller.selectAffixInstance(instanceId)
                                }
                            }
                            Text { visible: root.controller.prefixAffixes.length === 0; Layout.fillWidth: true; text: "No prefixes on this item yet."; color: "#758B96"; font.pixelSize: 11; leftPadding: 4 }
                        }

                        Button {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            id: addPrefixButton
                            text: "Add prefix"
                            onClicked: root.controller.beginAddAffix("prefix")
                            background: Rectangle { radius: 5; color: "#111F29"; border.color: "#344B58" }
                            contentItem: Text { text: addPrefixButton.text; color: "#9FC1C9"; font.pixelSize: 11; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#22343F" }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 7
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Suffix"; color: "#DDE7EB"; font.pixelSize: 13; font.weight: Font.DemiBold }
                            Text { Layout.fillWidth: true; text: root.controller.suffixCountLabel; color: "#869BA5"; font.pixelSize: 11 }
                            Text { text: root.controller.suffixHeaderHint; color: "#728893"; font.pixelSize: 10 }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Repeater {
                                model: root.controller.suffixAffixes
                                delegate: AffixRow {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    entry: modelData
                                    selected: root.controller.selectedInstanceId === modelData.id
                                    onActivated: (instanceId) => root.controller.selectAffixInstance(instanceId)
                                }
                            }
                            Text { visible: root.controller.suffixAffixes.length === 0; Layout.fillWidth: true; text: "No suffixes on this item yet."; color: "#758B96"; font.pixelSize: 11; leftPadding: 4 }
                        }

                        Button {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            id: addSuffixButton
                            text: "Add suffix"
                            onClicked: root.controller.beginAddAffix("suffix")
                            background: Rectangle { radius: 5; color: "#111F29"; border.color: "#344B58" }
                            contentItem: Text { text: addSuffixButton.text; color: "#9FC1C9"; font.pixelSize: 11; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                }
            }
        }
    }

    AffixSelector {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.minimumWidth: 455
        Layout.preferredWidth: 1.08
        controller: root.controller
    }
}
