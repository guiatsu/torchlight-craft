import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

Rectangle {
    id: root
    required property var browser
    color: Theme.surface
    border.color: Theme.borderSoft
    radius: Theme.radiusLarge

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 11

        RowLayout {
            Layout.fillWidth: true
            Text { text: "Possible Affixes"; color: Theme.text; font.pixelSize: 21; font.weight: Font.DemiBold }
            Item { Layout.fillWidth: true }
            Text { text: root.browser.selectedMode === "replace" ? "REPLACING" : root.browser.selectedMode === "edit" ? "EDITING" : "LOCAL CATALOG"; color: root.browser.selectedMode === "replace" ? Theme.warning : Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 0.7 }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Row {
                spacing: 4
                Repeater {
                    model: [
                        { id: "prefix", label: "Prefix" },
                        { id: "suffix", label: "Suffix" }
                    ]
                    delegate: Button {
                        id: groupButton
                        required property var modelData
                        text: modelData.label
                        onClicked: root.browser.setAffixGroup(modelData.id)
                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: root.browser.selectedGroup === modelData.id ? Theme.accentSoft : Theme.surfaceInset
                            border.color: root.browser.selectedGroup === modelData.id ? Theme.accent : Theme.borderSoft
                        }
                        contentItem: Text {
                            text: groupButton.text
                            color: root.browser.selectedGroup === modelData.id ? "#D1F4F5" : Theme.textSecondary
                            font.pixelSize: Theme.secondarySize
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
                Layout.preferredHeight: 36
                text: root.browser.searchQuery
                placeholderText: "Search affixes"
                placeholderTextColor: Theme.textMuted
                color: Theme.text
                font.pixelSize: Theme.secondarySize
                leftPadding: 11
                selectByMouse: true
                onTextEdited: root.browser.setSearchQuery(text)
                background: Rectangle {
                    color: Theme.surfaceInset
                    radius: Theme.radiusSmall
                    border.color: searchField.activeFocus ? Theme.accent : Theme.borderSoft
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                model: ["Basic", "Advanced", "Ultimate"]
                delegate: Button {
                    id: categoryButton
                    required property string modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    text: modelData
                    onClicked: root.browser.setAffixCategory(modelData)
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: root.browser.selectedCategory === modelData ? Theme.surfaceRaised : "transparent"
                        border.color: root.browser.selectedCategory === modelData ? Theme.border : "transparent"
                    }
                    contentItem: Text {
                        text: categoryButton.text
                        color: root.browser.selectedCategory === modelData ? Theme.text : Theme.textMuted
                        font.pixelSize: Theme.secondarySize
                        font.weight: root.browser.selectedCategory === modelData ? Font.DemiBold : Font.Medium
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSoft }

        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: "AFFIX"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
            Text { text: "TIERS"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
        }

        ButtonGroup { id: affixChoiceGroup }

        ListView {
            id: affixList
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(220, Math.max(100, root.browser.availableAffixes.length * 66 + 16))
            Layout.minimumHeight: 100
            Layout.maximumHeight: 220
            Layout.fillHeight: false
            clip: true
            spacing: 5
            model: root.browser.availableAffixes
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: RadioButton {
                id: candidate
                required property var modelData
                width: affixList.width - 8
                height: Math.max(58, candidateContent.implicitHeight + 14)
                checked: root.browser.selectedDefinitionId === modelData.id
                enabled: !modelData.alreadyAdded
                ButtonGroup.group: affixChoiceGroup
                onClicked: root.browser.selectDefinition(modelData.id)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: candidate.checked ? "#203945" : Theme.surfaceRaised
                    border.color: candidate.checked ? Theme.accent : Theme.borderSoft
                    opacity: candidate.enabled ? 1 : 0.55
                }

                indicator: Item {
                    width: 18
                    height: 18
                    x: candidate.width - width - 13
                    y: (candidate.height - height) / 2
                    Rectangle {
                        anchors.fill: parent
                        radius: width / 2
                        color: Theme.surfaceInset
                        border.color: candidate.checked ? Theme.accent : Theme.textMuted
                        border.width: candidate.checked ? 2 : 1
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: 8
                        height: 8
                        radius: 4
                        visible: candidate.checked
                        color: Theme.accent
                    }
                }

                RowLayout {
                    id: candidateContent
                    anchors.fill: candidate
                    anchors.leftMargin: 12
                    anchors.rightMargin: 42
                    anchors.topMargin: 7
                    anchors.bottomMargin: 7
                    spacing: 9
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            text: modelData.name
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.alreadyAdded ? "Already on this equipment" : "Compatibility provisional"
                            color: modelData.alreadyAdded ? Theme.warning : Theme.textMuted
                            font.pixelSize: 10
                        }
                    }
                    Text { text: modelData.tierSummary; color: Theme.basic; font.pixelSize: 10; font.weight: Font.DemiBold }
                }
            }

            ColumnLayout {
                anchors.centerIn: parent
                visible: root.browser.availableAffixes.length === 0
                spacing: 6
                Text { Layout.alignment: Qt.AlignHCenter; text: "No matching affixes"; color: Theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.maximumWidth: affixList.width - 36
                    text: "The local catalog has no entries for this base and filter. Unknown compatibility rules are not inferred."
                    color: Theme.textSecondary
                    font.pixelSize: Theme.secondarySize
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSoft }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text { text: root.browser.selectedDefinitionName; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight }
                    Text { text: root.browser.selectionVerificationText; color: Theme.textMuted; font.pixelSize: 10; elide: Text.ElideRight }
                }
                Button {
                    visible: root.browser.isEditingAffix
                    text: "Remove"
                    onClicked: root.browser.removeSelectedAffix()
                    background: Rectangle { radius: Theme.radiusSmall; color: "#332321"; border.color: "#704940" }
                    contentItem: Text { text: parent.text; color: Theme.error; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: root.browser.tierOptions
                    delegate: Button {
                        id: tierButton
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        enabled: modelData.eligible
                        text: modelData.eligible ? modelData.id : modelData.id + " · iLvl " + modelData.itemLevelRequired
                        onClicked: root.browser.setTier(modelData.id)
                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: root.browser.selectedTierId === modelData.id ? "#3B3150" : Theme.surfaceRaised
                            border.color: root.browser.selectedTierId === modelData.id ? Theme.advanced : Theme.borderSoft
                            opacity: modelData.eligible ? 1 : 0.55
                        }
                        contentItem: Text { text: tierButton.text; color: Theme.text; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: {
                    var options = root.browser.tierOptions
                    for (var i = 0; i < options.length; ++i)
                        if (options[i].id === root.browser.selectedTierId) return options[i].valueRange
                    return "Choose a tier to see its listed range."
                }
                color: Theme.textSecondary
                font.pixelSize: Theme.secondarySize
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
                    Layout.preferredHeight: 38
                    text: root.browser.selectedValue
                    placeholderText: "Affix value"
                    placeholderTextColor: Theme.textMuted
                    color: Theme.text
                    font.pixelSize: Theme.secondarySize
                    enabled: root.browser.selectedValueEditable
                    selectByMouse: true
                    onTextEdited: root.browser.setAffixValue(text)
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Theme.surfaceInset
                        border.color: valueField.activeFocus ? Theme.accent : Theme.borderSoft
                    }
                }
                Button {
                    id: commitAffixButton
                    Layout.preferredWidth: 138
                    Layout.preferredHeight: 38
                    text: root.browser.actionLabel
                    enabled: root.browser.selectedDefinitionId.length > 0 && root.browser.selectedTierEligible && !root.browser.selectedDefinitionAlreadyAdded
                    onClicked: root.browser.addOrUpdateAffix()
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: commitAffixButton.enabled ? Theme.gold : "#514838"
                        border.color: commitAffixButton.enabled ? Theme.goldBright : "#655B48"
                    }
                    contentItem: Text {
                        text: commitAffixButton.text
                        color: commitAffixButton.enabled ? "#17212A" : "#C4BAA2"
                        font.pixelSize: Theme.secondarySize
                        font.weight: Font.Bold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
