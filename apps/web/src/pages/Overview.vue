<script setup lang="ts">
import { Wallet, ReceiptText, ArrowRight } from "lucide-vue-next";
import { useOverview } from "../useOverview";
import { useSpending } from "../store";
import { dateLabel, money } from "../api";
import Chart from "../components/Chart.vue";
import ImportReceipts from "../components/ImportReceipts.vue";

const { state, pending } = useSpending();
const {
  period,
  months,
  receipts,
  lines,
  paid,
  categoryTotal,
  topProducts,
  categories,
  monthlyOption,
} = useOverview();
</script>

<template>
  <div class="page-heading">
    <div>
      <h1>Panoramica</h1>
    </div>
    <label class="period-select"
      ><span class="visually-hidden">Periodo</span
      ><select v-model="period">
        <option value="all">Tutto il periodo</option>
        <option v-for="month in months" :key="month" :value="month">
          {{
            new Intl.DateTimeFormat("it-IT", {
              month: "long",
              year: "numeric",
            }).format(new Date(`${month}-01T12:00:00`))
          }}
        </option>
      </select></label
    >
  </div>
  <ImportReceipts />
  <div class="stat-grid">
    <article class="stat-card featured">
      <div class="stat-top">Esborso effettivo<Wallet :size="18" /></div>
      <strong>{{ money(paid) }}</strong><span
        >Al netto di buoni e benefici di pagamento</span
      >
    </article>
    <article class="stat-card">
      <div class="stat-top">Scontrini importati<ReceiptText :size="18" /></div>
      <strong
        >{{ receipts.length.toString().padStart(2, "0")
        }}<small>{{ lines.length }} articoli</small></strong
      ><span>Solo acquisti riconciliati al centesimo</span>
    </article>
  </div>
  <div
    v-if="!state.receipts.some((receipt) => receipt.status === 'imported')"
    class="empty-state panel"
  >
    <h2>Nessuno scontrino importato</h2>
    <p>Carica uno scontrino PDF Esselunga per iniziare.</p>
  </div>
  <template v-else>
    <div class="dashboard-grid">
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>Esborso mensile</h2>
          </div>
          <span class="tag">Mensile</span>
        </div>
        <Chart
          :option="monthlyOption"
          label="Esborso effettivo mensile in euro"
        />
        <p class="panel-footnote">
          Ogni mese include solo gli scontrini caricati. I mesi incompleti non
          sono previsioni.
        </p>
      </section>
      <section class="panel category-panel">
        <div class="panel-heading">
          <div>
            <h2>Per categoria</h2>
          </div>
        </div>
        <div v-if="!categories.length" class="inline-empty">
          Nessun acquisto in questo periodo.
        </div>
        <div
          v-for="[category, amount] in categories"
          :key="category"
          class="category-row"
        >
          <div>
            <span>{{ category }}</span><strong>{{ money(amount) }}</strong>
          </div>
          <meter
            :value="amount"
            :max="categoryTotal || 1"
            :aria-label="category"
          ></meter>
        </div>
        <RouterLink
          v-if="pending.length"
          to="/da-rivedere"
          class="review-prompt"
          ><span>{{ pending.length }} prodotti da rivedere</span
          ><ArrowRight :size="17"
        /></RouterLink>
        <p class="panel-footnote">
          Importi dopo gli sconti prodotto, prima dei buoni.
        </p>
      </section>
    </div>
    <div class="dashboard-grid bottom-grid">
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>Dove spendi di più</h2>
          </div>
          <RouterLink to="/prodotti" class="text-link"
            >Tutti i prodotti <ArrowRight :size="15"
          /></RouterLink>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Prodotto</th>
                <th>Visite</th>
                <th class="align-right">Totale</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(product, index) in topProducts.slice(0, 5)"
                :key="product.id"
              >
                <td>
                  <RouterLink
                    :to="`/prodotti?prodotto=${product.id}`"
                    class="product-link"
                    ><span class="rank">{{
                      String(index + 1).padStart(2, "0")
                    }}</span
                    ><span
                      ><strong>{{ product.name }}</strong
                      ><small>{{ product.category }}</small></span
                    ></RouterLink
                  >
                </td>
                <td>{{ product.visits.size }}</td>
                <td class="align-right number">{{ money(product.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>Ultimi scontrini</h2>
          </div>
          <RouterLink to="/scontrini" class="text-link"
            >Vedi tutti <ArrowRight :size="15"
          /></RouterLink>
        </div>
        <div
          v-for="receipt in receipts.slice(0, 4)"
          :key="receipt.id"
          class="recent-receipt"
        >
          <span class="receipt-icon"><ReceiptText :size="20" /></span>
          <div>
            <strong>{{ receipt.retailer }}</strong><small
              >{{ dateLabel(receipt.date) }} ·
              {{ receipt.line_count }} articoli</small
            >
          </div>
          <strong class="number">{{ money(receipt.paid_cents) }}</strong>
        </div>
        <p class="panel-footnote">
          Prezzi osservati nei tuoi acquisti, non un listino aggiornato.
        </p>
      </section>
    </div>
  </template>
</template>
