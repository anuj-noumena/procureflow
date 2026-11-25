<script setup lang="ts">
import Status from "../components/Status.vue";
import Pager from "../components/Pager.vue";
import { useList } from "../lib/list";
import { amount, dateLabel, human } from "../lib/api";
import type { Req } from "../lib/requests";
interface Approval {
  id: string;
  status: string;
  requisition: Req;
  created_at: string;
}
const { q, page, filter, sort, data, size, error, loading, load } =
  useList<Approval>(
    () => "/approvals",
    () => "status",
  );
filter.value = "pending";
</script>
<template>
  <header class="heading">
    <div>
      <small>Assigned to you</small>
      <h1>Approval inbox</h1>
    </div>
  </header>
  <section class="panel">
    <div class="toolbar">
      <input
        v-model="q"
        type="search"
        aria-label="Search approvals"
        placeholder="Search approvals"
      /><select v-model="filter" aria-label="Approval status">
        <option
          v-for="s in ['pending', 'approved', 'rejected', 'cancelled']"
          :key="s"
          :value="s"
        >
          {{ human(s) }}
        </option></select
      ><select v-model="sort" aria-label="Sort">
        <option value="newest">Newest first</option>
        <option value="oldest">Oldest first</option>
      </select>
    </div>
    <p v-if="error" role="alert">
      {{ error }} <button @click="load">Retry</button>
    </p>
    <p v-else-if="loading" class="empty">Loading approvals…</p>
    <div v-else-if="data.items.length" class="scroll">
      <table>
        <thead>
          <tr>
            <th>Requisition</th>
            <th>Assigned</th>
            <th>Estimated total</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in data.items" :key="a.id">
            <td>
              <RouterLink class="rowlink" :to="'/approvals/' + a.id">{{
                a.requisition.description
              }}</RouterLink
              ><br /><small>{{ a.requisition.number }}</small>
            </td>
            <td>{{ dateLabel(a.created_at) }}</td>
            <td>
              {{
                amount(a.requisition.estimated_total, a.requisition.currency)
              }}
            </td>
            <td><Status :value="a.status" /></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="empty">No {{ filter }} approvals assigned to you.</p>
    <Pager
      :page="page"
      :size="size"
      :total="data.total"
      @change="page = $event"
    />
  </section>
</template>
