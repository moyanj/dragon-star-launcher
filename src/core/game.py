from jsonrpcserver import method, Success, Error
import os
from env import *
import subprocess
import httpx
import threading

from env import SERVER_URL  # 新增导入，用于后台线程

# 全局变量，用于存储下载进度
download_progress = {
    "percentage": 0.0,
    "total_size": 0,
    "downloaded": 0,
}


@method(name="get_game_status")
async def get_game_staus(name: str):
    if os.path.exists(os.path.join(config.game_path, name, "installed")):  # type: ignore
        return Success("installed")
    if os.path.exists(os.path.join(config.game_path, name, "installing")):  # type: ignore
        return Success("installing")
    return Success("download")


@method(name="start_game")
async def start_game(name: str):
    game_path = os.path.join(config.game_path, name, "start.bat")  # type: ignore
    if os.path.exists(game_path):  # type: ignore
        # 使用 subprocess.Popen 启动游戏进程，设置 shell=True 以支持批处理文件
        subprocess.Popen(game_path, shell=True)
        return Success()
    return Error(message="游戏未安装", code=404)


@method(name="download_game")
async def download_game(name: str):
    global download_progress
    game_url = f"{SERVER_URL}/game_resouse/{name}.zip"  # type: ignore
    print(game_url)
    download_path = os.path.join(config.game_path, name)  # type: ignore
    os.makedirs(download_path, exist_ok=True)

    def download_thread():
        global download_progress
        with open(os.path.join(download_path, "installing"), "w") as f:
            f.write("true")

        try:
            with httpx.Client() as client:  # 使用 Client 并启用默认配置
                with client.stream("GET", game_url) as response:  # 使用 stream 模式
                    total_size = int(response.headers.get("content-length", 0))
                    download_progress["total_size"] = total_size
                    block_size = 1 * 1024 * 1024  # 1 MB
                    progress = 0

                    with open(os.path.join(download_path, f"{name}.zip"), "wb") as f:
                        for data in response.iter_bytes(
                            block_size
                        ):  # 使用 iter_bytes() 获取数据块
                            f.write(data)
                            progress += len(data)
                            download_progress["downloaded"] = progress
                            download_progress["percentage"] = progress / total_size

            # 标记游戏为已安装
            with open(os.path.join(download_path, "installed"), "w") as f:
                f.write("installed")
            download_progress["downloaded"] = total_size
            download_progress["percentage"] = 100.0
            
        except Exception as e:
            print(f"下载失败: {str(e)}")
        finally:
            os.remove(os.path.join(download_path, "installing"))

    # 在后台线程中启动下载
    threading.Thread(target=download_thread, daemon=True).start()
    return Success("下载已开始")


@method(name="get_download_progress")
async def get_download_progress(name: str):
    global download_progress
    return Success(download_progress)
