import { defineStore } from "pinia";
import { ref } from "vue";
import { api, setToken } from "./api";
export interface Me {
  id: string;
  name: string;
  role: string;
  email: string;
  organization_name: string;
  permissions: string[];
}
export const useSession = defineStore("session", () => {
  const me = ref<Me | null>(null);
  async function restore() {
    me.value = (await api.get<Me>("/auth/me")).data;
  }
  async function signIn(data: {
    organization: string;
    email: string;
    password: string;
  }) {
    setToken((await api.post("/auth/login", data)).data.access_token);
    await restore();
  }
  function logout() {
    setToken("");
    me.value = null;
  }
  const can = (permission: string) =>
    !!me.value?.permissions.includes(permission);
  return { me, restore, signIn, logout, can };
});
