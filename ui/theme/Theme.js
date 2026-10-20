.pragma library

var background = "#081722"
var backgroundRaised = "#102431"
var surface = "#101F2A"
var surfaceRaised = "#172A36"
var surfaceInset = "#0B1922"
var border = "#344B58"
var borderSoft = "#273C48"
var text = "#E8EEF0"
var textSecondary = "#A9BBC3"
var textMuted = "#8B9FA8"
var accent = "#61C6D0"
var accentSoft = "#294651"
var gold = "#D7A542"
var goldBright = "#F0C96E"
var warning = "#E3B95E"
var error = "#E5A091"
var success = "#82C8B4"
var basic = "#D5AA56"
var advanced = "#BE91DE"
var ultimate = "#A7B7E7"

function tierBackground(tier) {
    if (tier === "T1") return "#382A23"
    if (tier === "T2") return "#30213A"
    return "#25343C"
}

function tierBorder(tier) {
    if (tier === "T1") return "#B97938"
    if (tier === "T2") return "#9655B7"
    return "#60727C"
}

function tierText(tier) {
    if (tier === "T1") return "#F18A69"
    if (tier === "T2") return "#D6A0EE"
    return "#BDCAD0"
}

var radiusSmall = 4
var radiusMedium = 7
var radiusLarge = 10
var gapSmall = 6
var gapMedium = 10
var gapLarge = 16
var bodySize = 13
var secondarySize = 11
