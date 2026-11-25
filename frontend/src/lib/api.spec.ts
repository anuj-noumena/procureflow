import { describe, it, expect } from "vitest";
import { AxiosError } from "axios";
import { amount, message, setToken } from "./api";
import { draftPayload, emptyLine } from "./requests";
describe("API boundary", () => {
  it("preserves decimal strings and removes derived fields during draft edits", () => {
    const line = {
      ...emptyLine(),
      quantity: "3.500",
      unit_price: "12.10",
      line_total: "45.84",
      description: " Brackets ",
    };
    const draft = draftPayload({
      description: " Lab ",
      department_id: "d",
      required_date: "2027-02-01",
      supplier_id: null,
      currency: "USD",
      lines: [line],
    });
    expect(draft.description).toBe("Lab");
    expect(draft.lines[0].quantity).toBe("3.500");
    expect(draft.lines[0].unit_price).toBe("12.10");
    expect(draft.lines[0]).not.toHaveProperty("line_total");
  });
  it("formats the server-provided amount without recalculation", () =>
    expect(amount("999999999999.99", "EUR")).toBe("EUR 999,999,999,999.99"));
  it("shows API conflicts and connection failures", () => {
    const error = new AxiosError("Conflict");
    Object.assign(error, {
      response: {
        status: 409,
        data: { error: { message: "Refresh the draft." } },
      },
    });
    expect(message(error)).toBe("Refresh the draft.");
    expect(message(new AxiosError("Offline"))).toContain("Could not reach");
  });
  it("removes the session token on logout", () => {
    setToken("test-session");
    setToken("");
    expect(sessionStorage.getItem("pf-session")).toBeNull();
  });
});
