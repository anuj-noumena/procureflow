<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, Layers3 } from "lucide-vue-next";
import { useSession } from "../lib/session";
import { useAction } from "../lib/api";
const data = reactive({ organization: "", email: "", password: "" }),
  session = useSession(),
  router = useRouter();
const { run, busy, error } = useAction();
function submit() {
  run(async () => {
    await session.signIn(data);
    await router.replace("/");
  });
}
</script>
<template>
  <main class="login">
    <section class="login-card">
      <div class="brand"><Layers3 />ProcureFlow</div>
      <h1>Sign in</h1>
      <p>Access your procurement workspace.</p>
      <form class="form" @submit.prevent="submit">
        <label
          >Workspace slug<input
            v-model="data.organization"
            required
            autocomplete="organization"
            placeholder="Your organization" /></label
        ><label
          >Email<input
            v-model="data.email"
            type="email"
            required
            autocomplete="username" /></label
        ><label
          >Password<input
            v-model="data.password"
            type="password"
            required
            autocomplete="current-password"
        /></label>
        <p role="alert" v-if="error">{{ error }}</p>
        <button class="primary" :disabled="busy">
          {{ busy ? "Signing in…" : "Sign in" }}<ArrowRight />
        </button>
      </form>
    </section>
  </main>
</template>
