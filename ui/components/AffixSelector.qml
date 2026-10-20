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
            spacing: 10
            Text {
                Layout.fillWidth: true
                text: root.browser.selectedTargetLabel
                color: Theme.textSecondary
                font.pixelSize: Theme.secondarySize
                font.weight: Font.Medium
                elide: Text.ElideRight
            }
            TextField {
                id: searchField
                Layout.preferredWidth: Math.min(250, root.width * 0.52)
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
                    text: modelData + " Affix"
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

        Text {
            Layout.fillWidth: true
            text: root.browser.selectedMode === "replace"
                ? "Choose a replacement for the selected affix slot."
                : root.browser.selectedMode === "edit"
                  ? "Choose a catalog option to update this affix."
                  : "Choose an affix for the selected slot."
            color: Theme.textMuted
            font.pixelSize: Theme.secondarySize
            elide: Text.ElideRight
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: Theme.borderSoft }

        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: "POSSIBLE AFFIXES"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
            Text { text: "TIER"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
        }

        ButtonGroup { id: affixChoiceGroup }

        ListView {
            id: affixList
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(320, Math.max(100, root.browser.availableAffixes.length * 66 + 16))
            Layout.minimumHeight: 100
            Layout.maximumHeight: 320
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
                            text: modelData.displayTierDescription || modelData.highestTierDescription || modelData.name
                            color: Theme.text
                            font.pixelSize: Theme.bodySize
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.alreadyAdded
                                  ? "Already on this equipment"
                                  : modelData.categoryLabel + " · community reference"
                            color: modelData.alreadyAdded ? Theme.warning : Theme.textMuted
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }
                    Rectangle {
                        implicitWidth: highestTierLabel.implicitWidth + 14
                        Layout.minimumWidth: 34
                        Layout.preferredHeight: 21
                        radius: 3
                        color: modelData.displayTierEligible ? "#282A2C" : Theme.surfaceInset
                        border.color: modelData.displayTierEligible
                            ? Theme.tierBorder(modelData.displayTierLabel || modelData.highestTierLabel)
                            : Theme.borderSoft
                        opacity: modelData.displayTierEligible ? 1 : 0.7
                        Text {
                            id: highestTierLabel
                            anchors.centerIn: parent
                            text: modelData.displayTierLabel || modelData.highestTierLabel
                            color: Theme.tierText(modelData.displayTierLabel || modelData.highestTierLabel)
                            font.pixelSize: 10
                            font.weight: Font.DemiBold
                        }
                        ToolTip.visible: highestTierHover.hovered
                        ToolTip.text: modelData.displayTierIsSelected
                            ? "Selected tier · " + modelData.tierCount + " source tiers"
                            : modelData.highestTierEligible
                              ? "Highest tier eligible for this item's Item Level · " + modelData.tierCount + " source tiers"
                              : "Top tier requires Item Level " + modelData.highestTierItemLevelRequired
                                + " · " + modelData.tierCount + " source tiers"
                        ToolTip.delay: 450
                        HoverHandler { id: highestTierHover }
                    }
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

            GridView {
                id: tierGrid
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(112, Math.max(38,
                    Math.ceil(root.browser.tierOptions.length / Math.max(1, Math.floor(width / 64))) * 38))
                cellWidth: width / Math.max(1, Math.floor(width / 64))
                cellHeight: 38
                clip: true
                model: root.browser.tierOptions
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                delegate: Button {
                    id: tierButton
                    required property var modelData
                    width: tierGrid.cellWidth - 5
                    height: 33
                    enabled: modelData.eligible
                    text: modelData.tierLabel
                    onClicked: root.browser.setTier(modelData.id)
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: root.browser.selectedTierId === modelData.id
                            ? Theme.tierBackground(modelData.tierLabel)
                            : Theme.surfaceRaised
                        border.color: root.browser.selectedTierId === modelData.id
                            ? Theme.tierBorder(modelData.tierLabel)
                            : Theme.borderSoft
                        opacity: modelData.eligible ? 1 : 0.55
                    }
                    contentItem: Text {
                        text: tierButton.text
                        color: root.browser.selectedTierId === modelData.id
                            ? Theme.tierText(modelData.tierLabel)
                            : modelData.eligible ? Theme.text : Theme.textMuted
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    ToolTip.visible: hovered
                    ToolTip.delay: 450
                    ToolTip.text: modelData.valueRange
                        + "\n" + (modelData.itemLevelRequired === null ? "Item Level not listed" : "Requires Item Level " + modelData.itemLevelRequired)
                        + " · Weight " + (modelData.weightRaw === null ? "not listed" : modelData.weightRaw)
                        + "\n" + modelData.sourceSection + " · " + modelData.sourceRowKey
                }
            }

            Connections {
                target: root.browser
                function onSelectionChanged() {
                    // TextField loses its initial text binding after keyboard input.
                    // Resync it when a tier or affix selection changes.
                    valueField.text = root.browser.selectedValue
                    var options = root.browser.tierOptions
                    var selected = -1
                    for (var i = 0; i < options.length; ++i) {
                        if (options[i].id === root.browser.selectedTierId) {
                            selected = i
                            break
                        }
                    }
                    if (selected >= 0)
                        tierGrid.positionViewAtIndex(selected, GridView.Contain)
                    else
                        tierGrid.positionViewAtBeginning()
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

            Text {
                Layout.fillWidth: true
                visible: root.browser.selectedTierAmbiguous
                text: "This saved tier label matches multiple source records. Choose a specific record to resolve it."
                color: Theme.warning
                font.pixelSize: 9
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 7
                Text {
                    Layout.fillWidth: true
                    text: root.browser.selectedTierTechnicalText
                    color: Theme.textMuted
                    font.pixelSize: 9
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Button {
                    visible: root.browser.selectedTierSourceUrl.length > 0
                    text: "Source"
                    onClicked: Qt.openUrlExternally(root.browser.selectedTierSourceUrl)
                    background: Rectangle { radius: Theme.radiusSmall; color: Theme.surfaceInset; border.color: Theme.borderSoft }
                    contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 9; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
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
