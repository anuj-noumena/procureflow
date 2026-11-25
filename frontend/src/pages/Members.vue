<script setup lang="ts">
import { ref, onMounted } from "vue";
import Dialog from "primevue/dialog";
import { Plus } from "lucide-vue-next";
import { api, human, useAction } from "../lib/api";
interface Member {
  id: string;
  name: string;
  email: string;
  role: string;
  active: boolean;
}
const users = ref<Member[]>([]),
  modal = ref(false),
  existing = ref(false),
  password = ref("");
const empty = () => ({
    id: "",
    name: "",
    email: "",
    role: "requester",
    active: true,
  }),
  form = ref(empty());
const roles = [
  "organization_admin",
  "procurement_manager",
  "department_manager",
  "requester",
  "finance_user",
];
const { run, busy, error } = useAction();
async function load() {
  users.value = (await api.get("/members")).data;
}
onMounted(() => run(load));
function edit(m?: Member) {
  form.value = m ? { ...m } : empty();
  password.value = "";
  existing.value = false;
  modal.value = true;
  error.value = "";
}
function save() {
  run(async () => {
    const f = form.value;
    if (f.id)
      await api.put("/members/" + f.id, { role: f.role, active: f.active });
    else if (existing.value)
      await api.post("/members/enroll", { email: f.email, role: f.role });
    else
      await api.post("/members", {
        name: f.name,
        email: f.email,
        role: f.role,
        password: password.value,
      });
    password.value = "";
    modal.value = false;
    await load();
  });
}
</script>
<template>
  <header class="heading">
    <div>
      <small>Administration</small>
      <h1>User management</h1>
    </div>
    <button class="primary" @click="edit()"><Plus />Add member</button>
  </header>
  <p v-if="error && !modal" role="alert">{{ error }}</p>
  <section class="panel scroll">
    <table>
      <thead>
        <tr>
          <th>Member</th>
          <th>Role</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in users" :key="m.id">
          <td>
            <strong>{{ m.name }}</strong
            ><br /><small>{{ m.email }}</small>
          </td>
          <td>{{ human(m.role) }}</td>
          <td>{{ m.active ? "Active" : "Inactive" }}</td>
          <td><button @click="edit(m)">Edit</button></td>
        </tr>
      </tbody>
    </table>
  </section>
  <Dialog
    v-model:visible="modal"
    modal
    :header="form.id ? 'Edit membership' : 'Add member'"
    ><form class="form" @submit.prevent="save">
      <template v-if="!form.id"
        ><label
          >Account<select v-model="existing">
            <option :value="false">Create account</option>
            <option :value="true">Enroll existing account</option>
          </select></label
        ><label>Email<input v-model="form.email" type="email" required /></label
        ><template v-if="!existing"
          ><label>Name<input v-model="form.name" required /></label
          ><label
            >Initial password<input
              v-model="password"
              type="password"
              minlength="12"
              maxlength="128"
              required
              autocomplete="new-password" /></label></template></template
      ><label
        >Role<select v-model="form.role">
          <option v-for="r in roles" :key="r" :value="r">{{ human(r) }}</option>
        </select></label
      ><label v-if="form.id"
        >Membership status<select v-model="form.active">
          <option :value="true">Active</option>
          <option :value="false">Inactive</option>
        </select></label
      >
      <p v-if="error" role="alert">{{ error }}</p>
      <button class="primary" :disabled="busy">Save membership</button>
    </form></Dialog
  >
</template>
