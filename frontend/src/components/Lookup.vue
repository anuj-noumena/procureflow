<script setup lang="ts">
import { ref, watch } from "vue";
import { api, message } from "../lib/api";
interface Option {
  id: string;
  name: string;
  unit?: string;
  description?: string;
  currency?: string;
  reference_price?: string;
}
const props = defineProps<{
  path: string;
  modelValue: string | null;
  label: string;
}>();
const emit = defineEmits<{
  "update:modelValue": [id: string | null];
  pick: [option: Option];
}>();
const q = ref(""),
  items = ref<Option[]>([]),
  chosen = ref(""),
  error = ref(""),
  opened = ref(false),
  total = ref(0),
  busy = ref(false);
let serial = 0;
async function search() {
  const current = ++serial;
  busy.value = true;
  error.value = "";
  try {
    const r = await api.get(props.path, {
      params: {
        q: q.value,
        size: 10,
        status: props.path === "/suppliers" ? "active" : undefined,
      },
    });
    if (current === serial) {
      items.value = r.data.items;
      total.value = r.data.total;
    }
  } catch (e) {
    if (current === serial) error.value = message(e);
  } finally {
    if (current === serial) busy.value = false;
  }
}
watch(q, search);
watch(
  () => props.modelValue,
  async (id) => {
    if (!id) {
      chosen.value = "";
      return;
    }
    try {
      const r = await api.get(props.path + "/" + id);
      if (props.modelValue === id) chosen.value = r.data.name;
    } catch (e) {
      error.value = message(e);
    }
  },
  { immediate: true },
);
function choose(o: Option) {
  emit("update:modelValue", o.id);
  emit("pick", o);
  chosen.value = o.name;
  opened.value = false;
  q.value = "";
}
</script>
<template>
  <div class="stack">
    <label
      >{{ label
      }}<button
        type="button"
        @click="
          opened = !opened;
          if (opened) search();
        "
      >
        {{ chosen || "Choose " + label.toLowerCase() }}
      </button></label
    >
    <div v-if="opened" class="subform">
      <input
        v-model="q"
        :aria-label="'Search ' + label"
        placeholder="Search by name"
      /><span v-if="busy">Searching…</span
      ><button v-for="o in items" :key="o.id" type="button" @click="choose(o)">
        {{ o.name }}</button
      ><small v-if="!busy"
        >{{ items.length }} of {{ total }} matches. Refine your search as
        needed.</small
      ><button
        type="button"
        @click="
          emit('update:modelValue', null);
          opened = false;
        "
      >
        Clear selection
      </button>
    </div>
    <p v-if="error" role="alert">{{ error }}</p>
  </div>
</template>
