import { RPCClient, type RPCClientConfig } from "jsonrpctts"

export var base_api = "";
if (import.meta.env.DEV) {
    base_api = "http://127.0.0.1:6553";
} else {
    base_api = "";
}

interface RPCFunction {
    "requests.get": (url: string, params?: object, headers?: object) => Response;
    "requests.post": (url: string, params?: object, headers?: object) => Response;
    "requests.req": (method: string, url: string, params?: object, headers?: object) => Response;
}

const rpc = new RPCClient<RPCFunction>({
    "endpoint": base_api
})