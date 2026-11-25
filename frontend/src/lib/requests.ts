export interface Line {
  description: string;
  unit: string;
  catalog_item_id: string | null;
  quantity: string;
  unit_price: string;
  tax_percent: string;
  line_total?: string;
}
export interface Req {
  id: string;
  number: string;
  description: string;
  department_id: string;
  supplier_id: string | null;
  requester_id: string;
  requester_name: string;
  required_date: string;
  currency: string;
  estimated_total: string;
  status: string;
  version: number;
  created_at: string;
  modified_at: string;
  lines: Line[];
  history: {
    event: string;
    sequence: number;
    actor_id: string;
    actor_name: string;
    comment: string;
    created_at: string;
  }[];
}
export interface Choice {
  id: string;
  name: string;
}
export interface Organization {
  id: string;
  slug: string;
  name: string;
  currency: string;
  status: string;
  departments: Choice[];
  branches: Choice[];
}
export const emptyLine = (): Line => ({
  description: "",
  unit: "each",
  catalog_item_id: null,
  quantity: "1",
  unit_price: "0.00",
  tax_percent: "0",
});
export function draftPayload(
  r: Pick<
    Req,
    | "description"
    | "department_id"
    | "supplier_id"
    | "required_date"
    | "currency"
    | "lines"
  >,
) {
  return {
    description: r.description.trim(),
    department_id: r.department_id,
    supplier_id: r.supplier_id,
    required_date: r.required_date,
    currency: r.currency,
    lines: r.lines.map((l) => ({
      description: l.description.trim(),
      unit: l.unit,
      quantity: l.quantity,
      unit_price: l.unit_price,
      tax_percent: l.tax_percent,
      catalog_item_id: l.catalog_item_id,
    })),
  };
}
