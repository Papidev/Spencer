import { afterAll, afterEach, beforeAll, expect, test } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { useProducts } from "./useProducts";
import { useSpending } from "./store";

const server = setupServer(
  http.get("*/api/state", () =>
    HttpResponse.json({
      receipts: [
        { id: 1, date: "2026-10-25", status: "imported" },
        { id: 2, date: "2026-11-08", status: "imported" },
      ],
      categories: [],
      products: [
        { id: 1, name: "Latte", category_id: null, reviewed: true, kind: "fixed" },
        { id: 2, name: "Altro", category_id: null, reviewed: true },
      ],
      aliases: [
        { id: 1, label: "LATTE", product_id: 1 },
        { id: 2, label: "ALTRO", product_id: 2 },
      ],
      purchases: [
        {
          id: 1,
          receipt_id: 1,
          alias_id: 1,
          gross_cents: 201,
          discount_cents: 0,
          price_verified: true,
        },
        {
          id: 2,
          receipt_id: 1,
          alias_id: 1,
          gross_cents: 201,
          discount_cents: 0,
          price_verified: true,
        },
        {
          id: 3,
          receipt_id: 2,
          alias_id: 1,
          gross_cents: 201,
          discount_cents: 42,
          price_verified: true,
        },
        {
          id: 4,
          receipt_id: 1,
          alias_id: 2,
          gross_cents: 2000,
          discount_cents: 0,
          price_verified: true,
        },
      ],
    }),
  ),
);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

test("recurring products rank by visits, not repeated lines or spending", async () => {
  await useSpending().reload();
  const products = useProducts();
  expect(products.rows.value[0].name).toBe("Altro");
  products.order.value = "visits";
  expect(products.rows.value[0].name).toBe("Latte");
  expect(products.rows.value[0].visits).toBe(2);
});

test("price history groups repeat lines and preserves discount effects", async () => {
  await useSpending().reload();
  const products = useProducts();
  products.selected.value = 1;
  expect(
    products.history.value.map((entry) => entry.net / entry.count),
  ).toEqual([201, 159]);
  expect(
    products.history.value.map((entry) => entry.gross / entry.count),
  ).toEqual([201, 201]);
  expect(products.history.value.map((entry) => entry.promotional)).toEqual([
    false,
    true,
  ]);
  expect(products.option.value.series).toHaveLength(1);
});

test("full-price and promotional purchases on the same receipt stay separate", async () => {
  server.use(
    http.get("*/api/state", () =>
      HttpResponse.json({
        receipts: [{ id: 1, date: "2026-11-08", status: "imported" }],
        categories: [],
        products: [{ id: 1, name: "Latte", category_id: null, reviewed: true, kind: "fixed" }],
        aliases: [{ id: 1, label: "LATTE", product_id: 1 }],
        purchases: [
          {
            id: 1,
            receipt_id: 1,
            alias_id: 1,
            gross_cents: 200,
            discount_cents: 0,
            price_verified: true,
          },
          {
            id: 2,
            receipt_id: 1,
            alias_id: 1,
            gross_cents: 200,
            discount_cents: 50,
            price_verified: true,
          },
        ],
      }),
    ),
  );
  await useSpending().reload();
  const products = useProducts();
  products.selected.value = 1;
  expect(
    products.history.value.map((entry) => ({
      promotional: entry.promotional,
      price: entry.net / entry.count,
    })),
  ).toEqual([
    { promotional: false, price: 200 },
    { promotional: true, price: 150 },
  ]);
  expect(products.rows.value[0].visits).toBe(1);
});

test("receipt descriptions remain searchable after the recognized name changes", async () => {
  await useSpending().reload();
  useSpending().state.value.products[0].name = "Bevanda intera";
  useSpending().state.value.products[0].brand = "Marca esempio";
  const products = useProducts();
  products.search.value = "LATTE";
  expect(products.rows.value.map((product) => product.name)).toEqual(["Bevanda intera"]);
  products.search.value = "Marca esempio";
  expect(products.rows.value.map((product) => product.name)).toEqual(["Bevanda intera"]);
});

test("known products keep their AI provenance after manual corrections or a new search", async () => {
  await useSpending().reload();
  Object.assign(useSpending().state.value.products[0], {
    source_url: "https://example.com/latte",
    confirmation: "manual",
    search_status: "running",
  });
  const products = useProducts();
  expect(products.rows.value).toHaveLength(2);
  products.knownOnly.value = true;
  expect(products.rows.value.map((product) => product.id)).toEqual([1]);
  products.search.value = "Altro";
  expect(products.rows.value).toHaveLength(0);
  products.knownOnly.value = false;
  expect(products.rows.value.map((product) => product.id)).toEqual([2]);
});


test.each(["unknown", "variable_weight", undefined] as const)(
  "%s products retain spending history without a price comparison",
  async (kind) => {
    await useSpending().reload();
    useSpending().state.value.products[0].kind = kind;
    const products = useProducts();
    products.selected.value = 1;
    expect(products.comparable.value).toBe(false);
    expect(products.option.value.series).toEqual([]);
    expect(products.history.value.map((entry) => entry.net)).toEqual([402, 159]);
    expect(products.rows.value.find((product) => product.id === 1)?.amount).toBe(561);
    useSpending().state.value.products[0].kind = "fixed";
    expect(products.comparable.value).toBe(true);
    expect(products.option.value.series).toHaveLength(1);
  },
);
