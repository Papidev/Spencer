<script setup lang="ts">
import { ref } from "vue";
import { Check, Pencil } from "lucide-vue-next";
import type { Category, Product } from "../types";
import { useSpending } from "../store";

const props = defineProps<{
  product: Product;
  categories: Category[];
  labels: string[];
}>();
defineEmits<{ edit: [id: number] }>();
const { mutate, busy } = useSpending();
const name = ref(props.product.name);
const categoryId = ref(props.product.category_id);
</script>

<template>
  <tr>
    <td>
      <label class="visually-hidden" :for="`name-${product.id}`"
        >Nome per {{ product.name }}</label
      ><input
        :id="`name-${product.id}`"
        v-model="name"
        maxlength="160"
      /><small>{{ labels.join(" · ") }}</small>
    </td>
    <td>
      <select
        v-model="categoryId"
        :aria-label="`Categoria per ${product.name}`"
      >
        <option :value="null">Non categorizzato</option>
        <option
          v-for="category in categories"
          :key="category.id"
          :value="category.id"
        >
          {{ category.name }}
        </option>
      </select>
    </td>
    <td>
      <div class="row-actions">
        <button
          class="button small primary"
          :disabled="busy || !name.trim()"
          :aria-label="`Conferma ${product.name}`"
          @click="
            mutate(`/products/${product.id}`, 'PATCH', {
              name,
              category_id: categoryId,
              reviewed: true,
            })
          "
        >
          <Check :size="15" />Conferma</button
        ><button
          class="icon-button"
          :aria-label="`Associa ${product.name}`"
          @click="$emit('edit', product.id)"
        >
          <Pencil :size="16" />
        </button>
      </div>
    </td>
  </tr>
</template>
