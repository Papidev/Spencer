<script setup lang="ts">
import type { Product } from "../types";
import ProductImage from "./ProductImage.vue";

defineProps<{ product: Product; original?: string }>();
</script>

<template>
  <span class="product-identity">
    <ProductImage :product-id="product.id" :url="product.image_url" :illustration="product.illustration" :category-id="product.category_id" :name="product.name" />
    <span>
      <strong>{{ product.name }}</strong>
      <small v-if="product.brand || product.pack_size">{{
        [product.brand, product.pack_size].filter(Boolean).join(" · ")
      }}</small>
      <small v-if="original" class="muted">Scontrino: {{ original }}</small>
    </span>
  </span>
</template>
