export type Category = { id: number; name: string };
export type Product = {
  id: number;
  name: string;
  category_id: number | null;
  category_status?: "pending" | "running" | "retry" | "failed" | "not_found" | "done";
  reviewed: boolean;
  brand?: string;
  pack_size?: string;
  kind?: "unknown" | "fixed" | "variable_weight";
  image_url?: string;
  source_url?: string;
  confirmation?: "" | "automatic" | "manual";
  manual_fields?: string[];
  search_status?:
    | "idle"
    | "pending"
    | "running"
    | "retry"
    | "failed"
    | "not_found"
    | "matched";
  search_error?: string;
};
export type Alias = {
  id: number;
  label: string;
  retailer: string;
  product_id: number;
};
export type Receipt = {
  id: number;
  filename: string;
  retailer: string;
  store: string;
  date: string | null;
  document: string | null;
  status: "imported" | "failed";
  error: string | null;
  total_cents: number;
  voucher_cents: number;
  paid_cents: number;
  line_count: number;
  payments: { label: string; cents: number }[];
};
export type Purchase = {
  id: number;
  receipt_id: number;
  alias_id: number;
  position: number;
  gross_cents: number;
  discount_cents: number;
  price_verified: boolean;
  discount_label: string;
};
export type State = {
  receipts: Receipt[];
  products: Product[];
  aliases: Alias[];
  categories: Category[];
  purchases: Purchase[];
};
export type EnrichedPurchase = Purchase & {
  product: Product;
  receipt: Receipt;
  label: string;
};
