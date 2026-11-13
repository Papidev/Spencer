<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { X, Unlink, ArrowRight } from "lucide-vue-next";
import { useSpending } from "../store";

const props = defineProps<{ productId: number }>();
const emit = defineEmits<{ close: [] }>();
const { state, products, mutate, busy, error } = useSpending();
const product = computed(() =>
  state.value.products.find((product) => product.id === props.productId)!,
);
const name = ref(product.value.name);
const categoryId = ref(product.value.category_id);
const targets = ref<Record<number, number | null>>({});
const dialog = ref<HTMLDialogElement>();
const aliases = computed(() =>
  state.value.aliases.filter((alias) => alias.product_id === props.productId),
);
onMounted(() => dialog.value?.showModal());
const save = async () => {
  if (
    await mutate(`/products/${props.productId}`, "PATCH", {
      name: name.value,
      category_id: categoryId.value,
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
      <p class="muted">
        La correzione si applica anche agli acquisti passati e alle future
        descrizioni già associate.
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
      <h3>Descrizioni sullo scontrino</h3>
      <p class="muted">
        Associa a un altro prodotto solo se sei sicuro che sia lo stesso
        articolo e formato. Puoi separarlo di nuovo.
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
