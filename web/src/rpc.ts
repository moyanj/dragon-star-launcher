import { RPCClient, type RPCClientConfig } from "jsonrpctts"

export var base_api = "";
if (import.meta.env.DEV) {
    base_api = "http://127.0.0.1:6553";
} else {
    base_api = "";
}

interface RPCFunction {
    "get_game_status": (name: string) => string;
    "start_game": (name: string) => string;
    "requests.req": (method: string, url: string, params?: object, headers?: object) => Response;
}

export const rpc = new RPCClient<RPCFunction>({
    "endpoint": base_api + "/api"
})