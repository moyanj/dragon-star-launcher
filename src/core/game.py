from jsonrpcserver import method, Result, Success, Error
import os
from env import *
import subprocess  # 新增导入，用于启动游戏进程


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
    return Error("游戏未安装")
