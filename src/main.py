import multiprocessing
import webview
import click
from server import app as flask
from env import *
from tkinter import messagebox
import os
import httpx
import utils
from multiprocessing import Process
import uvicorn


# 渲染器字典
renderer_dict = {
    "edge": "edgechromium",  # Edge WebView2
    "ie": "mshtml",  # Internet Explorer
    "gtk": "gtk",  # WebKit2GTK
    "qt": "qt",  # QTWebEngine
}
port = -1


def has_webview():
    import winreg

    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\EdgeWebView\\BLBeacon", 0, winreg.KEY_READ)  # type: ignore
    except:
        return False
    return True


def install_webview():
    if DEBUG or is_linux:
        return
    if has_webview():
        return
    messagebox.showwarning("警告", "未安装Microsoft Edge WebView2")
    # 是否安装Microsoft Edge WebView2
    if messagebox.askyesno("提示", "是否安装Microsoft Edge WebView2?"):
        req = httpx.get("https://go.microsoft.com/fwlink/p/?LinkId=2124703")
        WebViewDownloadPath = os.path.join(
            dirs.user_cache_dir, "MicrosoftEdgeWebView2.exe"
        )
        with open(WebViewDownloadPath, "wb") as f:
            f.write(req.content)
        os.system(WebViewDownloadPath)

        utils.restart()


def _run_server():
    global port
    uvicorn.run(flask, host="127.0.0.1", port=port)


def run_server(debug):
    global port
    port = utils.get_free_port()
    t = Process(
        target=_run_server,
        name="StarGames-Server",
    )
    t.start()
    return f"http://127.0.0.1:{port}/", t


if is_linux:
    default_renderer = "gtk"
elif "qt" in build_info["args"]:
    default_renderer = "qt"
else:
    default_renderer = "edge"


# 创建WebView窗口
@click.command()
@click.option("--debug", is_flag=True, help="是否开启调试模式")
@click.option("--width", default=1280, help="宽度")
@click.option("--height", default=720, help="高度")
@click.option("--minimized", is_flag=True, help="最小化")
@click.option("--renderer", default=default_renderer, help="Webview渲染器")
def main(debug, width, height, minimized, renderer):
    """主函数

    Arguments:
        略
    """
    # 判断是否为正确的渲染引擎
    if renderer not in renderer_dict.keys():
        messagebox.showerror("错误", "请输入正确的渲染引擎！")
        exit()

    if renderer == "edge":
        install_webview()

    # 判断是否启动服务器
    url, t = run_server(debug)

    window_args = {
        "title": "Star Games",
        "width": width,
        "height": height,
        "minimized": minimized,
        "url": url,
    }

    start_args = {
        "user_agent": "StartGames-WebView/" + build_info["version"],
        "gui": renderer_dict[renderer],
        "storage_path": os.path.join(dirs.user_data_dir, "Web"),
    }

    # 以Debug模式启动
    if debug:
        window_args.update(
            {
                "title": "Star Games - Debug",
                "text_select": True,
                "url": "http://localhost:5173/",
            }
        )
        start_args.update({"icon": os.path.join(app_dir, "..", "images", "icon.png")})
    else:
        start_args.update({"icon": os.path.join(app_dir, "dist", "icon.png")})

    webview.create_window(**window_args)
    webview.start(**start_args)  #  type: ignore 启动WebView

    # 强制结束服务器
    t.terminate()
    t.join()


if __name__ == "__main__":
    if not is_linux:
        multiprocessing.freeze_support()  # 修复Windows下打包后的问题
    main()
