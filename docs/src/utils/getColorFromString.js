export const getColorFromString = str => {
    if (!str) return '#1890ff' // 默认颜色

    // 检测系统颜色模式
    const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches

    switch (str) {
        case "原神":
            return isDarkMode ? "#808080" : "#aaaaaa"
        case "崩坏：星穹铁道":
            return isDarkMode ? "#555555" : "#bfbfbf"
        case "绝区零":
            return isDarkMode ? "#404040" : "#cccccc"
        default:
            return '#1890ff'
    }
}