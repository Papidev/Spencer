<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import {
  LayoutDashboard,
  ReceiptText,
  Package,
  ListChecks,
  X,
} from "lucide-vue-next";
import { useSpending } from "./store";

const { products, reload, pending, error, notice, loading } = useSpending();
onMounted(reload);
const polling = setInterval(() => {
  if (
    products.value.some((product) =>
      ["pending", "running", "retry"].includes(product.search_status ?? ""),
    )
  ) void reload();
}, 4000);
onUnmounted(() => clearInterval(polling));
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink to="/" class="brand" aria-label="Spencer, panoramica"
        >Spencer</RouterLink
      >
      <nav aria-label="Navigazione principale">
        <RouterLink to="/" class="nav-link" exact-active-class="active"
          ><LayoutDashboard :size="18" />Panoramica</RouterLink
        >
        <RouterLink to="/scontrini" class="nav-link" active-class="active"
          ><ReceiptText :size="18" />Scontrini</RouterLink
        >
        <RouterLink to="/prodotti" class="nav-link" active-class="active"
          ><Package :size="18" />Prodotti</RouterLink
        >
        <RouterLink to="/da-rivedere" class="nav-link" active-class="active"
          ><ListChecks :size="18" />Da rivedere<span
            v-if="pending.length"
            class="nav-count"
            >{{ pending.length }}</span
          ></RouterLink
        >
      </nav>
    </aside>
    <div class="main-shell">
      <main>
        <div v-if="error" class="alert error" role="alert">
          {{ error }}
          <button class="text-button" @click="reload">Riprova</button>
        </div>
        <div v-if="notice" class="alert success" role="status">
          {{ notice
          }}<button
            class="icon-button"
            aria-label="Chiudi notifica"
            @click="notice = ''"
          >
            <X :size="16" />
          </button>
        </div>
        <div v-if="loading" class="loading-state">Apro il tuo archivio…</div>
        <RouterView v-else />
      </main>
    </div>
  </div>
</template>
