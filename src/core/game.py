from attr import has
from jsonrpcserver import method, Success, Error
import os
from env import *
import subprocess
import httpx
import threading
import xxhash
import zipfile
import shutil

from env import SERVER_URL

# 全局变量，用于存储所有游戏的下载进度
download_progresses = {}


def uninstall_game(name: str):
    game_path = os.path.join(config.game_path, name)  # type: ignore
    installed_files_path = os.path.join(game_path, "installed_files.txt")
    installed_file = os.path.join(game_path, "installed")

    # 检查游戏是否已安装
    if not os.path.exists(installed_file) or not os.path.exists(installed_files_path):
        return False

    try:
        # 读取已安装的文件列表
        with open(installed_files_path, "r") as f:
            installed_files = f.read().splitlines()

        # 删除已安装的文件和目录
        for file in installed_files:
            full_path = os.path.join(game_path, file)
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)

        # 删除安装目录
        shutil.rmtree(game_path)

        return True
    except Exception as e:
        return str(e)


@method(name="start_game")
async def start_game(name: str):
    game_path = os.path.join(config.game_path, name, "start.bat")  # type: ignore
    if os.path.exists(game_path):
        subprocess.Popen(game_path, shell=True)
        return Success()
    return Error(message="游戏未安装", code=404)


@method(name="download_game")
async def download_game(name: str):
    global download_progresses
    if (
        name in download_progresses
        and download_progresses[name]["status"] == "downloading"
    ):
        return Error(message="该游戏正在下载中", code=409)

    download_progresses[name] = {
        "percentage": 0.0,
        "total_size": 0,
        "downloaded": 0,
        "status": "downloading",
        "unzip_percentage": 0.0,  # 新增解压进度字段
    }
    uninstall_game(name)

    def download_thread():
        download_path = os.path.join(config.game_path, name)  # type: ignore
        try:
            game_url = f"{SERVER_URL}/resources/{name}.zip"

            os.makedirs(download_path, exist_ok=True)

            with open(os.path.join(download_path, "installing"), "w") as f:
                f.write("true")

            # 修改: 正确获取并解析game_hash
            game_hash_response = httpx.get(f"{SERVER_URL}/resources/{name}.hash")
            game_hash = game_hash_response.text.strip()  # 确保获取的是纯文本内容

            with httpx.Client() as client:
                with client.stream("GET", game_url) as response:
                    total_size = int(response.headers.get("content-length", 0))
                    download_progresses[name]["total_size"] = total_size
                    block_size = 1 * 1024 * 1024
                    progress = 0
                    hasher = xxhash.xxh128()

                    with open(os.path.join(download_path, f"{name}.zip"), "wb") as f:
                        for data in response.iter_bytes(block_size):
                            f.write(data)
                            hasher.update(data)
                            progress += len(data)
                            download_progresses[name]["downloaded"] = progress
                            download_progresses[name]["percentage"] = (
                                progress / total_size
                            ) * 100

            # 修改: 正确比较文件哈希值
            if hasher.hexdigest() != game_hash:
                download_progresses[name]["status"] = "failed"
                download_progresses[name]["error_message"] = f"文件校验失败，请重新下载"
                return

            # 解压文件
            zip_file_path = os.path.join(download_path, f"{name}.zip")
            installed_files = []  # 创建一个列表来存储解压后的文件
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                total_files = len(zip_ref.infolist())
                extracted_files = 0
                for file in zip_ref.infolist():
                    zip_ref.extract(file, download_path)
                    extracted_files += 1
                    installed_files.append(file.filename)  # 将文件名添加到列表中
                    download_progresses[name]["unzip_percentage"] = (
                        extracted_files / total_files
                    ) * 100
                    download_progresses[name][
                        "status"
                    ] = "unzipping"  # 更新状态为解压中

            os.remove(zip_file_path)

            # 将文件列表写入单独的文件
            installed_files_path = os.path.join(download_path, "installed_files.txt")
            with open(installed_files_path, "w") as f:
                f.write("\n".join(installed_files))

            # 标记游戏为已安装
            with open(os.path.join(download_path, "installed"), "w") as f:
                f.write(GameConfig.dict["version_code"])
            download_progresses[name]["downloaded"] = total_size
            download_progresses[name]["percentage"] = 100.0
            download_progresses[name]["status"] = "completed"

        except Exception as e:
            print(f"下载或解压失败: {str(e)}")
            download_progresses[name]["status"] = "failed"
            download_progresses[name]["error_message"] = f"安装失败: {str(e)}"
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


@method(name="uninstall_game")
async def uninstall_game_method(name: str):
    code = uninstall_game(name)
    if code is False:
        return Error(message="游戏未安装", code=404)
    if code is True:
        return Success(message="游戏已成功卸载")
    if isinstance(code, str):
        return Error(message=code, code=500)


@method(name="get_game_status")
async def get_game_info(name: str):
    if os.path.exists(os.path.join(config.game_path, name, "installed")):  # type: ignore
        return Success(
            {
                "status": "installed",
                "local_version_code": open(os.path.join(config.game_path, name, "installed"), "r", encoding="utf-8").read(),  # type: ignore
            }
        )
    if os.path.exists(os.path.join(config.game_path, name, "installing")):  # type: ignore
        return Success(
            {
                "status": "installing",
            }
        )
    return Success(
        {
            "status": "download",
        }
    )
