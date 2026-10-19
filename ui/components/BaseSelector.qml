import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

ColumnLayout {
    id: root
    required property var editor
    spacing: 6

    RowLayout {
        Layout.fillWidth: true
        spacing: 7

        ComboBox {
            id: categoryBox
            Layout.preferredWidth: 145
            Layout.preferredHeight: 36
            model: root.editor.baseCategories
            textRole: "name"
            currentIndex: {
                var list = root.editor.baseCategories
                for (var i = 0; i < list.length; ++i)
                    if (list[i].id === root.editor.selectedBaseCategory) return i
                return 0
            }
            onActivated: (index) => root.editor.setBaseCategory(root.editor.baseCategories[index].id)
            contentItem: Text {
                leftPadding: 10
                rightPadding: 24
                text: categoryBox.displayText
                color: Theme.text
                font.pixelSize: Theme.secondarySize
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surfaceInset
                border.color: categoryBox.activeFocus ? Theme.accent : Theme.borderSoft
            }
            indicator: Image {
                x: categoryBox.width - width - 9
                anchors.verticalCenter: parent.verticalCenter
                source: "../../assets/icons/down-chevron.svg"
                width: 10
                height: 10
            }
        }

        ComboBox {
            id: subcategoryBox
            Layout.preferredWidth: 170
            Layout.preferredHeight: 36
            model: root.editor.baseSubcategories
            textRole: "name"
            currentIndex: {
                var list = root.editor.baseSubcategories
                for (var i = 0; i < list.length; ++i)
                    if (list[i].id === root.editor.selectedBaseSubcategory) return i
                return 0
            }
            onActivated: (index) => root.editor.setBaseSubcategory(root.editor.baseSubcategories[index].id)
            contentItem: Text {
                leftPadding: 10
                rightPadding: 24
                text: subcategoryBox.displayText
                color: Theme.text
                font.pixelSize: Theme.secondarySize
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surfaceInset
                border.color: subcategoryBox.activeFocus ? Theme.accent : Theme.borderSoft
            }
            indicator: Image {
                x: subcategoryBox.width - width - 9
                anchors.verticalCenter: parent.verticalCenter
                source: "../../assets/icons/down-chevron.svg"
                width: 10
                height: 10
            }
        }

        TextField {
            id: baseSearch
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            text: root.editor.baseSearchQuery
            placeholderText: "Search equipment bases"
            placeholderTextColor: Theme.textMuted
            color: Theme.text
            font.pixelSize: Theme.secondarySize
            leftPadding: 10
            selectByMouse: true
            onTextEdited: root.editor.setBaseSearch(text)
            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.surfaceInset
                border.color: baseSearch.activeFocus ? Theme.accent : Theme.borderSoft
            }
        }
    }

    ComboBox {
        id: baseBox
        Layout.fillWidth: true
        Layout.preferredHeight: 36
        model: root.editor.baseOptions
        textRole: "name"
        currentIndex: {
            var list = root.editor.baseOptions
            for (var i = 0; i < list.length; ++i)
                if (list[i].id === root.editor.baseId) return i
            return -1
        }
        onActivated: (index) => root.editor.setBase(root.editor.baseOptions[index].id)
        contentItem: Text {
            leftPadding: 10
            rightPadding: 24
            text: baseBox.displayText || "Choose a base"
            color: Theme.text
            font.pixelSize: Theme.bodySize
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
            height: 47
            contentItem: ColumnLayout {
                spacing: 1
                Text {
                    text: modelData.name
                    color: Theme.text
                    font.pixelSize: Theme.secondarySize
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Text {
                    text: modelData.legacyAlias ? "Saved legacy placeholder" : modelData.craftingClass === "standard_craftable" ? "Standard crafting data" : modelData.craftingClass === "special_craftable" ? "Special system" : modelData.craftingClass === "non_craftable" ? "Non-craftable" : "Compatibility unknown"
                    color: Theme.textMuted
                    font.pixelSize: 9
                    Layout.fillWidth: true
                }
            }
            highlighted: baseBox.highlightedIndex === index
            background: Rectangle {
                color: highlighted ? Theme.surfaceRaised : Theme.surface
            }
        }
        popup.height: Math.min(420, baseBox.count * 47 + 12)
        ToolTip.visible: hovered
        ToolTip.text: root.editor.baseCraftingStatus + "\n" + root.editor.baseVerificationText + "\n" + root.editor.baseSourceUrl
        ToolTip.delay: 500
    }

    RowLayout {
        Layout.fillWidth: true
        Text {
            Layout.fillWidth: true
            text: root.editor.baseResultSummary
            color: Theme.textMuted
            font.pixelSize: 9
            elide: Text.ElideRight
        }
        Text {
            text: root.editor.baseCraftingStatus
            color: root.editor.baseCraftingStatus.startsWith("Standard") ? Theme.accent : Theme.warning
            font.pixelSize: 9
            elide: Text.ElideRight
        }
    }

    Text {
        Layout.fillWidth: true
        text: root.editor.characterRequirementText + " · " + root.editor.equipmentType
        color: Theme.textSecondary
        font.pixelSize: 9
        elide: Text.ElideRight
    }

    Text {
        Layout.fillWidth: true
        visible: root.editor.basePropertySummary.length > 0
        text: root.editor.basePropertySummary
        color: Theme.textSecondary
        font.pixelSize: 10
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        elide: Text.ElideRight
        HoverHandler { id: propertySummaryHover }
        ToolTip.visible: propertySummaryHover.hovered
        ToolTip.text: root.editor.baseSourceUrl + "\n" + root.editor.baseVerificationText
        ToolTip.delay: 500
    }
}
