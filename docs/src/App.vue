<script setup>
import Footer from './components/Footer.vue'
import { reactive, ref, computed, watch, onMounted, onUnmounted } from "vue"
import { message } from 'ant-design-vue'
import Gantt from 'frappe-gantt'
import gamesListData from "./data/data.json"
import { getColorFromString } from './utils/getColorFromString'
import { formatDate } from './utils/dateHandler'


const gamesList = reactive(gamesListData.games)
const gamesData = ref({})
const showAnnInfo = ref(false)
const selectedAnnInfo = ref({})
const selectedGames = ref(gamesList)

const countdown = ref('')

// 计算倒计时的方法
const updateCountdown = () => {
    if (!selectedAnnInfo.value.end) {
        countdown.value = ''
        return
    }

    const endTime = new Date(selectedAnnInfo.value.end)
    const now = new Date()
    const diff = endTime - now

    if (diff <= 0) {
        countdown.value = '已结束'
        return
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)
    const paddedHours = String(hours).padStart(2, '0')
    const paddedMinutes = String(minutes).padStart(2, '0')
    const paddedSeconds = String(seconds).padStart(2, '0')

    countdown.value = `${days}天 ${paddedHours}:${paddedMinutes}:${paddedSeconds}`
}

const pageContentHeight = ref('auto')
let gantt = null
const updateGanttHeight = () => {
    const content_element = document.querySelector('.page-content')
    pageContentHeight.value = content_element.clientHeight
    if (gantt) {
        gantt.update_options({ container_height: pageContentHeight.value, })
    }
}
const updateGanttTask = checkedValue => {
    selectedGames.value.sort((a, b) => {
        return gamesList.indexOf(a) - gamesList.indexOf(b)
    })

    let tasks = []
    for (const game of selectedGames.value) {
        for (const ann of gamesData.value[game]) {
            tasks.push({
                id: stringToHash(ann.title),
                name: ann.title,
                banner: ann.banner,
                // description: ann.description,
                start: ann.start_time,
                end: ann.end_time,
                // progress: calculateTimePercentage(ann.start_time, ann.end_time),
                color: getColorFromString(game),
            })
        }
    }
    gantt.refresh(tasks)
}

const stringToHash = str => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash; // 转换为32位整数
    }
    return Math.abs(hash);
}

const isTodayBetweenDates = (startTime, endTime) => {
    const today = new Date();
    const startDate = new Date(startTime);
    const endDate = new Date(endTime);

    return today >= startDate && today <= endDate;
}

// const calculateTimePercentage = (startTime, endTime) => {
//     const start = new Date(startTime).getTime();
//     const end = new Date(endTime).getTime();
//     const current = new Date().getTime();

//     // 确保时间范围有效
//     if (start >= end) return 0;

//     // 计算百分比
//     const totalDuration = end - start;
//     const elapsedDuration = current - start;

//     // 处理边界情况
//     if (elapsedDuration <= 0) return 0;
//     if (elapsedDuration >= totalDuration) return 100;

//     // 返回0-100之间的数值，保留小数
//     const percentage = Math.floor((elapsedDuration / totalDuration) * 100);
//     console.log(percentage);
//     return percentage;
// }

/** 动态导入 JSON 文件 */
const loadData = async () => {
    // 动态导入 JSON 文件
    for (const game of gamesList) {
        gamesData.value[game] = []
        try {
            const data = (await import(`./data/${game}/data.json`)).default
            for (const version of data.version_list) {
                if (isTodayBetweenDates(version.start_time, version.end_time)) {
                    gamesData.value[game].push({
                        "title": `《${game}》${version.code}版本`,
                        "description": `《${game}》${version.code}版本 ${version.name}`,
                        "game": game,
                        "start_time": version.start_time,
                        "end_time": version.end_time,
                        "banner": version.banner,
                        "ann_type": "version"
                    })
                }
                for (const ann of version.ann_list) {
                    if (isTodayBetweenDates(ann.start_time, ann.end_time)) {
                        gamesData.value[game].push({
                            "title": ann.title,
                            "description": ann.description,
                            "game": game,
                            "start_time": ann.start_time,
                            "end_time": ann.end_time,
                            "banner": ann.banner,
                            "ann_type": ann.ann_type,
                        })
                    }
                }
            }
        } catch (error) {
            console.log(error)
            message.error(`加载 ${game} 数据失败`)
        }
    }
}

const loadGantt = async () => {
    // 创建 Gantt 实例
    try {
        let tasks = []
        for (const game of selectedGames.value) {
            for (const ann of gamesData.value[game]) {
                tasks.push({
                    id: stringToHash(ann.title),
                    name: ann.title,
                    banner: ann.banner,
                    // description: ann.description,
                    start: ann.start_time,
                    end: ann.end_time,
                    // progress: calculateTimePercentage(ann.start_time, ann.end_time),
                    color: getColorFromString(game),
                })
            }
        }
        gantt = new Gantt("#gantt", tasks, {
            // auto_move_label: true,
            language: "zh",
            readonly: true,
            container_height: pageContentHeight.value,
            infinite_padding: false,
            on_click: (task) => {
                showAnnInfo.value = true
                selectedAnnInfo.value = task
            },
            popup: false,
        })
    } catch (error) {
        console.log(error)
        message.error(`加载图表失败`)
    }
}


const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)')
const handleColorSchemeChange = (e) => {
    updateGanttTask()
}

// 处理鼠标滚轮事件，实现水平滚动
const handleGanttScroll = (e) => {
    e.preventDefault(); // 阻止默认的垂直滚动行为
    const ganttContainer = document.querySelector('.gantt-container');
    if (ganttContainer) {
        ganttContainer.scrollLeft += e.deltaY;
    }
}

// 监听路由参数变化并重新加载数据
onMounted(async () => {
    updateGanttHeight()
    await loadData()
    loadGantt()
    window.addEventListener('resize', updateGanttHeight)
    colorSchemeQuery.addEventListener('change', handleColorSchemeChange)
    const timer = setInterval(() => {
        if (showAnnInfo.value) {
            updateCountdown()
        }
    }, 1000)

    // 添加鼠标滚轮事件监听
    const ganttContainer = document.querySelector('.gantt-container')
    if (ganttContainer) {
        ganttContainer.addEventListener('wheel', handleGanttScroll)
    }
})
onUnmounted(() => {
    window.removeEventListener('resize', updateGanttHeight)
    clearInterval(timer)

    // 移除鼠标滚轮事件监听
    const ganttContainer = document.querySelector('.gantt-container');
    if (ganttContainer) {
        ganttContainer.removeEventListener('wheel', handleGanttScroll);
    }
})

</script>

<template>
    <a-layout class="page-layout">
        <a-layout-content class="page-content">
            <!-- 甘特图 -->
            <div id="gantt"></div>
            <!-- 弹窗 -->
            <div class="gantt-overlay">
                <a-card :bodyStyle="{ borderRadius: '8px', boxShadow: 'rgba(0, 0, 0, 0.2) 2px 2px 10px 0px' }">
                    <a-checkbox-group v-model:value="selectedGames" @change="updateGanttTask">
                        <a-checkbox v-for="game in gamesList" :value="game">
                            {{ game }}
                        </a-checkbox>
                    </a-checkbox-group>
                </a-card>
            </div>
            <div class="ann-info-overlay">
                <a-card v-if="showAnnInfo">
                    <template #cover>
                        <img :alt="selectedAnnInfo.name" :src="selectedAnnInfo.banner" />
                    </template>
                    <a-card-meta :title="selectedAnnInfo.name">
                        <template #description>
                            {{ formatDate(selectedAnnInfo.start) }} - {{ formatDate(selectedAnnInfo.end) }}
                            <br />
                            剩余时间 {{ countdown }}
                        </template>
                    </a-card-meta>
                </a-card>
            </div>
        </a-layout-content>
    </a-layout>
</template>

<style scoped>
.page-layout {
    height: 100%;
    background: none;
    margin: 0 auto;
}

.page-content {
    height: 100%;
    min-height: 120px;
    line-height: 120px;
}

.gantt-overlay,
.ann-info-overlay {
    position: absolute;
    z-index: 1000;
    bottom: 32px;
}

.gantt-overlay {
    left: 32px;
}

.ann-info-overlay {
    right: 32px;
    max-width: 35%;
    box-shadow: rgba(0, 0, 0, 0.2) 2px 2px 10px 0px;
    border-radius: 8px;
}

:deep(.gantt-container) {
    overflow-y: hidden;
}

@media (prefers-color-scheme: light) {
    :deep(.bar-label) {
        fill: #181a1b;
    }

    :deep(.today-button) {
        background-color: #f3f3f3 !important;
    }

    :deep(.grid-header),
    :deep(.grid-header) * {
        background-color: white;
    }

    :deep(.current-date-highlight) {
        color: #181a1b;
    }

    :deep(.side-header) *,
    :deep(.upper-text) {
        color: #181a1b;
    }

    :deep(.ant-card-body) {
        background-color: white;
    }
}

@media (prefers-color-scheme: dark) {
    :deep(.bar-label) {
        fill: white;
    }

    :deep(.today-button) {
        background-color: #0c0c0c !important;
    }

    :deep(.grid-header),
    :deep(.grid-header) * {
        background-color: #181a1b;
    }

    :deep(.current-date-highlight) {
        color: white;
    }

    :deep(.side-header) *,
    :deep(.upper-text) {
        color: white;
    }

    :deep(.ant-card-body) {
        background-color: #181a1b;
    }

    :deep(.ant-card-body) * {
        color: white;
    }
}
</style>
