import { fireEvent, render, screen } from "@testing-library/vue";
import { expect, test } from "vitest";
import ProductImage from "./ProductImage.vue";

test("shows a generic drawing when a photo is missing or fails, and retries a new photo", async () => {
  const { rerender } = render(ProductImage, {
    props: { productId: 1, name: "Latte", illustration: "milk" },
  });
  expect(screen.getByRole("img", { name: "Latte · illustrazione generica" })).toHaveTextContent("🥛");
  await rerender({ url: "https://example.com/milk.jpg" });
  expect(screen.getByRole("img", { name: /illustrazione generica/ })).toBeVisible();
  await fireEvent.load(screen.getByRole("img", { name: "Latte" }));
  expect(screen.queryByRole("img", { name: /illustrazione generica/ })).not.toBeInTheDocument();
  await fireEvent.error(screen.getByRole("img", { name: "Latte" }));
  expect(screen.getByRole("img", { name: /illustrazione generica/ })).toBeVisible();
  await rerender({ url: "https://example.com/new-milk.jpg" });
  expect(screen.getByRole("img", { name: "Latte" })).toHaveAttribute("src", expect.stringContaining("new-milk.jpg"));
});

test("uses the category drawing while the local model is choosing a product drawing", async () => {
  const { useSpending } = await import("../store");
  useSpending().state.value.categories = [{ id: 5, name: "Latticini e uova" }];
  const { rerender } = render(ProductImage, { props: { productId: 2, name: "Formaggio", categoryId: 5 } });
  expect(screen.getByRole("img", { name: /Formaggio · illustrazione generica/ })).toHaveTextContent("🥛");
  await rerender({ illustration: "groceries" });
  expect(screen.getByRole("img", { name: /Formaggio · illustrazione generica/ })).toHaveTextContent("🥛");
  await rerender({ illustration: "cheese" });
  expect(screen.getByRole("img", { name: /Formaggio · illustrazione generica/ })).toHaveTextContent("🧀");
});
