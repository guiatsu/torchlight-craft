import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var controller
    color: "#0F1A24"
    border.color: "#314451"
    border.width: 1
    radius: 9

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text { text: "Affix catalogue"; color: "#E9EFF2"; font.pixelSize: 21; font.weight: Font.DemiBold }
                Text { text: "Select a listed property to add or edit it"; color: "#8DA2AE"; font.pixelSize: 12 }
            }
            Rectangle {
                radius: 4
                color: "#283122"
                border.color: "#677449"
                implicitWidth: verifiedLabel.implicitWidth + 18
                implicitHeight: 25
                Text { id: verifiedLabel; anchors.centerIn: parent; text: "LOCAL DATA"; color: "#C7D18D"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Row {
                spacing: 3
                Repeater {
                    model: [
                        { id: "prefix", label: "Prefix" },
                        { id: "suffix", label: "Suffix" }
                    ]
                    delegate: Button {
                        id: groupFilterButton
                        required property var modelData
                        text: modelData.label
                        onClicked: root.controller.setAffixGroup(modelData.id)
                        background: Rectangle {
                            radius: 5
                            color: root.controller.selectedGroup === modelData.id ? "#29414E" : "#121E28"
                            border.color: root.controller.selectedGroup === modelData.id ? "#59C2CF" : "#2C404D"
                        }
                        contentItem: Text {
                            text: groupFilterButton.text
                            color: root.controller.selectedGroup === modelData.id ? "#C5F2F5" : "#92A5AF"
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.preferredHeight: 38
                placeholderText: "Search affixes"
                placeholderTextColor: "#778D99"
                color: "#E6EDF0"
                font.pixelSize: 12
                leftPadding: 12
                onTextEdited: root.controller.setSearchQuery(text)
                background: Rectangle { color: "#0A141D"; radius: 5; border.color: searchField.activeFocus ? "#56BFCB" : "#2A3F4C" }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: ["Basic", "Advanced", "Ultimate"]
                delegate: Button {
                    id: categoryFilterButton
                    required property string modelData
                    Layout.fillWidth: true
                    text: modelData
                    onClicked: root.controller.setAffixCategory(modelData)
                    background: Rectangle {
                        radius: 5
                        color: root.controller.selectedCategory === modelData ? "#263946" : "transparent"
                        border.color: root.controller.selectedCategory === modelData ? "#647F8B" : "transparent"
                    }
                    contentItem: Text {
                        text: categoryFilterButton.text
                        color: root.controller.selectedCategory === modelData ? "#E8EFF2" : "#8498A3"
                        font.pixelSize: 12
                        font.weight: root.controller.selectedCategory === modelData ? Font.DemiBold : Font.Medium
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#243743" }

        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: "POSSIBLE AFFIXES"; color: "#8399A5"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1.2 }
            Text { text: "LISTED TIERS"; color: "#8399A5"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1.1 }
        }

        ButtonGroup { id: affixChoiceGroup }

        ListView {
            id: affixList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: root.controller.availableAffixes
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: RadioButton {
                id: candidate
                required property var modelData
                width: affixList.width - 8
                height: candidateContent.implicitHeight + 16
                checked: root.controller.selectedDefinitionId === modelData.id
                enabled: !modelData.alreadyAdded
                ButtonGroup.group: affixChoiceGroup
                onClicked: root.controller.selectDefinition(modelData.id)

                background: Rectangle {
                    radius: 5
                    color: candidate.checked ? "#243A46" : "#17232E"
                    border.color: candidate.checked ? "#56BFCC" : "#324652"
                    border.width: candidate.checked ? 1.3 : 1
                    opacity: candidate.enabled ? 1 : 0.62
                }

                indicator: Item {
                    width: 20
                    height: 20
                    x: candidate.width - width - 13
                    y: (candidate.height - height) / 2

                    Rectangle {
                        anchors.fill: parent
                        radius: width / 2
                        color: "#101B24"
                        border.color: candidate.checked ? "#66D0DC" : "#8999A0"
                        border.width: candidate.checked ? 2 : 1
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: 8
                        height: 8
                        radius: 4
                        visible: candidate.checked
                        color: "#66D0DC"
                    }
                }

                RowLayout {
                    id: candidateContent
                    anchors.fill: candidate
                    anchors.leftMargin: 12
                    anchors.rightMargin: 44
                    anchors.topMargin: 8
                    anchors.bottomMargin: 8
                    spacing: 10

                    Rectangle {
                        Layout.alignment: Qt.AlignTop
                        width: 24; height: 24; radius: 12
                        color: "#394852"; border.color: "#687B83"
                        Image { anchors.centerIn: parent; source: "../../assets/icons/info.svg"; width: 15; height: 15 }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            text: modelData.name
                            color: "#E5ECEF"
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.alreadyAdded ? "Already on this item" : modelData.category + " · Compatibility provisional"
                            color: modelData.alreadyAdded ? "#D8B771" : "#A0B1B8"
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }

                    Text { text: modelData.tierSummary; color: "#E8C16E"; font.pixelSize: 10; font.weight: Font.Bold }
                }
            }

            ColumnLayout {
                anchors.centerIn: parent
                visible: root.controller.availableAffixes.length === 0
                spacing: 8
                Text { Layout.alignment: Qt.AlignHCenter; text: "No entries in this view"; color: "#CED9DE"; font.pixelSize: 14; font.weight: Font.DemiBold }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.maximumWidth: affixList.width - 44
                    text: "The local catalogue has no matching affixes for this base and filter. No compatibility rules are being inferred."
                    color: "#8DA2AC"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#243743" }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 9

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    Text { text: root.controller.isEditingAffix ? "Edit selected affix" : "Selected affix"; color: "#E5ECEF"; font.pixelSize: 13; font.weight: Font.DemiBold }
                    Text { Layout.fillWidth: true; text: root.controller.selectionVerificationText; color: "#8FA6B1"; font.pixelSize: 10; elide: Text.ElideRight }
                }
                Button {
                    id: removeAffixButton
                    visible: root.controller.isEditingAffix
                    text: "Remove"
                    onClicked: root.controller.removeSelectedAffix()
                    background: Rectangle { radius: 5; color: "#322222"; border.color: "#71453F" }
                    contentItem: Text { text: removeAffixButton.text; color: "#F0B1A2"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 7
                Repeater {
                        model: root.controller.tierOptions
                    delegate: Button {
                        id: tierButton
                        required property var modelData
                        Layout.fillWidth: true
                        enabled: modelData.eligible
                        text: modelData.eligible ? modelData.id : modelData.id + " · " + modelData.itemLevelRequired
                        onClicked: root.controller.setTier(modelData.id)
                        background: Rectangle {
                            radius: 4
                            color: root.controller.selectedTierId === modelData.id ? "#42365A" : "#17232E"
                            border.color: root.controller.selectedTierId === modelData.id ? "#B08BE5" : "#334855"
                            opacity: modelData.eligible ? 1 : 0.5
                        }
                        contentItem: Text {
                            text: tierButton.text
                            color: "#D9C4F5"
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: {
                    var options = root.controller.tierOptions
                    for (var i = 0; i < options.length; ++i) if (options[i].id === root.controller.selectedTierId) return options[i].valueRange
                    return "Choose a tier to see its listed range."
                }
                color: "#9EAFB6"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                TextField {
                    id: valueField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    text: root.controller.selectedValue
                    placeholderText: "Editable display value"
                    placeholderTextColor: "#748A97"
                    color: "#E6EDF0"
                    font.pixelSize: 11
                    enabled: root.controller.selectedValueEditable
                    onTextEdited: root.controller.setAffixValue(text)
                    background: Rectangle { radius: 5; color: "#0A141D"; border.color: valueField.activeFocus ? "#56C2CE" : "#2C424F" }
                }
                Button {
                    id: commitAffixButton
                    Layout.preferredWidth: 132
                    Layout.preferredHeight: 40
                    text: root.controller.selectedDefinitionAlreadyAdded ? "Already added" : root.controller.isEditingAffix ? "Update affix" : "Add affix"
                    enabled: root.controller.selectedDefinitionId.length > 0 && root.controller.selectedTierEligible && !root.controller.selectedDefinitionAlreadyAdded
                    onClicked: root.controller.addOrUpdateAffix()
                    background: Rectangle {
                        radius: 5
                        color: commitAffixButton.enabled ? "#C99A43" : "#514838"
                        border.color: commitAffixButton.enabled ? "#E5BE69" : "#655B48"
                    }
                    contentItem: Text { text: commitAffixButton.text; color: commitAffixButton.enabled ? "#172028" : "#B0A58E"; font.pixelSize: 12; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
            }
        }
    }
}
