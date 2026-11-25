<script setup lang="ts">
import { Plus, Search } from "lucide-vue-next";
import Pager from "../components/Pager.vue";
import RequestsTable from "../components/RequestsTable.vue";
import { human } from "../lib/api";
import { useSession } from "../lib/session";
import { useList } from "../lib/list";
import type { Req } from "../lib/requests";
const session = useSession();
const { q, page, filter, sort, data, size, error, loading, load } =
  useList<Req>(
    () => "/requisitions",
    () => "status",
  );
</script>
<template>
  <header class="heading">
    <div>
      <small>Procurement</small>
      <h1>Requisitions</h1>
    </div>
    <RouterLink
      class="primary button"
      v-if="session.can('requisition.write')"
      to="/requisitions/new"
      ><Plus />New requisition</RouterLink
    >
  </header>
  <section class="panel">
    <div class="toolbar">
      <label class="search"
        ><Search /><input
          v-model="q"
          type="search"
          placeholder="Search requisitions"
          aria-label="Search requisitions" /></label
      ><select v-model="filter" aria-label="Requisition status">
        <option value="">All statuses</option>
        <option
          v-for="s in [
            'draft',
            'pending_approval',
            'approved',
            'rejected',
            'cancelled',
          ]"
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
    <p v-else-if="loading" class="empty">Loading requisitions…</p>
    <RequestsTable v-else-if="data.items.length" :items="data.items" />
    <p v-else class="empty">No requisitions match this view.</p>
    <Pager
      :page="page"
      :size="size"
      :total="data.total"
      @change="page = $event"
    />
  </section>
</template>
