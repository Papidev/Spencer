<script setup lang="ts">
import { ref, watch } from "vue";
import { Package } from "lucide-vue-next";

const props = defineProps<{ productId: number; url?: string; name: string }>();
const failed = ref(false);
watch(
  () => props.url,
  () => {
    failed.value = false;
  },
);
</script>

<template>
  <span class="product-image">
    <img
      v-if="url && !failed"
      :src="`/api/products/${productId}/image?packaged=1&v=${encodeURIComponent(url)}`"
      :alt="name"
      loading="lazy"
      referrerpolicy="no-referrer"
      @error="failed = true"
    />
    <Package v-else :size="22" aria-hidden="true" />
  </span>
</template>
