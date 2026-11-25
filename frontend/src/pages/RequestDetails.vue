<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import Dialog from "primevue/dialog";
import Status from "../components/Status.vue";
import { api, amount, dateLabel, human, useAction } from "../lib/api";
import { useSession } from "../lib/session";
import type { Req, Choice, Organization } from "../lib/requests";
const id = useRoute().params.id as string,
  req = ref<Req>(),
  org = ref<Organization>(),
  approvers = ref<Choice[]>([]),
  approver = ref(""),
  action = ref(""),
  supplier = ref("");
const session = useSession(),
  { busy, error, run } = useAction();
const canEdit = computed(
  () =>
    session.can("requisition.write") &&
    (session.me?.id === req.value?.requester_id ||
      session.can("requisition.manage")),
);
async function load() {
  const [r, o] = await Promise.all([
    api.get<Req>("/requisitions/" + id),
    api.get<Organization>("/organization"),
  ]);
  req.value = r.data;
  org.value = o.data;
  if (r.data.supplier_id)
    supplier.value = (
      await api.get("/suppliers/" + r.data.supplier_id)
    ).data.name;
  if (r.data.status === "draft" && canEdit.value)
    approvers.value = (await api.get<Choice[]>("/approvers")).data.filter(
      (a) => a.id !== r.data.requester_id,
    );
}
onMounted(() => run(load));
function confirmAction() {
  run(async () => {
    const type = action.value;
    action.value = "";
    await api.post("/requisitions/" + id + "/" + type, {
      version: req.value!.version,
      ...(type === "submit" ? { approver_id: approver.value } : {}),
    });
    await load();
  });
}
</script>
<template>
  <p v-if="error" role="alert">
    {{ error }} <button @click="run(load)">Refresh</button>
  </p>
  <p class="empty" v-if="busy && !req">Loading requisition…</p>
  <div v-if="req" class="stack">
    <header class="heading">
      <div>
        <small>{{ req.number }}</small>
        <h1>{{ req.description }}</h1>
      </div>
      <Status :value="req.status" />
    </header>
    <section class="card">
      <h2>Request details</h2>
      <dl class="facts">
        <div>
          <dt>Requester</dt>
          <dd>{{ req.requester_name }}</dd>
        </div>
        <div>
          <dt>Department</dt>
          <dd>
            {{
              org?.departments.find((d) => d.id === req?.department_id)?.name
            }}
          </dd>
        </div>
        <div>
          <dt>Required by</dt>
          <dd>{{ dateLabel(req.required_date) }}</dd>
        </div>
        <div>
          <dt>Supplier</dt>
          <dd>{{ supplier || "Unspecified" }}</dd>
        </div>
        <div>
          <dt>Estimated total</dt>
          <dd>{{ amount(req.estimated_total, req.currency) }}</dd>
        </div>
      </dl>
    </section>
    <section class="panel">
      <div class="sectiontitle"><h2>Line items</h2></div>
      <div class="scroll">
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Quantity / unit</th>
              <th>Unit price</th>
              <th>Tax</th>
              <th>Line total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(l, i) in req.lines" :key="i">
              <td>{{ l.description }}</td>
              <td>{{ l.quantity }} {{ l.unit }}</td>
              <td>{{ l.unit_price }}</td>
              <td>{{ l.tax_percent }}%</td>
              <td>{{ l.line_total }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!req.lines.length" class="empty">No line items yet.</p>
    </section>
    <div class="actions" v-if="canEdit">
      <button
        v-if="['draft', 'pending_approval'].includes(req.status)"
        @click="action = 'cancel'"
      >
        Cancel requisition</button
      ><template v-if="req.status === 'draft'"
        ><RouterLink class="button" :to="'/requisitions/' + id + '/edit'"
          >Edit draft</RouterLink
        ><button
          class="primary"
          :disabled="!req.lines.length"
          @click="action = 'submit'"
        >
          Submit for approval
        </button></template
      >
    </div>
    <section class="card">
      <h2>History</h2>
      <ol class="timeline">
        <li v-for="e in req.history" :key="e.sequence">
          <strong>{{ human(e.event) }}</strong
          ><small
            >{{ e.actor_name }} ·
            {{ new Date(e.created_at).toLocaleString() }}</small
          >
          <p v-if="e.comment">{{ e.comment }}</p>
        </li>
      </ol>
    </section>
  </div>
  <Dialog
    :visible="!!action"
    @update:visible="action = ''"
    modal
    :header="action === 'submit' ? 'Submit requisition' : 'Cancel requisition'"
    ><form class="form" @submit.prevent="confirmAction">
      <template v-if="action === 'submit'"
        ><label
          >Assigned approver<select
            aria-label="Assigned approver"
            v-model="approver"
            required
          >
            <option value="">Choose an approver</option>
            <option v-for="a in approvers" :key="a.id" :value="a.id">
              {{ a.name }}
            </option>
          </select></label
        >
        <p v-if="!approvers.length">
          An eligible colleague must be active in this workspace.
        </p></template
      >
      <p v-else>
        Cancellation closes this requisition and its pending approval.
      </p>
      <div class="actions">
        <button type="button" @click="action = ''">Back</button
        ><button
          class="primary"
          :disabled="busy || (action === 'submit' && !approver)"
        >
          Confirm {{ action === "submit" ? "submission" : "cancellation" }}
        </button>
      </div>
    </form></Dialog
  >
</template>
