from jsonrpcserver import method, Success, Error
import httpx
from env import *
import subprocess
import sys


@method(name="check_update")
async def check_update():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{SERVER_URL}/version")
        v = int(res.text.strip())

    if v > VERSION:
        return Success(True)
    else:
        return Success(False)


@method(name="update")
async def update():
    subprocess.run(["update.exe"], cwd=app_dir)
    sys.exit()
