<script setup lang="ts">
import { amount, dateLabel } from "../lib/api";
import type { Req } from "../lib/requests";
import Status from "./Status.vue";
defineProps<{ items: Req[] }>();
</script>
<template>
  <div class="scroll">
    <table>
      <thead>
        <tr>
          <th>Requisition</th>
          <th>Required by</th>
          <th>Estimated total</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in items" :key="r.id">
          <td>
            <RouterLink :to="'/requisitions/' + r.id" class="rowlink">{{
              r.description
            }}</RouterLink
            ><br /><small class="muted">{{ r.number }}</small>
          </td>
          <td>{{ dateLabel(r.required_date) }}</td>
          <td>{{ amount(r.estimated_total, r.currency) }}</td>
          <td><Status :value="r.status" /></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
