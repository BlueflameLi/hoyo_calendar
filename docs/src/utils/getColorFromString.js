export const getColorFromString = str => {
    if (!str) return '#1890ff' // 默认颜色

    // 检测系统颜色模式
    const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches

    switch (str) {
        case "原神":
            return isDarkMode ? "#c2383d" : "#F16B6F"
        case "崩坏：星穹铁道":
            return isDarkMode ? "#7f9eb2" : "#C5C6B6"
        case "绝区零":
            return isDarkMode ? "#aacd78" : "#AACD6E"
        default:
            return '#1890ff'
    }
}