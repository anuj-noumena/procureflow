<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
defineProps<{ page: number; size: number; total: number }>();
const emit = defineEmits<{ change: [page: number] }>();
</script>
<template>
  <footer class="pager">
    <span
      >{{ total ? (page - 1) * size + 1 : 0 }}–{{
        Math.min(page * size, total)
      }}
      of {{ total }}</span
    >
    <div>
      <button
        aria-label="Previous page"
        :disabled="page <= 1"
        @click="emit('change', page - 1)"
      >
        <ChevronLeft /></button
      ><button
        aria-label="Next page"
        :disabled="page * size >= total"
        @click="emit('change', page + 1)"
      >
        <ChevronRight />
      </button>
    </div>
  </footer>
</template>
