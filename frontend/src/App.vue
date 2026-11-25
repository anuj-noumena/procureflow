<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  Layers3,
  LayoutDashboard,
  FileText,
  Inbox,
  Building2,
  BookOpen,
  Settings,
  Users,
  LogOut,
  Menu,
  ChevronRight,
} from "lucide-vue-next";
import { useSession } from "./lib/session";
import { human } from "./lib/api";
const session = useSession(),
  router = useRouter(),
  route = useRoute(),
  menu = ref(false);
const nav = computed(() =>
  [
    { to: "/", name: "Dashboard", icon: LayoutDashboard, show: true },
    { to: "/requisitions", name: "Requisitions", icon: FileText, show: true },
    {
      to: "/approvals",
      name: "Approvals",
      icon: Inbox,
      show: session.can("approval.decide"),
    },
    { to: "/suppliers", name: "Suppliers", icon: Building2, show: true },
    { to: "/catalog", name: "Catalog", icon: BookOpen, show: true },
    {
      to: "/organization",
      name: "Organization settings",
      icon: Settings,
      show: session.can("organization.manage"),
    },
    {
      to: "/members",
      name: "User management",
      icon: Users,
      show: session.can("organization.manage"),
    },
  ].filter((n) => n.show),
);
function logout() {
  session.logout();
  router.replace("/login");
}
watch(
  () => route.path,
  () => (menu.value = false),
);
onMounted(() => window.addEventListener("pf-expired", logout));
onUnmounted(() => window.removeEventListener("pf-expired", logout));
</script>
<template>
  <RouterView v-if="route.path === '/login'" />
  <div v-else class="layout">
    <aside :class="{ expanded: menu }">
      <div class="brand"><Layers3 />ProcureFlow</div>
      <div class="workspace">
        <span class="orgmark">{{
          session.me?.organization_name.charAt(0)
        }}</span>
        <div>
          <small>Workspace</small
          ><strong>{{ session.me?.organization_name }}</strong>
        </div>
      </div>
      <nav>
        <RouterLink
          v-for="n in nav"
          :key="n.to"
          :to="n.to"
          :class="{
            current: n.to !== '/' && route.path.startsWith(n.to + '/'),
          }"
          ><component :is="n.icon" />{{ n.name }}</RouterLink
        >
      </nav>
      <div class="account">
        <b>{{ session.me?.name.charAt(0) }}</b>
        <div>
          <strong>{{ session.me?.name }}</strong
          ><small>{{ human(session.me?.role || "") }}</small>
        </div>
        <button @click="logout" aria-label="Sign out"><LogOut /></button>
      </div>
    </aside>
    <div class="maincol">
      <header class="topbar">
        <button
          class="menu"
          aria-label="Toggle navigation"
          @click="menu = !menu"
        >
          <Menu /></button
        ><span>Workspace</span><ChevronRight /><strong>{{
          route.meta.title ||
          nav.find((n) => route.path.startsWith(n.to) && n.to !== "/")?.name ||
          "Overview"
        }}</strong>
      </header>
      <main class="content"><RouterView :key="route.fullPath" /></main>
    </div>
  </div>
</template>
