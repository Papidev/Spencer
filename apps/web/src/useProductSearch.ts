import { computed } from "vue";
import { useSpending } from "./store";
import type { Product } from "./types";

export const productSearchLabel = (product: Product) => {
  switch (product.search_status) {
    case "pending":
      return "Ricerca in attesa";
    case "running":
      return "Ricerca in corso";
    case "retry":
      return "Ricerca da riprovare";
    case "failed":
      return "Ricerca non disponibile";
    case "not_found":
      return "Non identificato";
    default:
      return product.confirmation === "automatic"
        ? "Confermato automaticamente"
        : product.reviewed ? "Descrizione confermata" : "Da rivedere";
  }
};

export const useProductSearch = () => {
  const { products, mutate, notice, busy } = useSpending();
  const waiting = computed(() =>
    products.value.filter((product) =>
      ["pending", "running", "retry"].includes(product.search_status ?? ""),
    ).length,
  );
  const categorizing = computed(() =>
    products.value.filter((product) =>
      product.category_id === null &&
      !product.manual_fields?.includes("category_id") &&
      ["pending", "running", "retry"].includes(product.category_status ?? ""),
    ).length,
  );
  const available = computed(() =>
    products.value.filter((product) =>
      ["idle", "failed"].includes(product.search_status ?? "idle"),
    ).length,
  );
  const unidentified = computed(() =>
    products.value.filter((product) => product.search_status === "not_found").length,
  );
  const search = async () => {
    if (await mutate("/products/search", "POST"))
      notice.value = "Ricerca dei dettagli avviata. Puoi continuare a usare Spencer.";
  };
  return { waiting, categorizing, available, unidentified, search, busy };
};
