<script setup lang="ts">
import { Store } from "lucide-vue-next";

defineProps<{ retailer: string }>();
</script>

<template>
  <span class="retailer-image">
    <img v-if="retailer.toLowerCase() === 'esselunga'" src="/esselunga.svg" alt="Esselunga" />
    <Store v-else :size="22" aria-hidden="true" />
  </span>
</template>
