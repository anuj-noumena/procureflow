import { ref, watch, shallowRef } from "vue";
import { api, message, type Page } from "./api";
export function useList<T>(path: () => string, filterName: () => string) {
  const page = ref(1),
    q = ref(""),
    filter = ref(""),
    sort = ref("newest"),
    size = 12;
  const data = shallowRef<Page<T>>({ items: [], total: 0 }),
    loading = ref(false),
    error = ref("");
  let serial = 0;
  async function load() {
    const sequence = ++serial;
    loading.value = true;
    error.value = "";
    try {
      const result = await api.get<Page<T>>(path(), {
        params: {
          page: page.value,
          size,
          q: q.value,
          sort: sort.value,
          [filterName()]: filter.value || undefined,
        },
      });
      if (sequence === serial) data.value = result.data;
    } catch (e) {
      if (sequence === serial) error.value = message(e);
    } finally {
      if (sequence === serial) loading.value = false;
    }
  }
  watch(
    [q, filter, sort],
    () => {
      page.value = 1;
    },
    { flush: "sync" },
  );
  watch([page, q, filter, sort, path], load, { immediate: true });
  return { page, q, filter, sort, size, data, loading, error, load };
}
