<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Search, Pencil, Package } from "lucide-vue-next";
import { dateLabel, money } from "../api";
import { useProducts } from "../useProducts";
import ProductEditor from "../components/ProductEditor.vue";
import Chart from "../components/Chart.vue";

const {
  state,
  products,
  search,
  category,
  order,
  selected,
  rows,
  history,
  option,
} = useProducts();
const route = useRoute();
const editing = ref<number | null>(null);
watch(
  () => route.query.prodotto,
  (value) => {
    selected.value = Number(value) || null;
  },
  { immediate: true },
);
</script>

<template>
  <div class="page-heading">
    <div>
      <h1>Prodotti</h1>
    </div>
    <span class="tag">{{ products.length }} prodotti</span>
  </div>
  <div class="filters">
    <label class="search-field"
      ><Search :size="18" /><input
        v-model="search"
        placeholder="Cerca un prodotto…"
        aria-label="Cerca un prodotto" /></label
    ><select v-model="category" aria-label="Filtra per categoria">
      <option value="all">Tutte le categorie</option>
      <option value="null">Non categorizzato</option>
      <option
        v-for="item in state.categories"
        :key="item.id"
        :value="String(item.id)"
      >
        {{ item.name }}
      </option></select
    ><select v-model="order" aria-label="Ordina prodotti">
      <option value="spending">Spesa maggiore</option>
      <option value="visits">Più ricorrenti</option>
    </select>
  </div>
  <section v-if="selected && history.length" class="panel product-history">
    <div class="panel-heading">
      <div>
        <h2>{{ products.find((product) => product.id === selected)?.name }}</h2>
      </div>
      <button class="text-button" @click="selected = null">Chiudi</button>
    </div>
    <Chart
      :option="option"
      label="Prezzi pagati: acquisti a prezzo pieno e in promozione"
    />
    <p class="panel-footnote">
      Prezzo medio per riga, esclusi buoni e benefici sullo scontrino. “Prezzo
      pieno” indica che non è riportato uno sconto sul prodotto. Verifica che
      formato e quantità siano gli stessi; non è un confronto al kg o al litro.
    </p>
    <div class="table-wrap">
      <table aria-label="Storico acquisti del prodotto">
        <thead>
          <tr>
            <th>Data</th>
            <th>Acquisto</th>
            <th>Righe</th>
            <th class="align-right">Prezzo pagato per riga</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in history" :key="entry.id">
            <td>{{ dateLabel(entry.date) }}</td>
            <td>
              <span
                class="status-badge"
                :class="entry.promotional ? 'promotion' : 'full-price'"
                >{{
                  entry.promotional ? "In promozione" : "Prezzo pieno"
                }}</span
              >
            </td>
            <td>{{ entry.count }}</td>
            <td class="align-right number">
              <template v-if="entry.verified"
                ><del v-if="entry.promotional" class="original-price">{{
                  money(entry.gross / entry.count)
                }}</del
                >{{ money(entry.net / entry.count) }}</template
              ><span v-else>Da verificare</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
  <section class="panel">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Prodotto</th>
            <th>Categoria</th>
            <th>Visite con acquisto</th>
            <th class="align-right">Spesa totale</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in rows" :key="product.id">
            <td>
              <button class="table-button" @click="selected = product.id">
                <strong>{{ product.name }}</strong><small>{{
                  product.reviewed ? "Descrizione confermata" : "Da rivedere"
                }}</small>
              </button>
            </td>
            <td>
              {{
                state.categories.find((item) => item.id === product.category_id)
                  ?.name ?? "Non categorizzato"
              }}
            </td>
            <td>{{ product.visits }}</td>
            <td class="align-right number">{{ money(product.amount) }}</td>
            <td>
              <button
                class="icon-button"
                :aria-label="`Modifica ${product.name}`"
                @click="editing = product.id"
              >
                <Pencil :size="16" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!rows.length" class="empty-state">
      <Package :size="30" />
      <h2>Nessun prodotto trovato.</h2>
      <p>
        {{
          products.length
            ? "Prova un altro nome o una categoria diversa."
            : "I prodotti compariranno dopo il primo scontrino."
        }}
      </p>
    </div>
  </section>
  <ProductEditor v-if="editing" :product-id="editing" @close="editing = null" />
</template>
