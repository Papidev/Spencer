import { computed, ref } from "vue";
import { request } from "./api";
import type { EnrichedPurchase, State } from "./types";

const state = ref<State>({
  receipts: [],
  products: [],
  aliases: [],
  categories: [],
  purchases: [],
});
const loading = ref(true);
const error = ref("");
const busy = ref(false);
const notice = ref("");

// One local data source shared across routes. No additional state library is needed yet.
export const useSpending = () => {
  const purchases = computed<EnrichedPurchase[]>(() => {
    const aliases = new Map(
      state.value.aliases.map((alias) => [alias.id, alias]),
    );
    const products = new Map(
      state.value.products.map((product) => [product.id, product]),
    );
    const receipts = new Map(
      state.value.receipts.map((receipt) => [receipt.id, receipt]),
    );
    return state.value.purchases.flatMap((purchase) => {
      const alias = aliases.get(purchase.alias_id);
      const product = alias && products.get(alias.product_id);
      const receipt = receipts.get(purchase.receipt_id);
      return alias && product && receipt?.status === "imported"
        ? [{ ...purchase, product, receipt, label: alias.label }]
        : [];
    });
  });
  const products = computed(() =>
    state.value.products.filter((product) =>
      purchases.value.some((purchase) => purchase.product.id === product.id),
    ),
  );
  const pending = computed(() =>
    products.value.filter((product) => !product.reviewed),
  );

  const reload = async () => {
    try {
      state.value = await request<State>("/state");
      error.value = "";
    } catch (caught) {
      error.value =
        caught instanceof Error
          ? caught.message
          : "Connessione non disponibile.";
    } finally {
      loading.value = false;
    }
  };

  const mutate = async (path: string, method: string, body?: unknown) => {
    busy.value = true;
    error.value = "";
    try {
      await request(path, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      await reload();
      notice.value = "Modifiche salvate.";
      return true;
    } catch (caught) {
      error.value =
        caught instanceof Error ? caught.message : "Operazione non riuscita.";
      return false;
    } finally {
      busy.value = false;
    }
  };

  return {
    state,
    loading,
    error,
    busy,
    notice,
    purchases,
    products,
    pending,
    reload,
    mutate,
  };
};
