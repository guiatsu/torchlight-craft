import QtQuick
import "../theme/Theme.js" as Theme

Rectangle {
    id: badge
    required property string tier
    implicitWidth: tierLabel.implicitWidth + 14
    implicitHeight: 23
    radius: 4
    color: Theme.tierBackground(tier)
    border.color: Theme.tierBorder(tier)
    border.width: 1

    Text {
        id: tierLabel
        anchors.centerIn: parent
        text: badge.tier
        color: Theme.tierText(badge.tier)
        font.pixelSize: 11
        font.weight: Font.DemiBold
    }
}
