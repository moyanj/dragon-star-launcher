from jsonrpcserver import method, Success, Error
import os
from env import *
import subprocess
import httpx
import threading
import zipfile

from env import SERVER_URL

# 全局变量，用于存储所有游戏的下载进度
download_progresses = {}

@method(name="get_game_status")
async def get_game_staus(name: str):
    if os.path.exists(os.path.join(config.game_path, name, "installed")): # type: ignore
        return Success("installed")
    if os.path.exists(os.path.join(config.game_path, name, "installing")): # type: ignore
        return Success("installing")
    return Success("download")

@method(name="start_game")
async def start_game(name: str):
    game_path = os.path.join(config.game_path, name, "start.bat") # type: ignore
    if os.path.exists(game_path):
        subprocess.Popen(game_path, shell=True)
        return Success()
    return Error(message="游戏未安装", code=404)

@method(name="download_game")
async def download_game(name: str):
    global download_progresses
    if name in download_progresses and download_progresses[name]["status"] == "downloading":
        return Error(message="该游戏正在下载中", code=409)
    
    download_progresses[name] = {
        "percentage": 0.0,
        "total_size": 0,
        "downloaded": 0,
        "status": "downloading",
        "unzip_percentage": 0.0  # 新增解压进度字段
    }
    
    def download_thread():
        download_path = os.path.join(config.game_path, name) # type: ignore
        try:
            game_url = f"{SERVER_URL}/game_resouse/{name}.zip"
            
            os.makedirs(download_path, exist_ok=True)
            
            with open(os.path.join(download_path, "installing"), "w") as f:
                f.write("true")

            with httpx.Client() as client:
                with client.stream("GET", game_url) as response:
                    total_size = int(response.headers.get("content-length", 0))
                    download_progresses[name]["total_size"] = total_size
                    block_size = 1 * 1024 * 1024
                    progress = 0

                    with open(os.path.join(download_path, f"{name}.zip"), "wb") as f:
                        for data in response.iter_bytes(block_size):
                            f.write(data)
                            progress += len(data)
                            download_progresses[name]["downloaded"] = progress
                            download_progresses[name]["percentage"] = (progress / total_size) * 100

            # 解压文件
            zip_file_path = os.path.join(download_path, f"{name}.zip")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                total_files = len(zip_ref.infolist())
                extracted_files = 0
                for file in zip_ref.infolist():
                    zip_ref.extract(file, download_path)
                    extracted_files += 1
                    download_progresses[name]["unzip_percentage"] = (extracted_files / total_files) * 100
                    download_progresses[name]["status"] = "unzipping"  # 更新状态为解压中

            os.remove(zip_file_path)

            # 标记游戏为已安装
            with open(os.path.join(download_path, "installed"), "w") as f:
                f.write("installed")
            download_progresses[name]["downloaded"] = total_size
            download_progresses[name]["percentage"] = 100.0
            download_progresses[name]["status"] = "completed"
            
        except Exception as e:
            print(f"下载或解压失败: {str(e)}")
            download_progresses[name]["status"] = "failed"
            download_progresses[name]["error_message"] = f"下载或解压失败: {str(e)}"
        finally:
            if os.path.exists(os.path.join(download_path, "installing")):
                os.remove(os.path.join(download_path, "installing"))

    threading.Thread(target=download_thread, daemon=True).start()
    return Success("下载已开始")

@method(name="get_download_progress")
async def get_download_progress(name):
    global download_progresses
    if name in download_progresses:
        return Success(download_progresses[name])
    else:
        return Error(message="该游戏没有下载进度信息", code=404)