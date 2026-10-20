import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

Rectangle {
    id: root
    required property var crafting
    color: Theme.surface
    border.color: Theme.borderSoft
    radius: Theme.radiusLarge

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 9

        RowLayout {
            Layout.fillWidth: true
            Text { text: "CRAFTING WORKSPACE"; color: Theme.textMuted; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1 }
            Item { Layout.fillWidth: true }
            Text { text: root.crafting.modelName; color: Theme.warning; font.pixelSize: 10; font.weight: Font.DemiBold }
        }

        Text {
            Layout.fillWidth: true
            text: "One random outcome from the selected standard-craft pool. The chosen row below only opens its probability details."
            color: Theme.textSecondary
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 5
            Repeater {
                model: ["Basic", "Advanced", "Ultimate"]
                delegate: Button {
                    required property string modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    text: modelData
                    onClicked: root.crafting.setCategory(modelData)
                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: root.crafting.selectedCategory === modelData ? "#263E49" : Theme.surfaceInset
                        border.color: root.crafting.selectedCategory === modelData ? Theme.accent : Theme.border
                    }
                    contentItem: Text {
                        text: parent.text
                        color: modelData === "Basic" ? Theme.basic : modelData === "Advanced" ? Theme.advanced : Theme.ultimate
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: optInRow.implicitHeight + 16
            radius: Theme.radiusSmall
            color: "#302719"
            border.color: "#846A3B"
            RowLayout {
                id: optInRow
                anchors.fill: parent
                anchors.margins: 7
                spacing: 8
                CheckBox {
                    id: modelOptIn
                    checked: root.crafting.experimentalEnabled
                    onToggled: root.crafting.setExperimentalEnabled(checked)
                    indicator: Rectangle {
                        implicitWidth: 18; implicitHeight: 18
                        x: modelOptIn.leftPadding; y: parent.height / 2 - height / 2
                        radius: 3
                        color: modelOptIn.checked ? Theme.gold : Theme.surfaceInset
                        border.color: modelOptIn.checked ? Theme.goldBright : Theme.border
                        Text { anchors.centerIn: parent; visible: modelOptIn.checked; text: "✓"; color: "#17212A"; font.pixelSize: 13; font.bold: true }
                    }
                    contentItem: Text {
                        text: "Enable TLIDB Weighted (Experimental)"
                        color: Theme.text
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        leftPadding: modelOptIn.indicator.width + modelOptIn.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: "TLIDB weights are community data; they are not verified in-game odds. Numeric values inside a tier range are not simulated."
            color: Theme.warning
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }
        Text {
            Layout.fillWidth: true
            text: root.crafting.ruleStatusSummary
            color: Theme.textMuted
            font.pixelSize: 8
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: targetColumn.implicitHeight + 14
            radius: Theme.radiusSmall
            color: Theme.surfaceInset
            border.color: Theme.border
            ColumnLayout {
                id: targetColumn
                anchors.fill: parent
                anchors.margins: 8
                spacing: 3
                Text { text: "ATTEMPT PREVIEW"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 0.8 }
                Text {
                    Layout.fillWidth: true
                    text: root.crafting.baseName + " · Item Level " + root.crafting.itemLevel + " · " + root.crafting.operationLabel
                    color: Theme.text
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    text: root.crafting.poolConstructed
                        ? (root.crafting.selectedCategory + " pool · " + root.crafting.familyCount + " families · " + root.crafting.rollableOutcomeCount + " rollable rows · total weight " + root.crafting.totalWeight)
                        : root.crafting.poolMessage
                    color: root.crafting.poolAvailable ? Theme.textSecondary : Theme.warning
                    font.pixelSize: 10
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    visible: root.crafting.poolConstructed
                    text: "Pool ID: " + root.crafting.poolId
                    color: Theme.textMuted
                    font.pixelSize: 8
                    wrapMode: Text.WrapAnywhere
                }
                Text {
                    Layout.fillWidth: true
                    visible: root.crafting.poolConstructed
                    text: root.crafting.slotEvidenceText
                    color: Theme.warning
                    font.pixelSize: 8
                    wrapMode: Text.WordWrap
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text { text: "POSSIBLE AFFIX FAMILIES"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 0.8 }
            Item { Layout.fillWidth: true }
            Text { text: "FAMILY CHANCE · HIGHEST TIER"; color: Theme.textMuted; font.pixelSize: 9; font.weight: Font.Bold }
        }

        ScrollView {
            id: candidatesScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 90
            clip: true
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            ColumnLayout {
                width: candidatesScroll.availableWidth
                spacing: 4
                Repeater {
                    model: root.crafting.candidates
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: candidateRow.implicitHeight + 12
                        radius: Theme.radiusSmall
                        color: modelData.selected ? "#203A47" : Theme.surfaceRaised
                        border.color: modelData.selected ? Theme.accent : Theme.borderSoft
                        Accessible.role: Accessible.RadioButton
                        Accessible.name: modelData.name + " · " + modelData.chance
                        Accessible.checked: modelData.selected
                        RowLayout {
                            id: candidateRow
                            anchors.fill: parent
                            anchors.margins: 7
                            spacing: 8
                            Rectangle {
                                width: 18; height: 18; radius: 9
                                color: "transparent"
                                border.width: 1.5
                                border.color: modelData.selected ? Theme.accent : Theme.textMuted
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 8; height: 8; radius: 4
                                    color: Theme.accent
                                    visible: modelData.selected
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    color: Theme.text
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.highestTier + " · " + modelData.highestRange + " · family weight " + modelData.familyWeight
                                    color: Theme.textSecondary
                                    font.pixelSize: 9
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 1
                                    elide: Text.ElideRight
                                }
                            }
                            Text { text: modelData.chance; color: Theme.accent; font.pixelSize: 9; font.weight: Font.DemiBold }
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.crafting.selectFamily(modelData.familyId)
                        }
                    }
                }
                Text {
                    visible: root.crafting.candidates.length === 0
                    Layout.fillWidth: true
                    text: root.crafting.poolMessage || "No eligible outcomes in this pool."
                    color: Theme.textMuted
                    font.pixelSize: 10
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 132
            visible: root.crafting.selectedTiers.length > 0
            color: Theme.surfaceInset
            border.color: Theme.border
            radius: Theme.radiusSmall
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 4
                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: root.crafting.selectedFamilyName; color: Theme.text; font.pixelSize: 10; font.weight: Font.DemiBold; elide: Text.ElideRight }
                    Text { text: "TIER CHANCES"; color: Theme.textMuted; font.pixelSize: 8; font.weight: Font.Bold }
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                    ColumnLayout {
                        width: parent.width
                        spacing: 3
                        Repeater {
                            model: root.crafting.selectedTiers
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 6
                                Rectangle {
                                    implicitWidth: tierText.implicitWidth + 12
                                    implicitHeight: 19
                                    radius: 3
                                    color: Theme.tierBackground(modelData.tierLabel)
                                    border.color: Theme.tierBorder(modelData.tierLabel)
                                    Text { id: tierText; anchors.centerIn: parent; text: modelData.tierLabel; color: Theme.tierText(modelData.tierLabel); font.pixelSize: 9; font.weight: Font.DemiBold }
                                }
                                Text { Layout.fillWidth: true; text: modelData.range; color: modelData.rollable ? Theme.textSecondary : Theme.textMuted; font.pixelSize: 9; elide: Text.ElideRight }
                                Text { text: "w " + modelData.weight; color: Theme.textMuted; font.pixelSize: 8 }
                                ColumnLayout {
                                    spacing: 1
                                    Text {
                                        text: modelData.rollable ? modelData.jointChance : "0 weight · never drawn"
                                        color: modelData.rollable ? Theme.accent : Theme.textMuted
                                        font.pixelSize: 8
                                        horizontalAlignment: Text.AlignRight
                                    }
                                    Text {
                                        visible: modelData.rollable
                                        text: "within family: " + modelData.conditionalChance
                                        color: Theme.textMuted
                                        font.pixelSize: 8
                                        horizontalAlignment: Text.AlignRight
                                    }
                                }
                            }
                        }
                    }
                }
                Text { text: "Joint chance = this tier from the full pool · Conditional chance = tier within this family"; color: Theme.textMuted; font.pixelSize: 8; wrapMode: Text.WordWrap }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: resultColumn.implicitHeight + 12
            radius: Theme.radiusSmall
            color: "#101D26"
            border.color: Theme.borderSoft
            ColumnLayout {
                id: resultColumn
                anchors.fill: parent
                anchors.margins: 7
                spacing: 3
                Text { text: "LAST SESSION RESULT"; color: Theme.textMuted; font.pixelSize: 8; font.weight: Font.Bold; font.letterSpacing: 0.7 }
                Text { Layout.fillWidth: true; text: root.crafting.lastResultText; color: Theme.textSecondary; font.pixelSize: 9; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                text: "Craft once"
                enabled: root.crafting.canCraft
                onClicked: root.crafting.craftOnce()
                background: Rectangle { radius: 5; color: parent.enabled ? Theme.gold : "#514832"; border.color: parent.enabled ? Theme.goldBright : "#716342" }
                contentItem: Text { text: parent.text; color: parent.enabled ? "#152029" : "#A49A7F"; font.pixelSize: 12; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
            Button {
                Layout.preferredWidth: 85
                Layout.preferredHeight: 40
                text: "Undo"
                enabled: root.crafting.canUndo
                onClicked: root.crafting.undoLast()
                background: Rectangle { radius: 5; color: parent.enabled ? Theme.surfaceRaised : Theme.surfaceInset; border.color: Theme.border }
                contentItem: Text { text: parent.text; color: parent.enabled ? Theme.text : Theme.textMuted; font.pixelSize: 11; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }
        Text { Layout.alignment: Qt.AlignRight; text: root.crafting.historyCount + " craft(s) in this session · not saved as history"; color: Theme.textMuted; font.pixelSize: 8 }
    }
}
