import { computed } from "vue";
import { useSpending } from "./store";

const categoryDrawings: Record<string, string> = {
  "Frutta e verdura": "vegetables",
  Carne: "meat",
  Pesce: "fish",
  Salumi: "salami",
  "Latticini e uova": "milk",
  "Pasta, riso e cereali": "pasta",
  "Pane e prodotti da forno": "bread",
  "Dolci e snack": "cookies",
  Surgelati: "frozen",
  "Dispensa e condimenti": "sauce",
  Bevande: "juice",
  Alcolici: "wine",
  Casa: "cleaning",
  "Cura della persona": "personal-care",
};

export const useProductIllustration = (product: {
  illustration?: string;
  categoryId?: number | null;
}) => {
  const { state } = useSpending();
  return computed(() =>
    product.illustration && product.illustration !== "groceries"
      ? product.illustration
      : categoryDrawings[
          state.value.categories.find((category) => category.id === product.categoryId)?.name ?? ""
        ] || product.illustration,
  );
};
