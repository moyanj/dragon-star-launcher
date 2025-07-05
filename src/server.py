from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jsonrpcserver import async_dispatch
import uvicorn
from utils import Rest
from contextlib import asynccontextmanager
from env import *  # 所有全局变量
import httpx
import yaml
import tkinter.messagebox
import sys
import core


@asynccontextmanager
async def lifespan(app: FastAPI):
    global VERSION
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/game.yml")
            response.raise_for_status()
            GameConfig.set_conf(yaml.safe_load(response.text))
            response = await client.get(f"{SERVER_URL}/version")
            VERSION = int(response.text.strip())
    except Exception:
        tkinter.messagebox.showerror("错误", "无法连接至服务器")
        sys.exit(1)
    yield


# 初始化FastAPI
app = FastAPI(title="StarGames-Server", lifespan=lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# 404错误
@app.exception_handler(404)
async def error_404(request: Request, exc: HTTPException):
    return Rest("页面不存在", 404)


# 顶级错误处理器
@app.exception_handler(HTTPException)
async def error_500(request: Request, exc: HTTPException):
    return Rest("未知错误", 500, data=str(exc.detail))


@app.get("/")
async def index():
    # 返回主页
    return FileResponse(path=app_dir + "/dist/" + "index.html")


@app.route("/api", methods=["POST"])
async def api(request: Request):
    # 处理JSON-RPC请求
    response = await async_dispatch(await request.body())
    return Response(response)


if not DEBUG:
    app.mount("/", StaticFiles(directory=app_dir + "/dist"), name="static")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=6553, reload=True)
