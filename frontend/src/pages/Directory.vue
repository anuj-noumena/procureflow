<script setup lang="ts">
import { computed, ref } from "vue";
import { Plus, Search, ArrowUpRight, Trash2 } from "lucide-vue-next";
import Dialog from "primevue/dialog";
import Status from "../components/Status.vue";
import Pager from "../components/Pager.vue";
import { api, amount, human, useAction } from "../lib/api";
import { useList } from "../lib/list";
import { useSession } from "../lib/session";
const props = defineProps<{ kind: "suppliers" | "catalog" }>();
const supplier = computed(() => props.kind === "suppliers"),
  title = computed(() => (supplier.value ? "Suppliers" : "Catalog"));
interface Entry {
  id: string;
  name: string;
  category: string;
  tax_id?: string | null;
  status: string;
  addresses: string[];
  contacts: { name: string; email: string; phone: string }[];
  kind: string;
  unit: string;
  code: string;
  description: string;
  reference_price: string;
  currency: string;
}
const blank = (): Entry => ({
  id: "",
  name: "",
  category: "",
  tax_id: "",
  status: "draft",
  contacts: [],
  addresses: [],
  kind: "product",
  unit: "each",
  code: "",
  description: "",
  reference_price: "0.00",
  currency: "USD",
});
const form = ref(blank()),
  open = ref(false);
const { page, size, q, filter, sort, data, loading, error, load } =
  useList<Entry>(
    () => "/" + props.kind,
    () => (supplier.value ? "status" : "kind"),
  );
const { run, busy, error: saveError } = useAction();
const session = useSession(),
  writable = computed(() => session.can("directory.write"));
function edit(entry?: Entry) {
  form.value = entry
    ? { ...blank(), ...JSON.parse(JSON.stringify(entry)) }
    : blank();
  saveError.value = "";
  open.value = true;
}
async function save() {
  await run(async () => {
    const f = form.value;
    const payload = supplier.value
      ? {
          name: f.name,
          category: f.category,
          tax_id: f.tax_id || null,
          status: f.status,
          contacts: f.contacts,
          addresses: f.addresses,
        }
      : {
          name: f.name,
          code: f.code,
          category: f.category,
          description: f.description,
          unit: f.unit,
          kind: f.kind,
          reference_price: f.reference_price,
          currency: f.currency,
        };
    if (f.id) await api.put("/" + props.kind + "/" + f.id, payload);
    else await api.post("/" + props.kind, payload);
    open.value = false;
    await load();
  });
}
</script>
<template>
  <header class="heading">
    <div>
      <small>Procurement directory</small>
      <h1>{{ title }}</h1>
    </div>
    <button v-if="writable" class="primary" @click="edit()">
      <Plus />{{ supplier ? "Add supplier" : "Add item" }}
    </button>
  </header>
  <section class="panel">
    <div class="toolbar">
      <label class="search"
        ><Search /><input
          v-model="q"
          type="search"
          :placeholder="'Search ' + title.toLowerCase()"
          aria-label="Search directory"
      /></label>
      <select v-model="filter" aria-label="Filter directory">
        <option value="">All {{ supplier ? "statuses" : "types" }}</option>
        <option
          v-for="s in supplier
            ? ['draft', 'active', 'inactive', 'suspended']
            : ['product', 'service']"
          :key="s"
          :value="s"
        >
          {{ human(s) }}
        </option></select
      ><select v-model="sort" aria-label="Sort directory">
        <option value="newest">Newest first</option>
        <option value="oldest">Oldest first</option>
      </select>
    </div>
    <p v-if="error" role="alert">
      {{ error }} <button @click="load">Retry</button>
    </p>
    <p v-else-if="loading" class="empty">Loading directory…</p>
    <div v-else-if="data.items.length" class="scroll">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>{{ supplier ? "Tax ID" : "Reference price" }}</th>
            <th>{{ supplier ? "Status" : "Type" }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in data.items" :key="e.id">
            <td>
              <strong>{{ e.name }}</strong>
            </td>
            <td>{{ e.category }}</td>
            <td>
              {{
                supplier
                  ? e.tax_id || "—"
                  : amount(e.reference_price, e.currency)
              }}
            </td>
            <td><Status :value="supplier ? e.status : e.kind" /></td>
            <td>
              <button :aria-label="'Open ' + e.name" @click="edit(e)">
                <ArrowUpRight />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="empty">No {{ title.toLowerCase() }} match this view.</p>
    <Pager
      :page="page"
      :size="size"
      :total="data.total"
      @change="page = $event"
    />
  </section>
  <Dialog
    v-model:visible="open"
    modal
    :header="
      (form.id ? (writable ? 'Edit ' : 'View ') : 'Add ') +
      (supplier ? 'supplier' : 'catalog item')
    "
    :style="{ width: '38rem', maxWidth: '94vw' }"
  >
    <form class="form" @submit.prevent="save">
      <fieldset :disabled="!writable || busy">
        <label
          >Name<input
            v-model.trim="form.name"
            required
            maxlength="200" /></label
        ><label>Category<input v-model.trim="form.category" required /></label>
        <template v-if="supplier"
          ><label>Tax ID<input v-model.trim="form.tax_id" /></label
          ><label
            >Status<select aria-label="Status" v-model="form.status">
              <option
                v-for="s in ['draft', 'active', 'inactive', 'suspended']"
                :key="s"
                :value="s"
              >
                {{ human(s) }}
              </option>
            </select></label
          >
          <div class="subhead">
            <h3>Contacts</h3>
            <button
              type="button"
              @click="form.contacts.push({ name: '', email: '', phone: '' })"
            >
              <Plus />Contact
            </button>
          </div>
          <div class="subform" v-for="(c, i) in form.contacts" :key="i">
            <label>Contact name<input v-model="c.name" required /></label
            ><label
              >Email<input type="email" v-model="c.email" required /></label
            ><label>Phone<input v-model="c.phone" /></label
            ><button
              type="button"
              aria-label="Remove contact"
              @click="form.contacts.splice(i, 1)"
            >
              <Trash2 />
            </button>
          </div>
          <div class="subhead">
            <h3>Addresses</h3>
            <button type="button" @click="form.addresses.push('')">
              <Plus />Address
            </button>
          </div>
          <div v-for="(_, i) in form.addresses" :key="i" class="inline">
            <label>Address<input v-model="form.addresses[i]" required /></label
            ><button
              type="button"
              aria-label="Remove address"
              @click="form.addresses.splice(i, 1)"
            >
              <Trash2 />
            </button></div
        ></template>
        <template v-else
          ><label>Item code<input v-model="form.code" required /></label
          ><label
            >Type<select aria-label="Type" v-model="form.kind">
              <option>product</option>
              <option>service</option>
            </select></label
          ><label
            >Standard description<textarea v-model="form.description" /></label
          ><label>Unit<input v-model="form.unit" required /></label
          ><label
            >Reference price<input
              v-model="form.reference_price"
              inputmode="decimal"
              pattern="[0-9]+([.][0-9]{1,2})?"
              required /></label
          ><label
            >Currency<input
              v-model="form.currency"
              pattern="[A-Z]{3}"
              required /></label
        ></template>
      </fieldset>
      <p v-if="saveError" role="alert">{{ saveError }}</p>
      <div class="actions">
        <button type="button" @click="open = false">Close</button
        ><button v-if="writable" class="primary" :disabled="busy">
          Save {{ supplier ? "supplier" : "item" }}
        </button>
      </div>
    </form></Dialog
  >
</template>
