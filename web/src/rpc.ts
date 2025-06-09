import { RPCClient, type RPCClientConfig } from "jsonrpctts"
import { type Game } from "./stores/server";

export var base_api = "";
if (import.meta.env.DEV) {
    base_api = "http://127.0.0.1:6553";
} else {
    base_api = "";
}

interface RPCFunction {
    "get_game_status": (name: string) => GameStatus;
    "start_game": (name: string) => string;
    "download_game": (name: string) => string;
    "get_download_progress": (n: string) => DownloadProgress;
    "data.server_config": () => Game[];
}

export const rpc = new RPCClient<RPCFunction>({
    "endpoint": base_api + "/api"
})


export type DownloadProgress = {
    percentage: number,
    total_size: number,
    downloaded: number,
    status: string,
    error_message: string
    unzip_percentage: number
}

export type GameStatus = {
    status: string,
    local_version_code: number | null
}