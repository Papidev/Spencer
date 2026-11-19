<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Search, Pencil, Package } from "lucide-vue-next";
import { dateLabel, money } from "../api";
import { useProducts } from "../useProducts";
import ProductEditor from "../components/ProductEditor.vue";
import Chart from "../components/Chart.vue";
import ProductIdentity from "../components/ProductIdentity.vue";
import { productSearchLabel, useProductSearch } from "../useProductSearch";

const {
  state,
  products,
  search,
  category,
  knownOnly,
  order,
  sortColumns,
  sortBy,
  selected,
  selectedProduct,
  comparable,
  rows,
  history,
  option,
} = useProducts();
const route = useRoute();
const editing = ref<number | null>(null);
const { waiting, categorizing, available, unidentified, search: searchDetails, busy } = useProductSearch();
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
  <div class="search-progress" role="status">
    <p v-if="waiting">Ricerca dettagli: {{ waiting }} {{ waiting === 1 ? 'prodotto in lavorazione' : 'prodotti in lavorazione' }}. Puoi continuare a usare Spencer.</p>
    <p v-else>Nome, foto e formato cercati sul web con IA locale.</p>
    <p v-if="categorizing">Categorie IA: {{ categorizing }} {{ categorizing === 1 ? 'prodotto in lavorazione' : 'prodotti in lavorazione' }}.</p>
    <p v-if="unidentified">
      {{ unidentified }} {{ unidentified === 1 ? "prodotto non identificato" : "prodotti non identificati" }}.
      Puoi correggere i dettagli con il pulsante Modifica o riprovare la ricerca dal singolo prodotto.
    </p>
    <button v-if="available" class="button small" :disabled="busy" @click="searchDetails">
      Cerca dettagli per {{ available }} prodotti
    </button>
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
      <option value="spending-asc">Spesa minore</option>
      <option value="visits">Più ricorrenti</option>
      <option value="visits-asc">Meno ricorrenti</option>
      <option value="name-asc">Prodotto: A–Z</option>
      <option value="name">Prodotto: Z–A</option>
      <option value="category-asc">Categoria: A–Z</option>
      <option value="category">Categoria: Z–A</option>
      <option value="kind-asc">Tipo: A–Z</option>
      <option value="kind">Tipo: Z–A</option>
    </select>
  </div>
  <label class="checkbox-label">
    <input v-model="knownOnly" type="checkbox" />Solo prodotti conosciuti dall’IA
  </label>
  <section v-if="selected && history.length" class="panel product-history">
    <div class="panel-heading">
      <div>
        <h2>{{ selectedProduct?.name }}</h2>
      </div>
      <button class="text-button" @click="selected = null">Chiudi</button>
    </div>
    <Chart
      v-if="comparable"
      :option="option"
      label="Prezzi pagati: acquisti a prezzo pieno e in promozione"
    />
    <p v-if="comparable" class="panel-footnote">
      Prezzo medio per riga, esclusi buoni e benefici sullo scontrino. “Prezzo
      pieno” indica che non è riportato uno sconto sul prodotto. Verifica che
      formato e quantità siano gli stessi; non è un confronto al kg o al litro.
    </p>
    <p v-else class="panel-footnote">
      {{ selectedProduct?.kind === "variable_weight"
        ? "Prodotto a peso variabile: le confezioni possono avere quantità diverse. La spesa degli acquisti non è un confronto dei prezzi."
        : "Tipo di prodotto da determinare: il confronto dei prezzi sarà disponibile dopo la conferma di un formato fisso." }}
      Importi esclusi buoni e benefici sullo scontrino.
    </p>
    <div class="table-wrap">
      <table aria-label="Storico acquisti del prodotto">
        <thead>
          <tr>
            <th>Data</th>
            <th>Acquisto</th>
            <th>Righe</th>
            <th class="align-right">{{ comparable ? "Prezzo pagato per riga" : "Spesa acquisti" }}</th>
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
                  money(comparable ? entry.gross / entry.count : entry.gross)
                }}</del
                >{{ money(comparable ? entry.net / entry.count : entry.net) }}</template
              ><span v-else>Da verificare</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
  <section class="panel">
    <div class="table-wrap">
      <table class="products-table" aria-label="Prodotti">
        <thead>
          <tr>
            <th
              v-for="column in sortColumns"
              :key="column.key"
              :class="{ 'align-right': column.key === 'spending' }"
              :aria-sort="order === `${column.key}-asc` ? 'ascending' : order === column.key ? 'descending' : 'none'"
            >
              <button class="sort-button" @click="sortBy(column.key)">
                {{ column.label }}
                <span aria-hidden="true">{{ order === `${column.key}-asc` ? '↑' : order === column.key ? '↓' : '↕' }}</span>
              </button>
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in rows" :key="product.id">
            <td>
              <button class="table-button" @click="selected = product.id">
                <ProductIdentity :product="product" :original="state.aliases.filter((alias) => alias.product_id === product.id).map((alias) => alias.label).join(' · ')" />
                <small>{{ productSearchLabel(product) }}</small>
              </button>
              <small v-if="product.search_error" class="text-error">{{ product.search_error }}</small>
            </td>
            <td data-label="Categoria">
              {{
                state.categories.find((item) => item.id === product.category_id)
                  ?.name ?? "Non categorizzato"
              }}
            </td>
            <td data-label="Tipo">{{ product.kind === "fixed" ? "Formato fisso" : product.kind === "variable_weight" ? "Peso variabile / sfuso" : "Da determinare" }}</td>
            <td data-label="Visite con acquisto">{{ product.visits }}</td>
            <td class="align-right number" data-label="Spesa totale">{{ money(product.amount) }}</td>
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
            ? "Prova un altro nome o modifica i filtri."
            : "I prodotti compariranno dopo il primo scontrino."
        }}
      </p>
    </div>
  </section>
  <ProductEditor v-if="editing" :product-id="editing" @close="editing = null" />
</template>
