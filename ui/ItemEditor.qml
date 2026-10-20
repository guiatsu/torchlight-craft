import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "theme/Theme.js" as Theme

RowLayout {
    id: root
    required property var editor
    required property var browser
    required property var crafting
    required property bool craftingMode
    spacing: 14

    Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.minimumWidth: 360
        Layout.preferredWidth: 0.42
        color: Theme.surface
        border.color: Theme.borderSoft
        radius: Theme.radiusLarge

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 10

            BaseSelector { Layout.fillWidth: true; editor: root.editor }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    Layout.preferredWidth: 64
                    Layout.preferredHeight: 64
                    radius: Theme.radiusMedium
                    color: "#152B39"
                    border.color: "#53626B"
                    Image {
                        anchors.fill: parent
                        anchors.margins: 3
                        source: "../assets/icons/weapon-sigil.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    TextField {
                        Layout.fillWidth: true
                        text: root.editor.itemName
                        placeholderText: "Equipment name"
                        placeholderTextColor: Theme.textMuted
                        color: Theme.text
                        font.pixelSize: 19
                        font.weight: Font.DemiBold
                        selectByMouse: true
                        maximumLength: 80
                        onTextEdited: root.editor.setItemName(text)
                        background: Rectangle { color: "transparent" }
                    }
                    Text {
                        text: root.editor.baseSubcategory + " · " + root.editor.baseCategory
                        color: Theme.textSecondary
                        font.pixelSize: Theme.secondarySize
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 9
                Text { text: "Item Level"; color: Theme.textSecondary; font.pixelSize: Theme.secondarySize }
                SpinBox {
                    id: itemLevelSpin
                    Layout.preferredWidth: 110
                    Layout.preferredHeight: 34
                    from: 1
                    to: 100
                    value: root.editor.itemLevel
                    editable: true
                    validator: IntValidator { bottom: 1; top: 100 }
                    onValueModified: root.editor.setItemLevel(value)
                    palette.text: Theme.text
                    palette.buttonText: Theme.text
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Theme.surfaceInset
                        border.color: itemLevelSpin.activeFocus ? Theme.accent : Theme.borderSoft
                    }
                }
                CheckBox {
                    id: pricelessCheck
                    text: "Priceless"
                    checked: root.editor.priceless
                    onToggled: root.editor.setPriceless(checked)
                    spacing: 6
                    indicator: Rectangle {
                        implicitWidth: 18
                        implicitHeight: 18
                        x: pricelessCheck.leftPadding
                        y: parent.height / 2 - height / 2
                        radius: 3
                        color: pricelessCheck.checked ? Theme.gold : Theme.surfaceInset
                        border.color: pricelessCheck.checked ? Theme.goldBright : Theme.border
                        Image {
                            anchors.centerIn: parent
                            visible: pricelessCheck.checked
                            source: "../assets/icons/check.svg"
                            width: 12
                            height: 12
                        }
                    }
                    contentItem: Text {
                        text: pricelessCheck.text
                        color: Theme.text
                        font.pixelSize: Theme.bodySize
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: pricelessCheck.indicator.width + pricelessCheck.spacing
                    }
                }
                Item { Layout.fillWidth: true }
                Text {
                    text: root.editor.rarityLabel === "Not set" ? "Rarity not set" : root.editor.rarityLabel
                    color: Theme.textMuted
                    font.pixelSize: 10
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSoft }

            Rectangle {
                visible: root.editor.hasIncompatibleAffixes
                Layout.fillWidth: true
                implicitHeight: incompatibleLayout.implicitHeight + 18
                radius: Theme.radiusSmall
                color: "#342D1F"
                border.color: "#887044"
                ColumnLayout {
                    id: incompatibleLayout
                    anchors.fill: parent
                    anchors.margins: 9
                    spacing: 6
                    Text {
                        text: "Review incompatible affixes before saving"
                        color: Theme.warning
                        font.pixelSize: Theme.secondarySize
                        font.weight: Font.DemiBold
                    }
                    Repeater {
                        model: root.editor.incompatibleAffixes
                        delegate: Text {
                            required property var modelData
                            Layout.fillWidth: true
                            text: "• " + modelData.name + " — " + modelData.reason
                            color: Theme.textSecondary
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }
                    Button {
                        Layout.alignment: Qt.AlignRight
                        text: "Remove incompatible"
                        onClicked: incompatibleConfirm.open()
                        background: Rectangle { radius: Theme.radiusSmall; color: "#46372A"; border.color: "#8B6940" }
                        contentItem: Text {
                            text: parent.text
                            color: "#F0D9B2"
                            font.pixelSize: 10
                            font.weight: Font.DemiBold
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    text: "Prefix (" + root.editor.prefixCountLabel + ")"
                    color: Theme.text
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
                Item { Layout.fillWidth: true }
                Text {
                    visible: root.editor.prefixHeaderHint.indexOf("unknown") >= 0
                    text: root.editor.prefixHeaderHint
                    color: Theme.textMuted
                    font.pixelSize: 10
                }
            }

            ScrollView {
                id: prefixScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 95
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                ColumnLayout {
                    width: prefixScroll.availableWidth
                    spacing: 5
                    Repeater {
                        model: root.editor.prefixSlots
                        delegate: AffixSlot {
                            required property var modelData
                            Layout.fillWidth: true
                            slot: modelData
                            group: "prefix"
                            selectedInstanceId: root.browser.selectedInstanceId
                            selectedGroup: root.browser.selectedGroup
                            selectedSlotIndex: root.browser.selectedSlotIndex
                            onEditRequested: (instanceId) => root.browser.selectAffixInstance(instanceId)
                            onAddRequested: (group, index) => root.browser.beginAddAffixAtSlot(group, index)
                        }
                    }
                    Button {
                        visible: root.editor.prefixHeaderHint.indexOf("unknown") >= 0
                        Layout.fillWidth: true
                        text: "+  Add prefix"
                        onClicked: root.browser.beginAddAffix("prefix")
                        background: Rectangle { radius: Theme.radiusSmall; color: "#0C1B25"; border.color: Theme.border }
                        contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: Theme.secondarySize; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSoft }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    text: "Suffix (" + root.editor.suffixCountLabel + ")"
                    color: Theme.text
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                }
                Item { Layout.fillWidth: true }
                Text {
                    visible: root.editor.suffixHeaderHint.indexOf("unknown") >= 0
                    text: root.editor.suffixHeaderHint
                    color: Theme.textMuted
                    font.pixelSize: 10
                }
            }

            ScrollView {
                id: suffixScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 95
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                ColumnLayout {
                    width: suffixScroll.availableWidth
                    spacing: 5
                    Repeater {
                        model: root.editor.suffixSlots
                        delegate: AffixSlot {
                            required property var modelData
                            Layout.fillWidth: true
                            slot: modelData
                            group: "suffix"
                            selectedInstanceId: root.browser.selectedInstanceId
                            selectedGroup: root.browser.selectedGroup
                            selectedSlotIndex: root.browser.selectedSlotIndex
                            onEditRequested: (instanceId) => root.browser.selectAffixInstance(instanceId)
                            onAddRequested: (group, index) => root.browser.beginAddAffixAtSlot(group, index)
                        }
                    }
                    Button {
                        visible: root.editor.suffixHeaderHint.indexOf("unknown") >= 0
                        Layout.fillWidth: true
                        text: "+  Add suffix"
                        onClicked: root.browser.beginAddAffix("suffix")
                        background: Rectangle { radius: Theme.radiusSmall; color: "#0C1B25"; border.color: Theme.border }
                        contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: Theme.secondarySize; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                }
            }
        }
    }

    Loader {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.minimumWidth: 470
        Layout.preferredWidth: 0.58
        sourceComponent: root.craftingMode ? craftWorkspace : editWorkspace
    }

    Component {
        id: editWorkspace
        AffixSelector { browser: root.browser }
    }

    Component {
        id: craftWorkspace
        CraftPanel { crafting: root.crafting }
    }

    Dialog {
        id: incompatibleConfirm
        modal: true
        title: "Remove incompatible affixes?"
        anchors.centerIn: Overlay.overlay
        width: Math.min(400, root.width - 40)
        height: 190
        standardButtons: Dialog.NoButton
        background: Rectangle { radius: Theme.radiusMedium; color: Theme.surface; border.color: Theme.border }
        contentItem: Text {
            text: "This removes the listed affixes from the current equipment. The change can be undone by closing without saving."
            color: Theme.textSecondary
            font.pixelSize: Theme.bodySize
            wrapMode: Text.WordWrap
        }
        footer: RowLayout {
            Item { Layout.fillWidth: true }
            Button { text: "Cancel"; onClicked: incompatibleConfirm.close() }
            Button {
                text: "Remove affixes"
                onClicked: { root.editor.removeIncompatibleAffixes(); incompatibleConfirm.close() }
                background: Rectangle { radius: Theme.radiusSmall; color: Theme.gold; border.color: Theme.goldBright }
                contentItem: Text { text: parent.text; color: "#152029"; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }
    }
}
