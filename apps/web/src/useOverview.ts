import { computed, ref } from "vue";
import { useSpending } from "./store";
import { money } from "./api";

export const useOverview = () => {
  const { state, purchases } = useSpending();
  const period = ref("all");
  const months = computed(() =>
    [
      ...new Set(
        state.value.receipts
          .filter((receipt) => receipt.status === "imported")
          .map((receipt) => receipt.date!.slice(0, 7)),
      ),
    ]
      .sort()
      .reverse(),
  );
  const receipts = computed(() =>
    state.value.receipts.filter(
      (receipt) =>
        receipt.status === "imported" &&
        (period.value === "all" || receipt.date?.startsWith(period.value)),
    ),
  );
  const lines = computed(() =>
    purchases.value.filter((purchase) =>
      receipts.value.some((receipt) => receipt.id === purchase.receipt_id),
    ),
  );
  const paid = computed(() =>
    receipts.value.reduce((sum, receipt) => sum + receipt.paid_cents, 0),
  );
  const topProducts = computed(() => {
    const grouped = new Map<
      number,
      {
        id: number;
        name: string;
        category: string;
        amount: number;
        visits: Set<number>;
      }
    >();
    for (const line of lines.value) {
      if (!grouped.has(line.product.id))
        grouped.set(line.product.id, {
          id: line.product.id,
          name: line.product.name,
          category:
            state.value.categories.find(
              (category) => category.id === line.product.category_id,
            )?.name ?? "Non categorizzato",
          amount: 0,
          visits: new Set(),
        });
      const product = grouped.get(line.product.id)!;
      product.amount += line.gross_cents - line.discount_cents;
      product.visits.add(line.receipt_id);
    }
    return [...grouped.values()].sort((a, b) => b.amount - a.amount);
  });
  const categories = computed(() => {
    const grouped = new Map<string, number>();
    for (const line of lines.value) {
      const category =
        state.value.categories.find(
          (category) => category.id === line.product.category_id,
        )?.name ?? "Non categorizzato";
      grouped.set(
        category,
        (grouped.get(category) ?? 0) + line.gross_cents - line.discount_cents,
      );
    }
    return [...grouped].sort((a, b) => b[1] - a[1]);
  });
  const monthlyOption = computed(() => {
    const monthly = new Map<string, number>();
    for (const receipt of receipts.value) {
      const month = receipt.date!.slice(0, 7);
      monthly.set(month, (monthly.get(month) ?? 0) + receipt.paid_cents);
    }
    const entries = [...monthly].sort(([a], [b]) => a.localeCompare(b));
    return {
      animationDuration: 400,
      textStyle: { fontFamily: "inherit", color: "#7e8982" },
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: unknown) => money(Number(value) * 100),
      },
      grid: { left: 54, right: 22, top: 18, bottom: 40 },
      xAxis: {
        type: "category",
        data: entries.map(([month]) =>
          new Intl.DateTimeFormat("it-IT", {
            month: "short",
            year: "2-digit",
          }).format(new Date(`${month}-01T12:00:00`)),
        ),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { margin: 16 },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "#edf0eb", type: "dashed" } },
        axisLabel: { formatter: "{value} €" },
      },
      series: [
        {
          name: "Esborso",
          type: "bar",
          barMaxWidth: 42,
          itemStyle: { color: "#29634f", borderRadius: [5, 5, 0, 0] },
          data: entries.map(([, value]) => value / 100),
        },
      ],
    };
  });
  return {
    period,
    months,
    receipts,
    lines,
    paid,
    categoryTotal: computed(() =>
      categories.value.reduce((sum, [, amount]) => sum + amount, 0),
    ),
    topProducts,
    categories,
    monthlyOption,
  };
};
