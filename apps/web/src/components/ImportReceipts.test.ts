import { afterAll, beforeAll, expect, test } from "vitest";
import { render, screen } from "@testing-library/vue";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import ImportReceipts from "./ImportReceipts.vue";

let uploads = 0;
const server = setupServer(
  http.post("*/api/receipts", () => {
    uploads++;
    return HttpResponse.json(
      uploads === 1
        ? { status: "failed", error: "Il totale non corrisponde." }
        : uploads === 2
          ? { status: "duplicate" }
          : { status: "imported", line_count: 1 },
      { status: 201 },
    );
  }),
  http.get("*/api/state", () =>
    HttpResponse.json({
      receipts: [],
      purchases: [],
      products: [],
      aliases: [],
      categories: [],
    }),
  ),
);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterAll(() => server.close());

test("batch import reports each result and continues after a failed receipt", async () => {
  render(ImportReceipts);
  await userEvent.upload(
    screen.getByLabelText("Seleziona scontrini PDF"),
    ["bad.pdf", "duplicate.pdf", "good.pdf"].map(
      (name) => new File(["%PDF-test"], name, { type: "application/pdf" }),
    ),
  );
  await screen.findByText(/1 articolo importato/);
  expect(screen.getByText(/Il totale non corrisponde/)).toBeInTheDocument();
  expect(
    screen.getByText(/Già presente, nessun duplicato creato/),
  ).toBeInTheDocument();
  expect(uploads).toBe(3);
  expect(screen.getByRole("button", { name: "Carica PDF" })).toBeEnabled();
});
