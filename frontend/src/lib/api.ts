import axios from "axios";
import { ref } from "vue";
export const api = axios.create({ baseURL: "/api/v1", timeout: 15000 });
let token = sessionStorage.getItem("pf-session") || "";
export function setToken(value: string) {
  token = value;
  if (value) sessionStorage.setItem("pf-session", value);
  else sessionStorage.removeItem("pf-session");
}
api.interceptors.request.use((config) => {
  if (token) config.headers.Authorization = "Bearer " + token;
  return config;
});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      token &&
      !error.config?.url?.includes("/auth/login")
    ) {
      setToken("");
      window.dispatchEvent(new Event("pf-expired"));
    }
    return Promise.reject(error);
  },
);
export function message(error: unknown): string {
  if (axios.isAxiosError(error))
    return (
      error.response?.data?.error?.message ||
      "Could not reach the workspace. Please try again."
    );
  return error instanceof Error ? error.message : "The operation failed.";
}
export function useAction() {
  const busy = ref(false),
    error = ref("");
  async function run(action: () => Promise<void>) {
    if (busy.value) return;
    busy.value = true;
    error.value = "";
    try {
      await action();
    } catch (e) {
      error.value = message(e);
    } finally {
      busy.value = false;
    }
  }
  return { busy, error, run };
}
export interface Page<T> {
  items: T[];
  total: number;
}
export const human = (value: string) =>
  value.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
export const dateLabel = (value: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value.length === 10 ? value + "T12:00:00" : value));
export function amount(value: string, currency: string) {
  const [whole, fraction = "00"] = value.split(".");
  return (
    currency +
    " " +
    whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",") +
    "." +
    fraction.padEnd(2, "0")
  );
}
