<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Plus, Trash2 } from "lucide-vue-next";
import Lookup from "../components/Lookup.vue";
import { api, useAction } from "../lib/api";
import {
  draftPayload,
  emptyLine,
  type Line,
  type Req,
  type Organization,
} from "../lib/requests";
const route = useRoute(),
  router = useRouter(),
  id = route.params.id as string | undefined;
const org = ref<Organization>(),
  version = ref(1);
const form = ref({
  description: "",
  department_id: "",
  supplier_id: null as string | null,
  required_date: "",
  currency: "USD",
  lines: [emptyLine()],
});
const { busy, error, run } = useAction();
onMounted(() =>
  run(async () => {
    const result = await api.get<Organization>("/organization");
    org.value = result.data;
    form.value.department_id = result.data.departments[0]?.id || "";
    form.value.currency = result.data.currency;
    if (id) {
      const r = (await api.get<Req>("/requisitions/" + id)).data;
      form.value = draftPayload(r);
      version.value = r.version;
    }
  }),
);
function save() {
  run(async () => {
    const payload = draftPayload(form.value);
    const response = id
      ? await api.put("/requisitions/" + id, {
          ...payload,
          version: version.value,
        })
      : await api.post("/requisitions", payload);
    await router.push("/requisitions/" + response.data.id);
  });
}
function pick(
  line: Line,
  o: {
    name: string;
    description?: string;
    unit?: string;
    currency?: string;
    reference_price?: string;
  },
) {
  line.description = o.description || o.name;
  line.unit = o.unit || "each";
  line.unit_price =
    o.currency === form.value.currency ? o.reference_price || "0.00" : "";
}
</script>
<template>
  <header class="heading">
    <div>
      <small>Requisitions</small>
      <h1>{{ id ? "Edit draft" : "New requisition" }}</h1>
    </div>
  </header>
  <p v-if="error" role="alert">{{ error }}</p>
  <form class="form" @submit.prevent="save">
    <section class="card form">
      <h2>Request details</h2>
      <label
        >Description<input
          v-model.trim="form.description"
          required
          maxlength="200"
          placeholder="What are you requesting?"
      /></label>
      <div class="grid2">
        <label
          >Department<select v-model="form.department_id" required>
            <option v-for="d in org?.departments" :key="d.id" :value="d.id">
              {{ d.name }}
            </option>
          </select></label
        ><label
          >Required date<input
            v-model="form.required_date"
            type="date"
            required /></label
        ><label
          >Currency<input
            v-model="form.currency"
            pattern="[A-Z]{3}"
            maxlength="3"
            required /></label
        ><Lookup
          path="/suppliers"
          label="Supplier (optional)"
          v-model="form.supplier_id"
        />
      </div>
    </section>
    <section class="card form">
      <div class="subhead">
        <h2>Line items</h2>
        <button type="button" @click="form.lines.push(emptyLine())">
          <Plus />Add line
        </button>
      </div>
      <div class="subform" v-for="(l, i) in form.lines" :key="i">
        <div class="subhead">
          <strong>Line {{ i + 1 }}</strong
          ><button
            type="button"
            :aria-label="'Remove line ' + (i + 1)"
            @click="form.lines.splice(i, 1)"
          >
            <Trash2 />
          </button>
        </div>
        <Lookup
          label="Catalog item (optional)"
          path="/catalog"
          v-model="l.catalog_item_id"
          @pick="pick(l, $event)"
        /><label
          >Line description<input v-model.trim="l.description" required
        /></label>
        <div class="linegrid">
          <label
            >Quantity<input
              v-model="l.quantity"
              inputmode="decimal"
              pattern="[0-9]+([.][0-9]{1,3})?"
              required /></label
          ><label>Unit<input v-model.trim="l.unit" required /></label
          ><label
            >Unit price<input
              v-model="l.unit_price"
              inputmode="decimal"
              pattern="[0-9]+([.][0-9]{1,2})?"
              required /></label
          ><label
            >Tax (%)<input
              v-model="l.tax_percent"
              inputmode="decimal"
              pattern="[0-9]+([.][0-9]{1,2})?"
              required
          /></label>
        </div>
      </div>
    </section>
    <div class="actions">
      <RouterLink class="button" to="/requisitions">Back to list</RouterLink
      ><button class="primary" :disabled="busy || !org">Save draft</button>
    </div>
  </form>
</template>
