<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import Dialog from "primevue/dialog";
import Status from "../components/Status.vue";
import { api, amount, human, useAction } from "../lib/api";
import type { Req } from "../lib/requests";
const id = useRoute().params.id as string;
interface Review {
  id: string;
  requisition: Req;
  status: string;
  version: number;
  comment: string;
  decided_at: string | null;
}
const a = ref<Review>(),
  req = ref<Req>(),
  decision = ref(""),
  comment = ref("");
const { busy, error, run } = useAction();
async function load() {
  a.value = (await api.get<Review>("/approvals/" + id)).data;
  req.value = (
    await api.get<Req>("/requisitions/" + a.value.requisition.id)
  ).data;
}
onMounted(() => run(load));
function confirm() {
  run(async () => {
    const selected = decision.value;
    decision.value = "";
    await api.post("/approvals/" + id + "/decision", {
      version: a.value!.version,
      decision: selected,
      comment: comment.value,
    });
    await load();
  });
}
</script>
<template>
  <p v-if="error" role="alert">
    {{ error }} <button @click="run(load)">Refresh</button>
  </p>
  <p v-if="busy && !a" class="empty">Loading review…</p>
  <div v-if="a && req" class="stack">
    <header class="heading">
      <div>
        <small>Approval review · {{ req.number }}</small>
        <h1>{{ req.description }}</h1>
      </div>
      <Status :value="a.status" />
    </header>
    <section class="card">
      <h2>Requisition summary</h2>
      <dl class="facts">
        <div>
          <dt>Requester</dt>
          <dd>{{ req.requester_name }}</dd>
        </div>
        <div>
          <dt>Estimated total</dt>
          <dd>{{ amount(req.estimated_total, req.currency) }}</dd>
        </div>
        <div>
          <dt>Line items</dt>
          <dd>{{ req.lines.length }}</dd>
        </div>
        <div>
          <dt>Required by</dt>
          <dd>{{ req.required_date }}</dd>
        </div>
      </dl>
      <RouterLink :to="'/requisitions/' + req.id"
        >View full requisition</RouterLink
      >
    </section>
    <section v-if="a.status === 'pending'" class="card form">
      <h2>Your decision</h2>
      <label
        >Review comment<textarea
          v-model.trim="comment"
          maxlength="2000"
          placeholder="Required when rejecting a request"
        />
      </label>
      <div class="actions">
        <button :disabled="busy || !comment" @click="decision = 'rejected'">
          Reject</button
        ><button
          class="primary"
          :disabled="busy"
          @click="decision = 'approved'"
        >
          Approve
        </button>
      </div>
    </section>
    <section class="card">
      <h2>Decision history</h2>
      <ol class="timeline">
        <li
          v-for="e in req.history.filter(
            (h) => !['edited', 'created'].includes(h.event),
          )"
          :key="e.sequence"
        >
          <strong>{{ human(e.event) }}</strong
          ><small
            >{{ e.actor_name }} ·
            {{ new Date(e.created_at).toLocaleString() }}</small
          >
          <p>{{ e.comment }}</p>
        </li>
      </ol>
    </section>
  </div>
  <Dialog
    :visible="!!decision"
    @update:visible="decision = ''"
    :header="
      decision === 'approved' ? 'Approve requisition?' : 'Reject requisition?'
    "
    modal
    ><p>This records your final decision for {{ req?.number }}.</p>
    <div class="actions">
      <button @click="decision = ''">Back</button
      ><button class="primary" :disabled="busy" @click="confirm">
        Confirm decision
      </button>
    </div></Dialog
  >
</template>
