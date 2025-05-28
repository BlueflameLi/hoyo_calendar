<script setup>
import Footer from './components/Footer.vue'
import { reactive, ref, computed, watchEffect, watch, onMounted, onUnmounted } from "vue"
import Gantt from 'frappe-gantt'

const pageContentHeight = ref('auto')
let gantt = null
const updateContentHeight = () => {
    const content_element = document.querySelector('.page-content')
    pageContentHeight.value = content_element.clientHeight
    if (gantt) {
        gantt.update_options({ container_height: pageContentHeight.value, })
    }
}


/** 动态导入 JSON 文件 */
const loadData = async () => {
    try {
        // 动态导入 JSON 文件


        // 创建 Gantt 实例
        let tasks = [
            {
                id: '1',
                name: 'Redesign website',
                start: '2025-5-27',
                end: '2025-8-29',
                progress: 40
            }
        ]
        gantt = new Gantt("#gantt", tasks, {
            language: "zh",
            readonly: true,
            container_height: pageContentHeight.value,
            infinite_padding: false,
        });
    } catch (error) {
        console.log(error)
    }
}

// 监听路由参数变化并重新加载数据
onMounted(async () => {
    updateContentHeight()
    loadData()
    window.addEventListener('resize', updateContentHeight)
})
onUnmounted(() => {
    window.removeEventListener('resize', updateContentHeight)
})

</script>

<template>
    <a-layout class="page-layout">
        <a-layout-content class="page-content">
            <!-- 甘特图 -->
            <div id="gantt"></div>
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
    margin: 0 auto;
}

.page-content {
    height: 100%;
    min-height: 120px;
    line-height: 120px;
}

/* #gantt {
    width: 100%;
}

:deep(.grid-header),
:deep(.grid-background) {
    width: 100% !important;
} */

.page-footer {
    background-color: transparent;
}
</style>
