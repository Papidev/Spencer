import { afterAll, beforeAll, expect, test } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { useOverview } from "./useOverview";
import { useSpending } from "./store";

const server = setupServer(
  http.get("*/api/state", () =>
    HttpResponse.json({
      receipts: [
        {
          id: 1,
          date: "2026-11-08",
          status: "imported",
          total_cents: 1000,
          voucher_cents: 2000,
          paid_cents: 800,
        },
        { id: 2, date: null, status: "failed", total_cents: 9999 },
      ],
      categories: [],
      products: [{ id: 1, name: "Latte", category_id: null, reviewed: false }],
      aliases: [
        { id: 1, label: "LATTE", retailer: "Esselunga", product_id: 1 },
      ],
      purchases: [1, 2].map((id) => ({
        id,
        receipt_id: 1,
        alias_id: 1,
        gross_cents: 2000,
        discount_cents: 500,
        price_verified: true,
      })),
    }),
  ),
);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());

test("overview and monthly chart show actual out-of-pocket spending; visits count receipts", async () => {
  await useSpending().reload();
  const overview = useOverview();
  expect(overview.receipts.value).toHaveLength(1);
  expect(overview.paid.value).toBe(800);
  expect(overview.monthlyOption.value.series).toHaveLength(1);
  expect(overview.monthlyOption.value.series[0].data).toEqual([8]);
  expect(overview.topProducts.value[0].visits.size).toBe(1);
  expect(overview.categories.value).toEqual([["Non categorizzato", 3000]]);
  overview.period.value = "2026-10";
  expect(overview.paid.value).toBe(0);
});
