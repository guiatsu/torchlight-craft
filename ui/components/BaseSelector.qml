import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme/Theme.js" as Theme

RowLayout {
    id: root
    required property var editor
    spacing: 8

    ComboBox {
        id: categoryBox
        Layout.preferredWidth: 126
        Layout.preferredHeight: 38
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
            leftPadding: 11
            rightPadding: 25
            text: categoryBox.displayText
            color: Theme.text
            font.pixelSize: Theme.bodySize
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: Theme.radiusSmall
            color: Theme.surfaceInset
            border.color: categoryBox.activeFocus ? Theme.accent : Theme.borderSoft
        }
        indicator: Image {
            x: categoryBox.width - width - 10
            anchors.verticalCenter: parent.verticalCenter
            source: "../../assets/icons/down-chevron.svg"
            width: 11
            height: 11
        }
    }

    ComboBox {
        id: baseBox
        Layout.fillWidth: true
        Layout.minimumWidth: 150
        Layout.preferredHeight: 38
        model: root.editor.baseOptions
        textRole: "name"
        currentIndex: {
            var list = root.editor.baseOptions
            for (var i = 0; i < list.length; ++i)
                if (list[i].id === root.editor.baseId) return i
            return 0
        }
        onActivated: (index) => root.editor.setBase(root.editor.baseOptions[index].id)
        contentItem: Text {
            leftPadding: 11
            rightPadding: 25
            text: baseBox.displayText
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
            x: baseBox.width - width - 10
            anchors.verticalCenter: parent.verticalCenter
            source: "../../assets/icons/down-chevron.svg"
            width: 11
            height: 11
        }
        ToolTip.visible: hovered
        ToolTip.text: root.editor.equipmentType + " · " + root.editor.characterRequirementText + " · " + root.editor.baseVerificationText
        ToolTip.delay: 500
    }
}
