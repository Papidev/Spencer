<script setup lang="ts">
defineProps<{ illustration?: string; name: string }>();

const drawings: Record<string, string> = {
  milk: "🥛", cheese: "🧀", eggs: "🥚", yogurt: "🥣", bread: "🍞",
  pasta: "🍝", rice: "🍚", meat: "🥩", fish: "🐟", vegetables: "🥦",
  fruit: "🍎", coffee: "☕", tea: "🫖", water: "💧", juice: "🧃",
  wine: "🍷", beer: "🍺", oil: "🫒", sauce: "🥫", cookies: "🍪",
  chocolate: "🍫", "ice-cream": "🍦", frozen: "🧊", cleaning: "🧴",
  paper: "🧻", "personal-care": "🧼", "pet-food": "🐾", groceries: "🛍️",
  banana: "🍌", citrus: "🍊", grapes: "🍇", tomato: "🍅", potato: "🥔",
  carrot: "🥕", onion: "🧅", cucumber: "🥒", salad: "🥬", butter: "🧈",
  pizza: "🍕", nuts: "🥜", lightbulb: "💡", hamburger: "🍔", sponge: "🧽",
  eggplant: "🍆", lemon: "🍋", peach: "🍑",
  dessert: "🍰", cereal: "🌾", bags: "🛍️", salami: "🍖", spirits: "🍸",
};
</script>

<template>
  <span
    class="product-illustration"
    :class="`illustration-${illustration || 'groceries'}`"
    role="img"
    :aria-label="`${name} · illustrazione generica`"
    title="Illustrazione generica, non una foto del prodotto"
  >{{ drawings[illustration || 'groceries'] || drawings.groceries }}</span>
</template>
