<script setup lang="ts" async>
import { ElMenu, ElMenuItem, ElButton, ElNotification, ElProgress, ElPopover } from "element-plus";
import { ref, watch, type Ref } from "vue";
import { useGameList, server_url } from "./stores/server";
import { rpc, type DownloadProgress, type GameStatus } from "./rpc";
import { RPCError } from "jsonrpctts";

const game_list = useGameList();
const active = ref();
const status: Ref<GameStatus> = ref({
    "status": "download",
    "local_version_code": null
})
const status_text = ref("开始游戏");
let progressInterval: number | null = null;
const download_progresses: Ref<{ [key: string]: DownloadProgress }> = ref({});

watch(game_list, () => {
    console.log(game_list.value);
    active.value = game_list.value[0].id;
}, {
    once: true,
});

watch(active, async () => {
    status.value = await rpc.call("get_game_status", active.value);
});

watch(status, () => {
    if (status.value.status == "installed") {
        status_text.value = "开始游戏";
    } else if (status.value.status == "installing") {
        status_text.value = "下载中";
    } else if (status.value.status == "download") {
        status_text.value = "下载游戏";
    } else if (status.value.status == "update") {
        status_text.value = "更新游戏";
    }
});

watch(status, async (newStatus) => {
    if (newStatus.status === "installing") {
        // 清除旧的定时器（如果存在）
        if (progressInterval !== null) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        // 启动新的定时器
        await update_progress();
        progressInterval = window.setInterval(async () => {
            await update_progress();
        }, 500); // 每秒更新一次
    } else {
        // 清理定时器
        if (progressInterval !== null) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }
});

function changeMenu(id: string) {
    active.value = id;
}

async function update_progress() {
    download_progresses.value[active.value] = await rpc.call("get_download_progress", active.value);
    console.log(download_progresses.value);
    if (download_progresses.value[active.value].status == "failed") {
        ElNotification({
            title: "错误",
            message: "下载或解压失败：" + download_progresses.value[active.value].error_message,
            type: "error",
        });
        status.value = await rpc.call("get_game_status", active.value);
        if (progressInterval !== null) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        return
    }
    if (download_progresses.value[active.value].status == "unzipping") {
        // 更新解压进度
        const unzipPercentage = download_progresses.value[active.value].unzip_percentage || 0;
        console.log(`解压进度: ${unzipPercentage.toFixed(2)}%`);
    }
    if (download_progresses.value[active.value].percentage >= 100) {
        ElNotification({
            title: "提示",
            message: "游戏下载完成",
            type: "success",
        });
        status.value = await rpc.call("get_game_status", active.value);
        if (progressInterval !== null) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }
}

async function handler() {
    if (status.value.status == "installed") {
        try {
            await rpc.call("start_game", active.value)
            // 游戏启动成功时显示成功提示
            ElNotification({
                title: "提示",
                message: "游戏启动成功",
                type: "success",
            });
        } catch (e) {
            if (e instanceof RPCError) {
                ElNotification({
                    title: "错误",
                    message: e.message,
                    type: "error",
                });
            } else {
                ElNotification({
                    title: "错误",
                    message: "游戏启动失败",
                    type: "error",
                });
            }
        }
    } else if (status.value.status == "download" || status.value.status == "update") {
        ElNotification({
            title: "提示",
            message: "游戏下载开始",
            type: "primary",
        });
        await rpc.call("download_game", active.value)
        download_progresses.value[active.value] = {
            percentage: 0.0,
            total_size: 0,
            downloaded: 0,
            status: "downloading",
            error_message: "",
            unzip_percentage: 0.0
        };
        status.value = await rpc.call("get_game_status", active.value);
    }
}

</script>

<template>

    <div class="menu">
        <el-menu :default-active="active" :collapse="false">
            <el-menu-item v-for="item in game_list" @click="changeMenu(item.id)" :index="item.id"
                :class="{ 'is-active': active === item }">
                <img :src="server_url + '/icon/' + item.id + '.png'" class="icon" />
            </el-menu-item>

            <div class="setting">
                <el-button>
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 1024 1024"
                        class="setting-icon">
                        <path fill="currentColor"
                            d="M600.704 64a32 32 0 0 1 30.464 22.208l35.2 109.376c14.784 7.232 28.928 15.36 42.432 24.512l112.384-24.192a32 32 0 0 1 34.432 15.36L944.32 364.8a32 32 0 0 1-4.032 37.504l-77.12 85.12a357 357 0 0 1 0 49.024l77.12 85.248a32 32 0 0 1 4.032 37.504l-88.704 153.6a32 32 0 0 1-34.432 15.296L708.8 803.904c-13.44 9.088-27.648 17.28-42.368 24.512l-35.264 109.376A32 32 0 0 1 600.704 960H423.296a32 32 0 0 1-30.464-22.208L357.696 828.48a352 352 0 0 1-42.56-24.64l-112.32 24.256a32 32 0 0 1-34.432-15.36L79.68 659.2a32 32 0 0 1 4.032-37.504l77.12-85.248a357 357 0 0 1 0-48.896l-77.12-85.248A32 32 0 0 1 79.68 364.8l88.704-153.6a32 32 0 0 1 34.432-15.296l112.32 24.256c13.568-9.152 27.776-17.408 42.56-24.64l35.2-109.312A32 32 0 0 1 423.232 64H600.64zm-23.424 64H446.72l-36.352 113.088l-24.512 11.968a294 294 0 0 0-34.816 20.096l-22.656 15.36l-116.224-25.088l-65.28 113.152l79.68 88.192l-1.92 27.136a293 293 0 0 0 0 40.192l1.92 27.136l-79.808 88.192l65.344 113.152l116.224-25.024l22.656 15.296a294 294 0 0 0 34.816 20.096l24.512 11.968L446.72 896h130.688l36.48-113.152l24.448-11.904a288 288 0 0 0 34.752-20.096l22.592-15.296l116.288 25.024l65.28-113.152l-79.744-88.192l1.92-27.136a293 293 0 0 0 0-40.256l-1.92-27.136l79.808-88.128l-65.344-113.152l-116.288 24.96l-22.592-15.232a288 288 0 0 0-34.752-20.096l-24.448-11.904L577.344 128zM512 320a192 192 0 1 1 0 384a192 192 0 0 1 0-384m0 64a128 128 0 1 0 0 256a128 128 0 0 0 0-256" />
                    </svg>
                </el-button>
            </div>
        </el-menu>
    </div>
    <div class="content" :style="{ backgroundImage: `url(${server_url}/background/${active}.jpg)` }">
        <div class="start" @click="handler">
            <div class="status">
                <div class="status-ready" v-if="status.status === 'installed'">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 24 24"
                        class="status-icon">
                        <path fill="currentColor"
                            d="M8 17.175V6.825q0-.425.3-.713t.7-.287q.125 0 .263.037t.262.113l8.15 5.175q.225.15.338.375t.112.475t-.112.475t-.338.375l-8.15 5.175q-.125.075-.262.113T9 18.175q-.4 0-.7-.288t-.3-.712" />
                    </svg>
                </div>
                <div class="status-no" v-if="status.status === 'download'">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 24 24">
                        <path fill="currentColor"
                            d="M5 10H4V8h2v1h1v1h1v1h1v1h1V1h2v12h1v-1h1v-1h1v-1h1v-1h1V9h1V8h2v2h-1v1h-1v1h-1v1h-1v1h-1v1h-2v-1h-1v-1H9v-1H8v-1H7v-1H6v-1H5zM2 21h20v2H2z" />
                    </svg>
                </div>
                <div class="status-ing" v-if="status.status === 'installing'">
                    <el-popover placement="top" trigger="hover">
                        <template #reference>
                            <span>{{ String(Math.floor(download_progresses[active]?.percentage || 0)).padStart(2, '0')
                                }}.{{
                                    String(Math.floor(((download_progresses[active]?.percentage || 0) % 1) *
                                        100)).padStart(2, '0') }}%</span>
                        </template>
                        <div v-if="download_progresses[active]?.status === 'unzipping'">
                            <h3>解压中...</h3>
                            <el-progress :percentage="Math.floor(download_progresses[active]?.unzip_percentage || 0)"
                                :show-text="false"></el-progress>
                        </div>
                        <div v-else>
                            <h3>下载中...</h3>
                            <el-progress :percentage="Math.floor(download_progresses[active]?.percentage || 0)"
                                :show-text="false"></el-progress>
                        </div>
                    </el-popover>
                </div>
            </div>
            <span class="text">{{ status_text }}</span>
        </div>
    </div>
</template>

<style scoped>
.content {
    width: calc(100% - 120px);
    background-size: cover;
    background-position: center;
    margin-top: 0px;
    margin-bottom: 0px;
}

.menu {
    width: 100px;
    height: calc(100vh - 10px);
    overflow: overlay;
    margin-right: 5px;
    margin-top: 5px;
}

.menu .el-menu {
    height: 100%;
    width: 100%;
}

.menu .el-menu-item {
    height: calc((100% - 95px) / 9);
}

.menu .el-menu-item.is-active {
    background-color: rgb(33.2, 61.4, 90.5);
}

.icon {
    width: 55px;
    height: 55px;
    border: 1px solid #636466;
    border-radius: 5px;
}

.setting {
    position: fixed;
    width: 20px;
    bottom: 15px;
    left: 30px;
}

.setting>.el-button {
    width: 100%;
}

.setting-icon {
    width: 20px;
    height: 20px;
}

.start {
    position: fixed;
    width: 200px;
    height: 55px;
    bottom: 30px;
    right: 45px;
    background-color: #1864b1;
    border-radius: 7px;
    display: grid;
    place-items: center;
    grid-template-columns: 33% 66%;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
    cursor: pointer;
}

.status {
    width: 100%;
    height: 100%;
    background-color: #636466;
    border-radius: 7px 0 0 7px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.status-icon {
    width: 35px;
    height: 35px;
}

.text {
    width: 100%;
    line-height: 100%;
    text-align: center;
}

.el-progress {
    height: 50px !important;
    width: 50px !important;

}
</style>

<style>
#app {
    display: flex;
}
</style>
