// composables/useGameList.ts
import { ref } from 'vue';
import { rpc } from '@/rpc';

export const server_url = "http://222.186.150.90:13336";

// 模拟内存缓存（也可以根据需求使用 localStorage）
let cachedGameList: Game[] | null = null;


export type Game = {
  id: string;
  name: string;
  description: string;
  version: string;
  version_id: number;
};

export function useGameList() {
  const game_list = ref<Game[]>([]);

  // 包装为 async 内部函数
  (async () => {
    if (cachedGameList) {
      // 缓存存在，直接使用
      game_list.value = cachedGameList;
      return;
    }

    try {
      // @ts-ignore
      const list = await rpc.call("data.server_config");
      console.log(list);

      // 设置内存缓存
      cachedGameList = list;
      game_list.value = list;

    } catch (err) {
      console.error("获取游戏列表失败：", err);
      game_list.value = [];
    }
  })();

  return game_list;
}
