import { afterAll, afterEach, beforeAll, expect, test } from "vitest";
import userEvent from "@testing-library/user-event";
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
    products: [{ id: 1, name: "POLLO", category_id: null, reviewed: false, search_status: "not_found", category_status: "pending" }],
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
  expect(screen.getByText(/Categorie IA: 1 prodotto in lavorazione/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Modifica POLLO" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Cerca dettagli per/ })).not.toBeInTheDocument();
});


test("table headers toggle category sorting and stay in sync with the sorting menu and filters", async () => {
  const user = userEvent.setup();
  server.use(http.get("*/api/state", () => HttpResponse.json({
    receipts: [{ id: 1, date: "2026-11-08", status: "imported" }, { id: 2, date: "2026-11-09", status: "imported" }],
    categories: [{ id: 1, name: "Verdura" }, { id: 99, name: "Bevande" }],
    products: [
      { id: 1, name: "Zucchine", category_id: 1, kind: "variable_weight" },
      { id: 2, name: "Acqua", category_id: 99, kind: "fixed" },
      { id: 3, name: "Pane", category_id: null, kind: "unknown" },
      { id: 4, name: "Aranciata", category_id: 99, kind: "fixed" },
    ],
    aliases: [1, 2, 3, 4].map((id) => ({ id, label: `Prodotto ${id}`, product_id: id })),
    purchases: [
      ...[1, 2, 3, 4].map((id) => ({ id, receipt_id: 1, alias_id: id, gross_cents: id * 100, discount_cents: 0, price_verified: true })),
      { id: 5, receipt_id: 2, alias_id: 1, gross_cents: 100, discount_cents: 0, price_verified: true },
    ],
  })));
  await useSpending().reload();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", component: Products }],
  });
  await router.push("/");
  await router.isReady();
  render(Products, { global: { plugins: [router] } });
  const table = screen.getByRole("table", { name: "Prodotti" });
  const names = () => within(table).getAllByRole("row").slice(1).map((row) =>
    within(row).getByRole("button", { name: /^Modifica / }).getAttribute("aria-label"),
  );
  await user.click(within(table).getByRole("button", { name: "Categoria" }));
  expect(names()).toEqual(["Modifica Acqua", "Modifica Aranciata", "Modifica Pane", "Modifica Zucchine"]);
  expect(within(table).getByRole("columnheader", { name: "Categoria" })).toHaveAttribute("aria-sort", "ascending");
  expect(screen.getByRole("combobox", { name: "Ordina prodotti" })).toHaveValue("category-asc");
  await user.click(within(table).getByRole("button", { name: "Categoria" }));
  expect(names()).toEqual(["Modifica Zucchine", "Modifica Pane", "Modifica Acqua", "Modifica Aranciata"]);
  expect(within(table).getByRole("columnheader", { name: "Categoria" })).toHaveAttribute("aria-sort", "descending");
  await user.selectOptions(screen.getByRole("combobox", { name: "Ordina prodotti" }), "name-asc");
  expect(names()).toEqual(["Modifica Acqua", "Modifica Aranciata", "Modifica Pane", "Modifica Zucchine"]);
  await user.click(within(table).getByRole("button", { name: "Prodotto" }));
  expect(names()).toEqual(["Modifica Zucchine", "Modifica Pane", "Modifica Aranciata", "Modifica Acqua"]);
  await user.click(within(table).getByRole("button", { name: "Tipo" }));
  expect(names()).toEqual(["Modifica Pane", "Modifica Acqua", "Modifica Aranciata", "Modifica Zucchine"]);
  await user.click(within(table).getByRole("button", { name: "Spesa totale" }));
  expect(names()).toEqual(["Modifica Acqua", "Modifica Zucchine", "Modifica Pane", "Modifica Aranciata"]);
  await user.click(within(table).getByRole("button", { name: "Spesa totale" }));
  expect(names()).toEqual(["Modifica Aranciata", "Modifica Pane", "Modifica Acqua", "Modifica Zucchine"]);
  await user.click(within(table).getByRole("button", { name: "Visite con acquisto" }));
  expect(names()).toEqual(["Modifica Acqua", "Modifica Pane", "Modifica Aranciata", "Modifica Zucchine"]);
  await user.click(within(table).getByRole("button", { name: "Visite con acquisto" }));
  expect(names()).toEqual(["Modifica Zucchine", "Modifica Aranciata", "Modifica Pane", "Modifica Acqua"]);
  await user.click(within(table).getByRole("button", { name: "Categoria" }));
  await user.type(screen.getByRole("textbox", { name: "Cerca un prodotto" }), "a");
  expect(names()).toEqual(["Modifica Acqua", "Modifica Aranciata", "Modifica Pane"]);
  await user.selectOptions(screen.getByRole("combobox", { name: "Filtra per categoria" }), "99");
  expect(names()).toEqual(["Modifica Acqua", "Modifica Aranciata"]);
});
