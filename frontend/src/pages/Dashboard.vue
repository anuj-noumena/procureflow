<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  Plus,
  FileText,
  Clock3,
  Building2,
  ArrowUpRight,
} from "lucide-vue-next";
import { api, useAction, human } from "../lib/api";
import { useSession } from "../lib/session";
import type { Req } from "../lib/requests";
import RequestsTable from "../components/RequestsTable.vue";
const session = useSession(),
  recent = ref<Req[]>([]),
  counts = ref<Record<string, number>>({}),
  suppliers = ref(0),
  total = ref(0),
  ready = ref(false);
const states = [
  "draft",
  "pending_approval",
  "approved",
  "rejected",
  "cancelled",
];
const { run, busy, error } = useAction();
async function load() {
  const [list, s, ...all] = await Promise.all([
    api.get("/requisitions", { params: { size: 6 } }),
    api.get("/suppliers", { params: { size: 1, status: "active" } }),
    ...states.map((status) =>
      api.get("/requisitions", { params: { status, size: 1 } }),
    ),
  ]);
  recent.value = list.data.items;
  total.value = list.data.total;
  suppliers.value = s.data.total;
  counts.value = Object.fromEntries(
    states.map((state, i) => [state, all[i].data.total]),
  );
  ready.value = true;
}
onMounted(() => run(load));
</script>
<template>
  <header class="hero">
    <small>{{ session.me?.organization_name }}</small>
    <h1>Procurement overview</h1>
    <RouterLink
      v-if="session.can('requisition.write')"
      to="/requisitions/new"
      class="button"
      ><Plus />New requisition</RouterLink
    >
  </header>
  <p v-if="error" role="alert">
    {{ error }} <button @click="run(load)">Retry</button>
  </p>
  <p v-if="busy" class="empty">Loading workspace…</p>
  <template v-if="ready"
    ><div class="metrics">
      <div class="metric">
        <FileText /><span>Total requisitions</span><strong>{{ total }}</strong>
      </div>
      <div class="metric">
        <Clock3 /><span>Pending approval</span
        ><strong>{{ counts.pending_approval }}</strong>
      </div>
      <div class="metric">
        <Building2 /><span>Active suppliers</span
        ><strong>{{ suppliers }}</strong>
      </div>
    </div>
    <div class="stack">
      <section class="panel">
        <div class="sectiontitle">
          <h2>Recent requisitions</h2>
          <RouterLink to="/requisitions" class="button"
            >View all<ArrowUpRight
          /></RouterLink>
        </div>
        <RequestsTable v-if="recent.length" :items="recent" />
        <p v-else class="empty">No requisitions yet.</p>
      </section>
      <section class="card">
        <h2>Requisitions by status</h2>
        <div class="distribution" aria-label="Requisition status distribution">
          <span
            v-for="s in states"
            :key="s"
            :class="s"
            :style="{ flexGrow: counts[s] }"
          />
        </div>
        <div class="legend">
          <span v-for="s in states" :key="s"
            ><i :class="s" />{{ human(s) }} <b>{{ counts[s] }}</b></span
          >
        </div>
      </section>
    </div></template
  >
</template>
