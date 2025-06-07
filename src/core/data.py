from jsonrpcserver import method, Result, Success, Error
import os
from env import *


@method(name="data.config")
async def get_config():
    return Success(config.__dict__)


@method(name="data.build_info")
async def get_build_info():
    return Success(build_info)


@method(name="data.update_config")
async def update_config(data: dict, save: bool = True):
    config.update(data)
    if save:
        await config.__save__(os.path.join(dirs.user_config_dir, "config.json"))
    return Success()
