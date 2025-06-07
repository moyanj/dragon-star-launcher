// composables/useGameList.ts
import { ref } from 'vue';

export const server_url = "http://222.186.150.90:13336/";

// 模拟内存缓存（也可以根据需求使用 localStorage）
let cachedGameList: string[] | null = null;

export function useGameList() {
  const game_list = ref<string[]>([]);

  // 包装为 async 内部函数
  (async () => {
    if (cachedGameList) {
      // 缓存存在，直接使用
      game_list.value = cachedGameList;
      return;
    }

    try {
      const response = await fetch(server_url + "game_list");
      if (!response.ok) {
        throw new Error(`HTTP请求失败: 状态码 ${response.status}`);
      }

      const text = await response.text();
      const list = text.split('\n').filter(name => name.trim() !== '');

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
