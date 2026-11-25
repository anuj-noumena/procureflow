import { createRouter, createWebHistory } from "vue-router";
import { useSession } from "./lib/session";
import Directory from "./pages/Directory.vue";
import Login from "./pages/Login.vue";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/requisitions",
      component: () => import("./pages/Requisitions.vue"),
    },
    {
      path: "/requisitions/new",
      component: () => import("./pages/RequisitionEditor.vue"),
      meta: { permission: "requisition.write" },
    },
    {
      path: "/requisitions/:id/edit",
      component: () => import("./pages/RequisitionEditor.vue"),
      meta: { permission: "requisition.write" },
    },
    {
      path: "/requisitions/:id",
      component: () => import("./pages/RequestDetails.vue"),
    },
    { path: "/login", component: Login },
    {
      path: "/",
      component: () => import("./pages/Dashboard.vue"),
      meta: { title: "Dashboard" },
    },
    {
      path: "/approvals",
      component: () => import("./pages/Approvals.vue"),
      meta: { permission: "approval.decide" },
    },
    {
      path: "/approvals/:id",
      component: () => import("./pages/ApprovalDetails.vue"),
      meta: { permission: "approval.decide" },
    },
    {
      path: "/organization",
      component: () => import("./pages/Settings.vue"),
      meta: { permission: "organization.manage" },
    },
    {
      path: "/members",
      component: () => import("./pages/Members.vue"),
      meta: { permission: "organization.manage" },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },

    { path: "/suppliers", component: Directory, props: { kind: "suppliers" } },
    { path: "/catalog", component: Directory, props: { kind: "catalog" } },
  ],
});
router.beforeEach(async (to) => {
  const session = useSession();
  if (to.path === "/login") return true;
  if (!session.me) {
    if (!sessionStorage.getItem("pf-session")) return "/login";
    try {
      await session.restore();
    } catch {
      return "/login";
    }
  }
  if (to.meta.permission && !session.can(String(to.meta.permission)))
    return "/";
});
export default router;
