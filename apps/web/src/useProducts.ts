import { computed, ref } from "vue";
import { useSpending } from "./store";
import { money, dateLabel } from "./api";

export const useProducts = () => {
  const { state, products, purchases } = useSpending();
  const search = ref("");
  const category = ref("all");
  const knownOnly = ref(false);
  const order = ref("spending");
  const selected = ref<number | null>(null);
  const selectedProduct = computed(() =>
    products.value.find((product) => product.id === selected.value),
  );
  const comparable = computed(() => selectedProduct.value?.kind === "fixed");
  const rows = computed(() =>
    products.value
      .filter(
        (product) =>
          [
            product.name,
            product.brand ?? "",
            ...state.value.aliases
              .filter((alias) => alias.product_id === product.id)
              .map((alias) => alias.label),
          ]
            .join(" ")
            .toLocaleLowerCase("it")
            .includes(search.value.toLocaleLowerCase("it")) &&
          (category.value === "all" ||
            String(product.category_id) === category.value) &&
          (!knownOnly.value || Boolean(product.source_url)),
      )
      .map((product) => {
        const lines = purchases.value.filter(
          (line) => line.product.id === product.id,
        );
        return {
          ...product,
          visits: new Set(lines.map((line) => line.receipt_id)).size,
          amount: lines.reduce(
            (sum, line) => sum + line.gross_cents - line.discount_cents,
            0,
          ),
        };
      })
      .sort((a, b) =>
        order.value === "visits"
          ? b.visits - a.visits || b.amount - a.amount
          : b.amount - a.amount,
      ),
  );
  const history = computed(() => {
    const grouped = new Map<
      string,
      {
        id: string;
        receiptId: number;
        date: string;
        promotional: boolean;
        gross: number;
        net: number;
        count: number;
        verified: boolean;
      }
    >();
    for (const line of purchases.value.filter(
      (line) => line.product.id === selected.value,
    )) {
      const key = `${line.receipt_id}-${line.discount_cents > 0}`;
      if (!grouped.has(key))
        grouped.set(key, {
          id: key,
          receiptId: line.receipt_id,
          date: line.receipt.date!,
          promotional: line.discount_cents > 0,
          gross: 0,
          net: 0,
          count: 0,
          verified: true,
        });
      const entry = grouped.get(key)!;
      entry.gross += line.gross_cents;
      entry.net += line.gross_cents - line.discount_cents;
      entry.count++;
      entry.verified &&= line.price_verified;
    }
    return [...grouped.values()].sort(
      (a, b) =>
        a.date.localeCompare(b.date) ||
        a.receiptId - b.receiptId ||
        Number(a.promotional) - Number(b.promotional),
    );
  });
  const option = computed(() => ({
    textStyle: { fontFamily: "inherit", color: "#7e8982" },
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: unknown) => money(Number(value) * 100),
    },
    grid: { left: 55, right: 25, top: 25, bottom: 40 },
    xAxis: {
      type: "category",
      data: history.value.map(
        (entry) =>
          `${dateLabel(entry.date)}\n${entry.promotional ? "In promozione" : "Prezzo pieno"}`,
      ),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#e3e8df" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { formatter: "{value} €" },
      splitLine: { lineStyle: { color: "#edf0eb" } },
    },
    series: comparable.value
      ? [
          {
            name: "Prezzo pagato",
            type: "line",
            symbolSize: 9,
            lineStyle: { color: "#a7b9a3" },
            data: history.value.map((entry) => ({
              value: entry.verified ? entry.net / entry.count / 100 : null,
              symbol: entry.promotional ? "diamond" : "circle",
              itemStyle: { color: entry.promotional ? "#c48055" : "#29634f" },
            })),
          },
        ]
      : [],
  }));

  return {
    state,
    products,
    search,
    category,
    knownOnly,
    order,
    selected,
    selectedProduct,
    comparable,
    rows,
    history,
    option,
  };
};
