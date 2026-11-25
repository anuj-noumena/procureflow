<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, useAction } from "../lib/api";
import type { Organization } from "../lib/requests";
import { useSession } from "../lib/session";
const org = ref<Organization>(),
  branch = ref(""),
  dept = ref(""),
  notice = ref(""),
  session = useSession();
const { run, busy, error } = useAction();
async function load() {
  org.value = (await api.get("/organization")).data;
}
onMounted(() => run(load));
function save() {
  run(async () => {
    const { name, currency, status } = org.value!;
    await api.put("/organization", { name, currency, status });
    await session.restore();
    notice.value = "Organization settings saved.";
  });
}
function add(kind: "branches" | "departments") {
  run(async () => {
    await api.post("/organization/" + kind, {
      name: kind === "branches" ? branch.value : dept.value,
    });
    branch.value = "";
    dept.value = "";
    await load();
    notice.value = "Directory updated.";
  });
}
</script>
<template>
  <header class="heading">
    <div>
      <small>Administration</small>
      <h1>Organization settings</h1>
    </div>
  </header>
  <p v-if="error" role="alert">{{ error }}</p>
  <p v-if="notice" role="status">{{ notice }}</p>
  <div v-if="org" class="stack">
    <form class="card form" @submit.prevent="save">
      <h2>Workspace profile</h2>
      <label>Organization name<input v-model="org.name" required /></label>
      <div class="grid2">
        <label
          >Default currency<input
            v-model="org.currency"
            pattern="[A-Z]{3}"
            required /></label
        ><label
          >Workspace status<select v-model="org.status">
            <option>active</option>
            <option>paused</option>
          </select></label
        >
      </div>
      <p v-if="org.status === 'paused'">
        Pausing restricts workspace access until an administrator reactivates it
        here.
      </p>
      <div class="actions">
        <button class="primary" :disabled="busy">Save settings</button>
      </div>
    </form>
    <div class="grid2">
      <section
        v-for="kind in ['departments', 'branches'] as const"
        :key="kind"
        class="card"
      >
        <h2>{{ kind === "branches" ? "Branches" : "Departments" }}</h2>
        <ul>
          <li v-for="u in org[kind]" :key="u.id">{{ u.name }}</li>
        </ul>
        <form class="inline form" @submit.prevent="add(kind)">
          <label v-if="kind === 'branches'"
            >Branch name<input v-model="branch" required /></label
          ><label v-else>Department name<input v-model="dept" required /></label
          ><button :disabled="busy">Add</button>
        </form>
      </section>
    </div>
  </div>
</template>
