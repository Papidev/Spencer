import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import "./style.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: () => import("./pages/Overview.vue") },
    { path: "/scontrini", component: () => import("./pages/Receipts.vue") },
    { path: "/prodotti", component: () => import("./pages/Products.vue") },
    { path: "/da-rivedere", component: () => import("./pages/Review.vue") },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

createApp(App).use(router).mount("#app");
