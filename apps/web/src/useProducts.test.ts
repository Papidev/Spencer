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
        { id: 1, name: "Latte", category_id: null, reviewed: true },
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
        products: [{ id: 1, name: "Latte", category_id: null, reviewed: true }],
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
