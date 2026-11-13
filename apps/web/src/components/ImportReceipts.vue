<script setup lang="ts">
import { ref } from "vue";
import { FileUp, LoaderCircle } from "lucide-vue-next";
import { request } from "../api";
import { useSpending } from "../store";

const { reload, notice } = useSpending();
const input = ref<HTMLInputElement>();
const importing = ref(false);
const dragging = ref(false);
const results = ref<{ name: string; message: string; failed: boolean }[]>([]);

const upload = async (files: FileList | null) => {
  if (!files?.length || importing.value) return;
  importing.value = true;
  results.value = [];
  for (const file of Array.from(files)) {
    try {
      if (file.size > 15 * 1024 * 1024)
        throw new Error("Il PDF supera il limite di 15 MB.");
      const form = new FormData();
      form.append("file", file);
      const result = await request<{
        status: string;
        error?: string;
        line_count?: number;
      }>("/receipts", { method: "POST", body: form });
      results.value.push({
        name: file.name,
        message:
          result.status === "duplicate"
            ? "Già presente, nessun duplicato creato."
            : result.status === "failed"
              ? result.error!
              : result.line_count === 1
                ? "1 articolo importato."
                : `${result.line_count} articoli importati.`,
        failed: result.status === "failed",
      });
    } catch (caught) {
      results.value.push({
        name: file.name,
        message:
          caught instanceof Error
            ? caught.message
            : "Importazione non riuscita.",
        failed: true,
      });
    }
  }
  await reload();
  importing.value = false;
  if (input.value) input.value.value = "";
  notice.value = "Importazione terminata. Controlla l’esito di ogni file.";
};
</script>

<template>
  <section
    class="import-zone"
    :class="{ dragging }"
    aria-label="Importa scontrini"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="
      dragging = false;
      upload($event.dataTransfer?.files ?? null);
    "
  >
    <div class="import-icon">
      <LoaderCircle v-if="importing" class="spin" :size="24" /><FileUp
        v-else
        :size="24"
      />
    </div>
    <div class="import-copy">
      <h3>
        {{ importing ? "Importazione in corso…" : "Importa scontrini" }}
      </h3>
      <p>Trascina qui i PDF digitali Esselunga. Massimo 15 MB per file.</p>
    </div>
    <button class="button light" :disabled="importing" @click="input?.click()">
      {{ importing ? "Importazione…" : "Carica PDF" }}
    </button>
    <input
      ref="input"
      class="visually-hidden"
      type="file"
      accept="application/pdf,.pdf"
      multiple
      aria-label="Seleziona scontrini PDF"
      :disabled="importing"
      @change="upload(($event.target as HTMLInputElement).files)"
    />
  </section>
  <ul v-if="results.length" class="import-results" aria-live="polite">
    <li
      v-for="(result, index) in results"
      :key="index"
      :class="{ 'text-error': result.failed }"
    >
      <strong>{{ result.name }}</strong> · {{ result.message }}
    </li>
  </ul>
</template>
