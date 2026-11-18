import { afterAll, afterEach, beforeAll, beforeEach, expect, test } from "vitest";
import { render, screen, waitFor } from "@testing-library/vue";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import ProductEditor from "./ProductEditor.vue";
import ProductIdentity from "./ProductIdentity.vue";
import { useSpending } from "../store";
import type { State } from "../types";

let data: State;
let saved: Record<string, unknown> | undefined;
let search: unknown;
const server = setupServer(
  http.get("*/api/state", () => HttpResponse.json(data)),
  http.patch("*/api/products/1", async ({ request }) => {
    saved = await request.json() as Record<string, unknown>;
    Object.assign(data.products[0], saved);
    return HttpResponse.json({ updated: true });
  }),
  http.post("*/api/products/1/search", async ({ request }) => {
    search = await request.json();
    return HttpResponse.json({ queued: true });
  }),
);
beforeAll(() => {
  // jsdom does not implement the native dialog API.
  HTMLDialogElement.prototype.showModal = () => {
    screen.getByRole("dialog", { hidden: true }).setAttribute("open", "");
  };
  server.listen({ onUnhandledRequest: "error" });
});
afterAll(() => server.close());
afterEach(() => server.resetHandlers());
beforeEach(async () => {
  saved = undefined;
  search = undefined;
  data = {
    receipts: [], purchases: [], aliases: [], categories: [{ id: 1, name: "Dispensa" }],
    products: [{
      id: 1, name: "Pesto alla Genovese", category_id: 1, reviewed: true,
      brand: "Barilla", pack_size: "190 g", image_url: "https://example.com/pesto.jpg",
      source_url: "https://example.com/pesto", confirmation: "automatic", search_status: "matched",
    }],
  };
  await useSpending().reload();
});

test("shows the automatic result and source, and saves only corrected fields", async () => {
  const user = userEvent.setup();
  render(ProductEditor, { props: { productId: 1 } });
  expect(screen.getByText("Confermato automaticamente")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Apri la fonte dei dettagli" })).toHaveAttribute("href", "https://example.com/pesto");
  await user.clear(screen.getByRole("textbox", { name: "Formato" }));
  await user.type(screen.getByRole("textbox", { name: "Formato" }), "90 g");
  await user.click(screen.getByRole("button", { name: "Salva e conferma" }));
  await waitFor(() => expect(saved).toEqual({ pack_size: "90 g", reviewed: true }));
});

test("retries without replacing manual corrections unless explicitly selected", async () => {
  const user = userEvent.setup();
  const view = render(ProductEditor, { props: { productId: 1 } });
  await user.click(screen.getByRole("button", { name: "Cerca di nuovo" }));
  await waitFor(() => expect(search).toEqual({ replace_manual: false }));
  view.unmount();
  render(ProductEditor, { props: { productId: 1 } });
  await user.click(screen.getByRole("checkbox", { name: "Sostituisci anche i dettagli corretti manualmente" }));
  await user.click(screen.getByRole("button", { name: "Cerca di nuovo" }));
  await waitFor(() => expect(search).toEqual({ replace_manual: true }));
});

test("displays the original receipt description alongside the recognized product", () => {
  render(ProductIdentity, { props: { product: data.products[0], original: "BAR.PESTO GENOV. 190G" } });
  expect(screen.getByText("Pesto alla Genovese")).toBeInTheDocument();
  expect(screen.getByText("Scontrino: BAR.PESTO GENOV. 190G")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: "Pesto alla Genovese" })).toHaveAttribute("src", "/api/products/1/image?packaged=1&v=https%3A%2F%2Fexample.com%2Fpesto.jpg");
});


test("saves a manual product classification", async () => {
  const user = userEvent.setup();
  render(ProductEditor, { props: { productId: 1 } });
  expect(screen.getByRole("combobox", { name: "Tipo di prodotto" })).toHaveValue("unknown");
  await user.selectOptions(screen.getByRole("combobox", { name: "Tipo di prodotto" }), "variable_weight");
  await user.click(screen.getByRole("button", { name: "Salva e conferma" }));
  await waitFor(() => expect(saved).toEqual({ kind: "variable_weight", reviewed: true }));
});
