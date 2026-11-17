import { afterAll, afterEach, beforeAll, expect, test } from "vitest";
import { render, screen, within } from "@testing-library/vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import Products from "./Products.vue";
import { useSpending } from "../store";

const server = setupServer();
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test.each(["unknown", "variable_weight"] as const)(
  "%s products show purchase spending without a price chart",
  async (kind) => {
    server.use(http.get("*/api/state", () => HttpResponse.json({
      receipts: [{ id: 1, date: "2026-11-08", status: "imported" }],
      categories: [],
      products: [{ id: 1, name: "Pollo", category_id: null, reviewed: true, kind }],
      aliases: [{ id: 1, label: "POLLO", product_id: 1 }],
      purchases: [
        { id: 1, receipt_id: 1, alias_id: 1, gross_cents: 400, discount_cents: 0, price_verified: true },
        { id: 2, receipt_id: 1, alias_id: 1, gross_cents: 600, discount_cents: 0, price_verified: true },
      ],
    })));
    await useSpending().reload();
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", component: Products }],
    });
    await router.push("/?prodotto=1");
    await router.isReady();
    render(Products, { global: { plugins: [router] } });
    const history = screen.getByRole("table", { name: "Storico acquisti del prodotto" });
    expect(within(history).getByRole("columnheader", { name: "Spesa acquisti" })).toBeInTheDocument();
    expect(within(history).getByText(/10,00/)).toBeInTheDocument();
    expect(within(history).queryByText(/5,00/)).not.toBeInTheDocument();
    expect(screen.queryByRole("img", { name: "Prezzi pagati: acquisti a prezzo pieno e in promozione" })).not.toBeInTheDocument();
    expect(screen.getByText(kind === "variable_weight" ? /le confezioni possono avere quantità diverse/ : /Tipo di prodotto da determinare:/)).toBeInTheDocument();
  },
);

test("unidentified products offer correction without a collective retry", async () => {
  server.use(http.get("*/api/state", () => HttpResponse.json({
    receipts: [{ id: 1, date: "2026-11-08", status: "imported" }],
    categories: [],
    products: [{ id: 1, name: "POLLO", category_id: null, reviewed: false, search_status: "not_found" }],
    aliases: [{ id: 1, label: "POLLO", product_id: 1 }],
    purchases: [{ id: 1, receipt_id: 1, alias_id: 1, gross_cents: 400, discount_cents: 0, price_verified: true }],
  })));
  await useSpending().reload();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", component: Products }],
  });
  await router.push("/");
  await router.isReady();
  render(Products, { global: { plugins: [router] } });
  expect(screen.getByText(/1 prodotto non identificato/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Modifica POLLO" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Cerca dettagli per/ })).not.toBeInTheDocument();
});
