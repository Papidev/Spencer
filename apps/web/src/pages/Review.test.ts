import {
  beforeAll,
  afterAll,
  afterEach,
  beforeEach,
  expect,
  test,
} from "vitest";
import { render, screen, waitFor } from "@testing-library/vue";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import Review from "./Review.vue";
import { useSpending } from "../store";
import type { State } from "../types";

let data: State;
const server = setupServer(
  http.get("*/api/state", () => HttpResponse.json(data)),
  http.patch("*/api/products/:id", async ({ params, request }) => {
    Object.assign(
      data.products.find((product) => product.id === Number(params.id))!,
      await request.json(),
    );
    return HttpResponse.json({ updated: true });
  }),
);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());
beforeEach(async () => {
  data = {
    receipts: [
      {
        id: 1,
        filename: "test.pdf",
        retailer: "Esselunga",
        store: "Negozio test",
        date: "2026-11-08",
        document: "1",
        status: "imported",
        error: null,
        total_cents: 200,
        voucher_cents: 0,
        paid_cents: 200,
        line_count: 1,
        payments: [],
      },
    ],
    products: [
      { id: 1, name: "LATTE TEST", category_id: null, reviewed: false },
    ],
    aliases: [
      { id: 1, label: "LATTE TEST", retailer: "Esselunga", product_id: 1 },
    ],
    categories: [{ id: 1, name: "Latticini" }],
    purchases: [
      {
        id: 1,
        receipt_id: 1,
        alias_id: 1,
        position: 0,
        gross_cents: 200,
        discount_cents: 0,
        price_verified: true,
        discount_label: "",
      },
    ],
  };
  await useSpending().reload();
});

test("a correction confirms the product and updates historical categorisation", async () => {
  const user = userEvent.setup();
  render(Review);
  await user.clear(
    screen.getByRole("textbox", { name: "Nome per LATTE TEST" }),
  );
  await user.type(
    screen.getByRole("textbox", { name: "Nome per LATTE TEST" }),
    "Latte intero",
  );
  await user.selectOptions(
    screen.getByRole("combobox", { name: "Categoria per LATTE TEST" }),
    "1",
  );
  await user.click(screen.getByRole("button", { name: "Conferma LATTE TEST" }));
  await screen.findByRole("heading", { name: "Tutto in ordine." });
  expect(useSpending().purchases.value[0].product.name).toBe("Latte intero");
  expect(useSpending().purchases.value[0].product.category_id).toBe(1);
});

test("failed saves preserve the product for review and explain the error", async () => {
  server.use(
    http.patch("*/api/products/:id", () =>
      HttpResponse.json({ detail: "Categoria non valida." }, { status: 422 }),
    ),
  );
  render(Review);
  await userEvent.click(
    screen.getByRole("button", { name: "Conferma LATTE TEST" }),
  );
  await waitFor(() =>
    expect(useSpending().error.value).toBe("Categoria non valida."),
  );
  expect(
    screen.getByRole("button", { name: "Conferma LATTE TEST" }),
  ).toBeInTheDocument();
});
