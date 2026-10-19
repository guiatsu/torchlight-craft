import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property var controller
    spacing: 8

    RowLayout {
        Layout.fillWidth: true
        spacing: 10

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 5
            Text { text: "CATEGORY"; color: "#8398A5"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1.1 }
            ComboBox {
                id: categoryBox
                Layout.fillWidth: true
                model: root.controller.baseCategories
                textRole: "name"
                currentIndex: {
                    var list = root.controller.baseCategories
                    for (var i = 0; i < list.length; ++i) if (list[i].id === root.controller.selectedBaseCategory) return i
                    return 0
                }
                onActivated: (index) => root.controller.setBaseCategory(root.controller.baseCategories[index].id)
                contentItem: Text {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 30
                    text: categoryBox.displayText
                    color: "#EAF1F4"
                    font.pixelSize: 13
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle { radius: 6; color: "#101C26"; border.color: categoryBox.activeFocus ? "#68C9D4" : "#324856" }
                indicator: Image { x: categoryBox.width - width - 13; anchors.verticalCenter: parent.verticalCenter; source: "../../assets/icons/down-chevron.svg"; width: 12; height: 12 }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 5
            Text { text: "EQUIPMENT BASE"; color: "#8398A5"; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 1.1 }
            ComboBox {
                id: baseBox
                Layout.fillWidth: true
                model: root.controller.baseOptions
                textRole: "name"
                currentIndex: {
                    var list = root.controller.baseOptions
                    for (var i = 0; i < list.length; ++i) if (list[i].id === root.controller.baseId) return i
                    return 0
                }
                onActivated: (index) => root.controller.setBase(root.controller.baseOptions[index].id)
                contentItem: Text {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 30
                    text: baseBox.displayText
                    color: "#EAF1F4"
                    font.pixelSize: 13
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle { radius: 6; color: "#101C26"; border.color: baseBox.activeFocus ? "#68C9D4" : "#324856" }
                indicator: Image { x: baseBox.width - width - 13; anchors.verticalCenter: parent.verticalCenter; source: "../../assets/icons/down-chevron.svg"; width: 12; height: 12 }
            }
        }
    }

    Text {
        Layout.fillWidth: true
        text: root.controller.equipmentType + " · " + root.controller.characterRequirementText + " · " + root.controller.baseVerificationText
        color: "#94A8B3"
        font.pixelSize: 11
        elide: Text.ElideRight
    }
}
