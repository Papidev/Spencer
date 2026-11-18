<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { X, Unlink, ArrowRight } from "lucide-vue-next";
import { useSpending } from "../store";
import ProductImage from "./ProductImage.vue";
import { productSearchLabel } from "../useProductSearch";

const props = defineProps<{ productId: number }>();
const emit = defineEmits<{ close: [] }>();
const { state, products, mutate, busy, error } = useSpending();
const product = computed(() =>
  state.value.products.find((product) => product.id === props.productId)!,
);
const name = ref(product.value.name);
const categoryId = ref(product.value.category_id);
const brand = ref(product.value.brand ?? "");
const kind = ref(product.value.kind ?? "unknown");
const packSize = ref(product.value.pack_size ?? "");
const imageUrl = ref(product.value.image_url ?? "");
const initial = {
  name: name.value,
  category_id: categoryId.value,
  brand: brand.value,
  pack_size: packSize.value,
  kind: kind.value,
  image_url: imageUrl.value,
};
const replaceManual = ref(false);
const targets = ref<Record<number, number | null>>({});
const dialog = ref<HTMLDialogElement>();
const aliases = computed(() =>
  state.value.aliases.filter((alias) => alias.product_id === props.productId),
);
onMounted(() => dialog.value?.showModal());
const save = async () => {
  if (
    await mutate(`/products/${props.productId}`, "PATCH", {
      ...Object.fromEntries(
        Object.entries({
          name: name.value,
          category_id: categoryId.value,
          brand: brand.value,
          pack_size: packSize.value,
          kind: kind.value,
          image_url: imageUrl.value,
        }).filter(([key, value]) => value !== initial[key as keyof typeof initial]),
      ),
      ...(!product.value.reviewed
        ? { name: name.value, category_id: categoryId.value }
        : {}),
      reviewed: true,
    })
  )
    emit("close");
};
</script>

<template>
  <dialog
    ref="dialog"
    class="editor-dialog"
    aria-labelledby="editor-title"
    @close="emit('close')"
  >
    <div class="panel-heading">
      <div>
        <h2 id="editor-title">Rivedi prodotto</h2>
      </div>
      <button class="icon-button" aria-label="Chiudi" @click="emit('close')">
        <X :size="20" />
      </button>
    </div>
    <div class="product-research">
      <ProductImage :product-id="product.id" :url="product.image_url" :name="product.name" />
      <div>
        <p>{{ productSearchLabel(product) }}</p>
        <p v-if="product.search_error" class="text-error" role="status">
          {{ product.search_error }}
        </p>
        <a
          v-if="product.source_url"
          :href="product.source_url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-button"
          >Apri la fonte dei dettagli</a
        >
      </div>
    </div>
    <form class="editor-form" @submit.prevent="save">
      <p v-if="error" class="text-error" role="alert">{{ error }}</p>
      <label
        >Nome del prodotto<input
          v-model="name"
          required
          maxlength="160"
          autofocus /></label
      ><label
        >Categoria<select v-model="categoryId">
          <option :value="null">Non categorizzato</option>
          <option
            v-for="category in state.categories"
            :key="category.id"
            :value="category.id"
          >
            {{ category.name }}
          </option>
        </select></label
      >
      <label>Tipo di prodotto<select v-model="kind">
        <option value="unknown">Da determinare</option>
        <option value="fixed">Formato fisso</option>
        <option value="variable_weight">Peso variabile / sfuso</option>
      </select></label>
      <p class="muted">Il confronto dei prezzi è disponibile solo per lo stesso articolo in formato fisso. Per peso variabile o tipo da determinare mostriamo la spesa degli acquisti.</p>
      <label>Marca<input v-model="brand" maxlength="160" /></label>
      <label
        >Formato<input
          v-model="packSize"
          maxlength="160"
          placeholder="Es. 190 g oppure 6 × 125 g"
      /></label>
      <label
        >URL dell’immagine<input
          v-model="imageUrl"
          type="url"
          maxlength="2048"
          placeholder="https://…"
      /></label>
      <p class="muted">
        La correzione si applica anche agli acquisti passati e alle future
        descrizioni già associate. I campi corretti manualmente non saranno
        sovrascritti dall’IA.
      </p>
      <button
        class="button primary"
        type="submit"
        :disabled="busy || !name.trim()"
      >
        Salva e conferma
      </button>
    </form>
    <div class="alias-section">
      <h3>Ricerca automatica</h3>
      <label class="checkbox-label"
        ><input v-model="replaceManual" type="checkbox" />Sostituisci anche i
        dettagli corretti manualmente</label
      >
      <button
        class="button small"
        :disabled="busy || ['pending', 'running'].includes(product.search_status ?? '')"
        @click="
          mutate(`/products/${productId}/search`, 'POST', {
            replace_manual: replaceManual,
          }).then((ok) => { if (ok) emit('close'); })
        "
      >Cerca di nuovo</button>
      <p class="muted">
        La ricerca parte dalle descrizioni originali dello scontrino.
        Ripetere la stessa ricerca potrebbe non trovare nuovi risultati.
        Puoi correggere i dettagli manualmente; il nome corretto non cambia la ricerca.
        Salva prima eventuali modifiche al modulo.
      </p>
    </div>
    <div class="alias-section">
      <h3>Descrizioni sullo scontrino</h3>
      <p class="muted">
        Associa a un altro prodotto solo se sei sicuro che sia lo stesso
        articolo e, per i prodotti in formato fisso, lo stesso formato. Puoi separarlo di nuovo.
      </p>
      <div v-for="alias in aliases" :key="alias.id" class="alias-row">
        <strong>{{ alias.label }}</strong>
        <div class="alias-actions">
          <select
            v-model="targets[alias.id]"
            :aria-label="`Associa ${alias.label} a un prodotto`"
          >
            <option :value="undefined">Scegli prodotto esistente…</option>
            <option
              v-for="other in products.filter((item) => item.id !== productId)"
              :key="other.id"
              :value="other.id"
            >
              {{ other.name }}
            </option></select
          ><button
            class="icon-button"
            :disabled="!targets[alias.id] || busy"
            :aria-label="`Conferma associazione ${alias.label}`"
            @click="
              mutate(`/aliases/${alias.id}`, 'PATCH', {
                product_id: targets[alias.id],
              }).then((ok) => {
                if (ok && !aliases.length) emit('close');
              })
            "
          >
            <ArrowRight :size="17" /></button
          ><button
            class="icon-button"
            :disabled="busy"
            :aria-label="`Separa ${alias.label} in un nuovo prodotto`"
            @click="
              mutate(`/aliases/${alias.id}`, 'PATCH', {
                product_id: null,
              }).then((ok) => {
                if (ok && !aliases.length) emit('close');
              })
            "
          >
            <Unlink :size="16" />
          </button>
        </div>
      </div>
    </div>
  </dialog>
</template>
