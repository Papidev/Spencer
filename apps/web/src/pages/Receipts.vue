<script setup lang="ts">
import { computed, ref } from "vue";
import {
  ExternalLink,
  Trash2,
  ReceiptText,
  Check,
  AlertCircle,
} from "lucide-vue-next";
import ImportReceipts from "../components/ImportReceipts.vue";
import { useSpending } from "../store";
import { dateLabel, money } from "../api";
import RetailerImage from "../components/RetailerImage.vue";
import ProductIdentity from "../components/ProductIdentity.vue";

const { state, purchases, mutate, busy } = useSpending();
const selected = ref<number | null>(null);
const deleting = ref<number | null>(null);
const detail = computed(() =>
  state.value.receipts.find((receipt) => receipt.id === selected.value),
);
const receiptLines = computed(() =>
  purchases.value.filter((line) => line.receipt_id === selected.value),
);
</script>

<template>
  <div class="page-heading">
    <div>
      <h1>Scontrini</h1>
    </div>
    <span class="tag">{{ state.receipts.length }} documenti</span>
  </div>
  <ImportReceipts />
  <section class="panel">
    <div class="panel-heading">
      <h2>Archivio acquisti</h2>
      <span class="muted">Esselunga · PDF digitali</span>
    </div>
    <div v-if="!state.receipts.length" class="empty-state">
      <ReceiptText :size="32" />
      <h2>Nessuno scontrino importato</h2>
      <p>Carica uno o più PDF per creare il tuo archivio.</p>
    </div>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Negozio / documento</th>
            <th>Data</th>
            <th>Articoli</th>
            <th>Stato</th>
            <th class="align-right">Totale</th>
            <th><span class="visually-hidden">Azioni</span></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="receipt in state.receipts" :key="receipt.id"
            ><tr>
              <td>
                <button
                  class="table-button"
                  @click="
                    selected = selected === receipt.id ? null : receipt.id
                  "
                >
                  <span class="receipt-identity">
                  <RetailerImage v-if="receipt.status === 'imported'" :retailer="receipt.retailer" />
                  <span><strong>{{
                    receipt.status === "imported"
                      ? receipt.retailer
                      : receipt.filename
                  }}</strong><small>{{
                    receipt.store || "Importazione da controllare"
                  }}</small></span></span>
                </button>
              </td>
              <td>{{ dateLabel(receipt.date) }}</td>
              <td>{{ receipt.line_count || "—" }}</td>
              <td>
                <span class="status-badge" :class="receipt.status"
                  ><Check
                    v-if="receipt.status === 'imported'"
                    :size="12"
                  /><AlertCircle v-else :size="12" />{{
                    receipt.status === "imported"
                      ? "Verificato"
                      : "Da controllare"
                  }}</span
                >
              </td>
              <td class="align-right number">
                {{
                  receipt.status === "imported"
                    ? money(receipt.total_cents)
                    : "—"
                }}
              </td>
              <td>
                <div class="row-actions">
                  <a
                    :href="`/api/receipts/${receipt.id}/pdf`"
                    class="icon-button"
                    target="_blank"
                    rel="noopener"
                    :aria-label="`Apri PDF ${receipt.filename}`"
                    ><ExternalLink :size="16" /></a
                  ><button
                    class="icon-button"
                    :aria-label="`Elimina ${receipt.filename}`"
                    @click="deleting = receipt.id"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="receipt.error">
              <td colspan="6" class="text-error">
                {{ receipt.error }} Puoi correggere il file e importarlo di
                nuovo.
              </td>
            </tr>
            <tr v-if="deleting === receipt.id">
              <td colspan="6">
                <div class="delete-confirm">
                  <span>Eliminare questo scontrino e i suoi acquisti?</span
                  ><button
                    class="button danger small"
                    :disabled="busy"
                    @click="
                      mutate(`/receipts/${receipt.id}`, 'DELETE').then((ok) => {
                        if (ok) deleting = null;
                      })
                    "
                  >
                    Elimina scontrino</button
                  ><button class="text-button" @click="deleting = null">
                    Annulla
                  </button>
                </div>
              </td>
            </tr></template
          >
        </tbody>
      </table>
    </div>
  </section>
  <section v-if="detail" class="panel receipt-detail">
    <div class="panel-heading">
      <div>
        <h2>{{ dateLabel(detail.date) }} · {{ detail.document }}</h2>
      </div>
      <button class="text-button" @click="selected = null">Chiudi</button>
    </div>
    <div class="receipt-summary">
      <span
        >Buoni scontrino
        <strong>{{ money(detail.voucher_cents) }}</strong></span
      ><span
        >Totale <strong>{{ money(detail.total_cents) }}</strong></span
      ><span
        >Esborso <strong>{{ money(detail.paid_cents) }}</strong></span
      >
    </div>
    <div class="payment-list">
      <span v-for="(payment, index) in detail.payments" :key="index"
        >{{ payment.label }}: {{ money(payment.cents) }}</span
      >
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Descrizione originale / prodotto</th>
            <th class="align-right">Prezzo stampato</th>
            <th class="align-right">Sconto</th>
            <th class="align-right">Pagato sul prodotto</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="line in receiptLines" :key="line.id">
            <td>
              <ProductIdentity :product="line.product" :original="line.label" />
              <small v-if="line.discount_label">{{ line.discount_label }}</small>
            </td>
            <td class="align-right">{{ money(line.gross_cents) }}</td>
            <td class="align-right">
              {{ line.discount_cents ? `−${money(line.discount_cents)}` : "—" }}
            </td>
            <td class="align-right number">
              {{ money(line.gross_cents - line.discount_cents) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
