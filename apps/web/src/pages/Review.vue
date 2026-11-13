<script setup lang="ts">
import { computed, ref } from "vue";
import { CheckCheck, Plus, Search } from "lucide-vue-next";
import { useSpending } from "../store";
import ReviewRow from "../components/ReviewRow.vue";
import ProductEditor from "../components/ProductEditor.vue";

const { state, pending, mutate, busy } = useSpending();
const editing = ref<number | null>(null);
const search = ref("");
const categoryName = ref("");
const renameId = ref<number | null>(null);
const renameName = ref("");
const rows = computed(() =>
  pending.value.filter((product) =>
    product.name
      .toLocaleLowerCase("it")
      .includes(search.value.toLocaleLowerCase("it")),
  ),
);
</script>

<template>
  <div class="page-heading">
    <div>
      <h1>Da rivedere</h1>
    </div>
    <span class="tag">{{ pending.length }} da rivedere</span>
  </div>
  <div class="info-note">
    Gli acquisti sono già inclusi nei totali. Quelli senza categoria compaiono
    come “Non categorizzato”. Confermare una descrizione non identifica
    automaticamente marca e formato.
  </div>
  <label class="search-field review-search"
    ><Search :size="18" /><input
      v-model="search"
      placeholder="Cerca tra i prodotti da rivedere…"
      aria-label="Cerca tra i prodotti da rivedere"
  /></label>
  <section class="panel">
    <div v-if="!rows.length" class="empty-state">
      <CheckCheck :size="34" />
      <h2>{{ pending.length ? "Nessun risultato." : "Tutto in ordine." }}</h2>
      <p>
        {{
          pending.length
            ? "Prova un’altra descrizione."
            : "I nuovi prodotti da confermare compariranno qui dopo un’importazione."
        }}
      </p>
    </div>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Nome leggibile / descrizione originale</th>
            <th>Categoria</th>
            <th>Conferma o associa</th>
          </tr>
        </thead>
        <tbody>
          <ReviewRow
            v-for="product in rows"
            :key="product.id"
            :product="product"
            :categories="state.categories"
            :labels="
              state.aliases
                .filter((alias) => alias.product_id === product.id)
                .map((alias) => alias.label)
            "
            @edit="editing = $event"
          />
        </tbody>
      </table>
    </div>
  </section>
  <section class="panel categories-editor">
    <div class="panel-heading">
      <div>
        <h2>Categorie</h2>
      </div>
    </div>
    <div class="category-chips">
      <button
        v-for="category in state.categories"
        :key="category.id"
        class="category-chip"
        @click="
          renameId = category.id;
          renameName = category.name;
        "
      >
        {{ category.name }} <span>↗</span>
      </button>
    </div>
    <form
      v-if="renameId"
      class="inline-form"
      @submit.prevent="
        mutate(`/categories/${renameId}`, 'PATCH', { name: renameName }).then(
          (ok) => {
            if (ok) renameId = null;
          },
        )
      "
    >
      <input
        v-model="renameName"
        aria-label="Nuovo nome categoria"
        required
        maxlength="80"
      /><button class="button small primary" :disabled="busy">Salva nome</button
      ><button type="button" class="text-button" @click="renameId = null">
        Annulla
      </button>
    </form>
    <form
      class="inline-form"
      @submit.prevent="
        mutate('/categories', 'POST', { name: categoryName }).then((ok) => {
          if (ok) categoryName = '';
        })
      "
    >
      <input
        v-model="categoryName"
        aria-label="Nome nuova categoria"
        placeholder="Una nuova categoria…"
        required
        maxlength="80"
      /><button
        class="button small light"
        :disabled="busy || !categoryName.trim()"
      >
        <Plus :size="16" />Aggiungi
      </button>
    </form>
  </section>
  <ProductEditor v-if="editing" :product-id="editing" @close="editing = null" />
</template>
