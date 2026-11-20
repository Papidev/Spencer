<script setup lang="ts">
import { ref, watch } from "vue";
import { useProductIllustration } from "../useProductIllustration";
import ProductIllustration from "./ProductIllustration.vue";

const props = defineProps<{
  productId: number;
  url?: string;
  name: string;
  illustration?: string;
  categoryId?: number | null;
}>();
const illustration = useProductIllustration(props);
const failed = ref(false);
const loaded = ref(false);
watch(
  () => props.url,
  () => {
    failed.value = false;
    loaded.value = false;
  },
);
</script>

<template>
  <span class="product-image">
    <ProductIllustration v-if="!url || failed || !loaded" :illustration="illustration" :name="name" />
    <img
      v-if="url && !failed"
      :class="{ loaded }"
      :src="`/api/products/${productId}/image?packaged=1&v=${encodeURIComponent(url)}`"
      :alt="name"
      loading="lazy"
      referrerpolicy="no-referrer"
      @load="loaded = true"
      @error="failed = true"
    />
  </span>
</template>
