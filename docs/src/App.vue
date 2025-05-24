<script setup>
import Footer from './components/Footer.vue'
import { reactive, ref, computed, watchEffect, watch } from "vue"

const games = ref([])
const data = reactive({})
const today_events = ref([])

/** 动态导入 JSON 文件 */
const loadData = async () => {
    try {
        const game_list_re = await fetch('/source/game_list.json')
        games.value = await game_list_re.json()
        games.value.forEach(async (game) => {
            console.log(game)
            const game_data_re = await fetch(`/source/${game}.json`)
            data[game] = await game_data_re.json()
        })
        console.log(data)
    } catch (error) {
        console.log(error)
    }
}
// 监听路由参数变化并重新加载数据
watchEffect(loadData)

const value = ref();
const onPanelChange = (value, mode) => {
    console.log(value, mode)
}
const onSelect = (date, info) => {
    const formattedDate = date.format('YYYY-MM-DD')
    console.log(formattedDate)

    // console.log(date, info)
}
</script>

<template>
    <a-layout class="page-layout">
        <a-layout-content class="page-content">
            <!-- 日历 -->
            <a-calendar v-model:value="value" @panelChange="onPanelChange" @select="onSelect" />
            <!-- 事件列表 -->
            <a-list item-layout="horizontal" :data-source="today_events">
                <template #renderItem="{ item }">
                    <a-list-item>
                        <a-list-item-meta
                            description="Ant Design, a design language for background applications, is refined by Ant UED Team">
                            <template #title>
                                <a href="https://www.antdv.com/">{{ item.title }}</a>
                            </template>
                            <template #avatar>
                                <a-avatar src="https://joeschmoe.io/api/v1/random" />
                            </template>
                        </a-list-item-meta>
                    </a-list-item>
                </template>
            </a-list>
        </a-layout-content>
        <!-- Footer -->
        <a-layout-footer class="page-footer">
            <Footer></Footer>
        </a-layout-footer>
    </a-layout>
</template>

<style scoped>
.page-layout {
    height: 100%;
    background: none;
    max-width: 1280px;
    margin: 0 auto;
}

.page-content {
    height: 100%;
    min-height: 120;
    line-height: 120px;
}

.page-footer {
    background-color: transparent;
}
</style>
