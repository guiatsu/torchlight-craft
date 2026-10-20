import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

ColumnLayout {
    id: root
    required property var editor
    property bool expanded: false
    spacing: 6

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                Layout.fillWidth: true
                text: root.editor.baseName
                color: Theme.text
                font.pixelSize: 14
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Text {
                Layout.fillWidth: true
                text: root.editor.baseSubcategory + " · " + root.editor.baseCategory
                      + " · " + root.editor.baseCraftingStatus
                color: Theme.textSecondary
                font.pixelSize: 9
                elide: Text.ElideRight
            }
        }
        Button {
            text: root.expanded ? "Done" : "Choose base"
            onClicked: root.expanded = !root.expanded
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surfaceInset
                border.color: Theme.borderSoft
            }
            contentItem: Text {
                text: parent.text
                color: Theme.text
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                leftPadding: 9
                rightPadding: 9
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        CheckBox {
            text: "Suggest base"
            checked: root.editor.autoSuggestBase
            onToggled: root.editor.setAutoSuggestBase(checked)
            font.pixelSize: 10
        }
        Text {
            Layout.fillWidth: true
            text: root.editor.baseSuggestionSummary
            color: root.editor.canApplyBaseSuggestion ? Theme.accent : Theme.textMuted
            font.pixelSize: 9
            elide: Text.ElideRight
            ToolTip.visible: suggestionHover.hovered
            ToolTip.text: root.editor.baseSuggestionSummary
            ToolTip.delay: 500
            HoverHandler { id: suggestionHover }
        }
        Button {
            visible: root.editor.canApplyBaseSuggestion
            text: "Use"
            onClicked: root.editor.applySuggestedBase()
            background: Rectangle { radius: Theme.radiusSmall; color: Theme.accentSoft }
            contentItem: Text {
                text: parent.text
                color: Theme.text
                font.pixelSize: 9
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                leftPadding: 8
                rightPadding: 8
            }
        }
    }

    Text {
        Layout.fillWidth: true
        visible: root.editor.baseCompatibilityWarning.length > 0
        text: root.editor.baseCompatibilityWarning
        color: Theme.warning
        font.pixelSize: 9
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        elide: Text.ElideRight
    }

    ColumnLayout {
        Layout.fillWidth: true
        visible: root.expanded
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            ComboBox {
                id: classFilter
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                model: root.editor.baseClassFilters
                textRole: "name"
                currentIndex: {
                    var entries = root.editor.baseClassFilters
                    for (var i = 0; i < entries.length; ++i)
                        if (entries[i].id === root.editor.baseClassFilter) return i
                    return 0
                }
                onActivated: (index) => root.editor.setBaseClassFilter(root.editor.baseClassFilters[index].id)
                contentItem: Text {
                    leftPadding: 9
                    rightPadding: 23
                    text: classFilter.displayText
                    color: Theme.text
                    font.pixelSize: 9
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle { radius: Theme.radiusSmall; color: Theme.surfaceInset; border.color: Theme.borderSoft }
                indicator: Image {
                    x: classFilter.width - width - 8
                    anchors.verticalCenter: parent.verticalCenter
                    source: "../../assets/icons/down-chevron.svg"
                    width: 9
                    height: 9
                }
            }
            ComboBox {
                id: categoryBox
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                model: root.editor.baseCategories
                textRole: "name"
                currentIndex: {
                    var entries = root.editor.baseCategories
                    for (var i = 0; i < entries.length; ++i)
                        if (entries[i].id === root.editor.selectedBaseCategory) return i
                    return 0
                }
                onActivated: (index) => root.editor.setBaseCategory(root.editor.baseCategories[index].id)
                contentItem: Text {
                    leftPadding: 9
                    rightPadding: 23
                    text: categoryBox.displayText
                    color: Theme.text
                    font.pixelSize: 9
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle { radius: Theme.radiusSmall; color: Theme.surfaceInset; border.color: Theme.borderSoft }
                indicator: Image {
                    x: categoryBox.width - width - 8
                    anchors.verticalCenter: parent.verticalCenter
                    source: "../../assets/icons/down-chevron.svg"
                    width: 9
                    height: 9
                }
            }
            ComboBox {
                id: subcategoryBox
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                model: root.editor.baseSubcategories
                textRole: "name"
                currentIndex: {
                    var entries = root.editor.baseSubcategories
                    for (var i = 0; i < entries.length; ++i)
                        if (entries[i].id === root.editor.selectedBaseSubcategory) return i
                    return 0
                }
                onActivated: (index) => root.editor.setBaseSubcategory(root.editor.baseSubcategories[index].id)
                contentItem: Text {
                    leftPadding: 9
                    rightPadding: 23
                    text: subcategoryBox.displayText
                    color: Theme.text
                    font.pixelSize: 9
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle { radius: Theme.radiusSmall; color: Theme.surfaceInset; border.color: Theme.borderSoft }
                indicator: Image {
                    x: subcategoryBox.width - width - 8
                    anchors.verticalCenter: parent.verticalCenter
                    source: "../../assets/icons/down-chevron.svg"
                    width: 9
                    height: 9
                }
            }
        }

        TextField {
            id: baseSearch
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            text: root.editor.baseSearchQuery
            placeholderText: "Search equipment bases"
            placeholderTextColor: Theme.textMuted
            color: Theme.text
            font.pixelSize: 10
            leftPadding: 9
            selectByMouse: true
            onTextEdited: root.editor.setBaseSearch(text)
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surfaceInset
                border.color: baseSearch.activeFocus ? Theme.accent : Theme.borderSoft
            }
        }

        ComboBox {
            id: baseBox
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            model: root.editor.baseOptions
            textRole: "name"
            currentIndex: {
                var entries = root.editor.baseOptions
                for (var i = 0; i < entries.length; ++i)
                    if (entries[i].id === root.editor.baseId) return i
                return -1
            }
            onActivated: (index) => root.editor.setBase(root.editor.baseOptions[index].id)
            contentItem: Text {
                leftPadding: 10
                rightPadding: 24
                text: baseBox.displayText || "Choose a base"
                color: Theme.text
                font.pixelSize: 10
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surfaceInset
                border.color: baseBox.activeFocus ? Theme.accent : Theme.borderSoft
            }
            indicator: Image {
                x: baseBox.width - width - 9
                anchors.verticalCenter: parent.verticalCenter
                source: "../../assets/icons/down-chevron.svg"
                width: 10
                height: 10
            }
            delegate: ItemDelegate {
                required property var modelData
                width: baseBox.width
                height: 44
                contentItem: ColumnLayout {
                    spacing: 1
                    Text {
                        Layout.fillWidth: true
                        text: modelData.name
                        color: Theme.text
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.legacyAlias ? "Saved legacy base" : modelData.craftingClass === "standard_craftable" ? "Standard crafting data" : modelData.craftingClass === "special_craftable" ? "Special system" : modelData.craftingClass === "unknown" ? "Compatibility unknown" : "Not craftable"
                        color: Theme.textMuted
                        font.pixelSize: 8
                        elide: Text.ElideRight
                    }
                }
                highlighted: baseBox.highlightedIndex === index
                background: Rectangle { color: highlighted ? Theme.surfaceRaised : Theme.surface }
            }
            popup.height: Math.min(380, baseBox.count * 44 + 12)
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: root.editor.baseResultSummary
                color: Theme.textMuted
                font.pixelSize: 8
                elide: Text.ElideRight
            }
            Text {
                text: root.editor.characterRequirementText
                color: Theme.textSecondary
                font.pixelSize: 8
                elide: Text.ElideRight
                ToolTip.visible: requirementHover.hovered
                ToolTip.text: "Character level requirement is separate from equipment Item Level."
                HoverHandler { id: requirementHover }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: root.editor.basePropertySummary.length > 0
            text: root.editor.basePropertySummary
            color: Theme.textSecondary
            font.pixelSize: 9
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            HoverHandler { id: propertySummaryHover }
            ToolTip.visible: propertySummaryHover.hovered
            ToolTip.text: root.editor.baseSourceUrl + "\n" + root.editor.baseVerificationText
            ToolTip.delay: 500
        }
    }
}
