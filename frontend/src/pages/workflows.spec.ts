import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { api } from "../lib/api";
import { useSession } from "../lib/session";
import Login from "./Login.vue";
import Directory from "./Directory.vue";
import ApprovalDetails from "./ApprovalDetails.vue";
import RequisitionEditor from "./RequisitionEditor.vue";
const push = vi.hoisted(() => vi.fn());
const route = vi.hoisted(() => ({ params: {} as Record<string, string> }));
vi.mock("vue-router", () => ({
  useRouter: () => ({ push, replace: push }),
  useRoute: () => route,
}));
const stubs = {
  Dialog: { props: ["visible"], template: '<div v-if="visible"><slot/></div>' },
  RouterLink: true,
  Lookup: true,
};
beforeEach(() => {
  setActivePinia(createPinia());
  route.params = {};
  push.mockReset();
});
afterEach(() => vi.restoreAllMocks());
it("requires a valid workspace, email and password", async () => {
  const view = mount(Login);
  const form = view.get("form").element as HTMLFormElement;
  expect(form.checkValidity()).toBe(false);
  const inputs = view.findAll("input");
  for (const [i, v] of [
    "north",
    "buyer@example.test",
    "some-password",
  ].entries())
    await inputs[i].setValue(v);
  expect(form.checkValidity()).toBe(true);
});
it("creates a supplier with the explicitly entered status", async () => {
  vi.spyOn(api, "get").mockResolvedValue({ data: { items: [], total: 0 } });
  const save = vi.spyOn(api, "post").mockResolvedValue({ data: {} });
  useSession().me = {
    id: "m",
    name: "Buyer",
    role: "procurement_manager",
    email: "b@test.example",
    organization_name: "North",
    permissions: ["directory.write"],
  };
  const view = mount(Directory, {
    props: { kind: "suppliers" },
    global: { stubs },
  });
  await flushPromises();
  await view.get("header button").trigger("click");
  const fields = view.findAll("fieldset input");
  await fields[0].setValue("Apex Tools");
  await fields[1].setValue("Tools");
  await view.get("fieldset select").setValue("active");
  await view.get("form").trigger("submit");
  await flushPromises();
  expect(save).toHaveBeenCalledWith("/suppliers", {
    name: "Apex Tools",
    category: "Tools",
    tax_id: null,
    contacts: [],
    addresses: [],
    status: "active",
  });
});
it("creates a draft and navigates to its returned identifier", async () => {
  vi.spyOn(api, "get").mockResolvedValue({
    data: { departments: [{ id: "d", name: "Ops" }], currency: "USD" },
  });
  const save = vi.spyOn(api, "post").mockResolvedValue({ data: { id: "r1" } });
  const view = mount(RequisitionEditor, { global: { stubs } });
  await flushPromises();
  await view.get("input[placeholder]").setValue("Office kit");
  await view.get('input[type="date"]').setValue("2027-04-10");
  await view.get(".subform input").setValue("Notebook");
  await view.get("form").trigger("submit");
  await flushPromises();
  expect(save).toHaveBeenCalledWith(
    "/requisitions",
    expect.objectContaining({
      description: "Office kit",
      lines: [
        expect.objectContaining({
          unit_price: "0.00",
          description: "Notebook",
        }),
      ],
    }),
  );
  expect(push).toHaveBeenCalledWith("/requisitions/r1");
});
it("requires confirmation before deciding an approval", async () => {
  route.params = { id: "a1" };
  const req = {
    id: "r1",
    description: "New desk",
    number: "PR-1",
    estimated_total: "100.00",
    currency: "USD",
    lines: [],
    history: [],
  };
  vi.spyOn(api, "get").mockImplementation(async (path) => ({
    data: path.startsWith("/approvals")
      ? { id: "a1", version: 1, status: "pending", requisition: req }
      : req,
  }));
  const save = vi.spyOn(api, "post").mockResolvedValue({ data: {} });
  const view = mount(ApprovalDetails, { global: { stubs } });
  await flushPromises();
  await view.get("textarea").setValue("Budget confirmed");
  await view
    .findAll("button")
    .find((b) => b.text() === "Approve")!
    .trigger("click");
  expect(save).not.toHaveBeenCalled();
  await view
    .findAll("button")
    .find((b) => b.text() === "Confirm decision")!
    .trigger("click");
  await flushPromises();
  expect(save).toHaveBeenCalledWith("/approvals/a1/decision", {
    version: 1,
    decision: "approved",
    comment: "Budget confirmed",
  });
});
