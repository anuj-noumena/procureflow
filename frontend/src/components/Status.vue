<script setup lang="ts">
import { human } from "../lib/api";
defineProps<{ value: string }>();
</script>
<template>
  <span class="status" :class="'status-' + value"
    ><i></i>{{ human(value) }}</span
  >
</template>
