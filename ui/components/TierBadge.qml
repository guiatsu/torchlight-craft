import QtQuick

Rectangle {
    id: badge
    required property string tier
    property string category: "Basic"
    implicitWidth: tierLabel.implicitWidth + 14
    implicitHeight: 23
    radius: 4
    color: category === "Ultimate" ? "#342B4D" : category === "Advanced" ? "#352645" : "#3A3022"
    border.color: category === "Ultimate" ? "#9C79D7" : category === "Advanced" ? "#AA6FDB" : "#C89445"
    border.width: 1

    Text {
        id: tierLabel
        anchors.centerIn: parent
        text: badge.tier
        color: badge.category === "Ultimate" ? "#D1B6F3" : badge.category === "Advanced" ? "#D4A5F0" : "#E6BD73"
        font.pixelSize: 11
        font.weight: Font.DemiBold
    }
}
