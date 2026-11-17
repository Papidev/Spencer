# Spencer

A local app for supermarket receipts and grocery spending, with an Italian interface.

- Import digital Esselunga PDF receipts.
- Track actual out-of-pocket spending by month.
- Review product names and categories; reuse confirmed matches on future imports.
- Automatically find readable product names, brands, pack sizes and photos using local Ollama and web search.
- See recurring products and when you bought them at full price or on promotion.

## Stack

pnpm + Turborepo monorepo:

- `apps/web`: Vue, TypeScript, Vite, Vue Router, Apache ECharts.
- `apps/api`: Python, FastAPI, pdfplumber, SQLAlchemy, SQLite, Alembic. Python dependencies are managed with uv.

## Local setup

Requires Node.js 22.12+ or 24+, pnpm 10.20, and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
pnpm install --frozen-lockfile
cd apps/api
uv sync --locked --python 3.12
cd ../..
pnpm dev
```

Open [localhost:5173](http://127.0.0.1:5173). The API runs on localhost:8000, with API documentation at [localhost:8000/docs](http://127.0.0.1:8000/docs).

`pnpm dev` starts both apps and applies database migrations. After changing Python dependencies, run `uv sync --locked` inside `apps/api` again. Vite polls source changes to support environments without native file watcher events.

### Local product research

Requires a running Ollama instance with the local `qwen3.5:9b` model, and Docker running for SearXNG. No paid AI or search services are used.

```sh
# Download the model once if it is not installed, then keep Ollama running.
ollama pull qwen3.5:9b
pnpm search:start
pnpm dev
```

`search:start` generates a local instance secret and starts the pinned SearXNG container on [localhost:8088](http://127.0.0.1:8088). Stop it with `pnpm search:stop`. The container is bound only to localhost; it is not configured as a public search service.

Clear product words in receipt descriptions (for example, latte or focaccia) assign a category independently of exact product identification, without web search or Ollama. This also fills missing categories on app startup. Existing categories and manual category corrections, including an explicitly empty category, are preserved. Ambiguous descriptions remain uncategorized; assigning a category does not confirm the product identity.

New products enter a persistent background queue after import. In **Prodotti**, **Cerca dettagli** queues products not yet searched or whose search service failed; products with no match are shown as **Non identificato** and can be corrected manually or retried individually using **Cerca di nuovo** in the product editor. Searches run one product at a time. Successful matches are applied and confirmed automatically, including a category from your existing list. Photos and source links come from retrieved pages, not URLs invented by the model. Original receipt descriptions and purchase amounts are preserved. Unknown details stay empty; an unsuccessful match keeps the original name.

You can edit name, category, brand, pack size, product type and image URL. Corrected fields are protected against later searches. Only selecting **Sostituisci anche i dettagli corretti manualmente** explicitly removes that protection. The editor shows the source and whether the confirmation was automatic.

Product photos are downloaded on first display, validated as PNG/JPEG/GIF/WebP (up to 4 MB) and cached in `data/product-images/`. Local Ollama vision must also recognize a visible retail package before the image is shown. Loose food, recipe photos and uncertain images show a placeholder. This check also applies to previously cached photos; its verdict is cached to avoid repeating inference. If the model is unavailable, the photo remains hidden until it can be checked. The browser loads approved photos through Spencer's API; the original image URL remains editable.

The model runs locally, but the product search words are sent to search engines and public product pages. PDFs, dates, receipt prices and personal receipt information are not sent. Search engines can block or limit requests; images can be missing or unavailable. A matching brand/name is not proof of the exact variant or pack size, so automatic results remain correctable.

Failed requests retry up to three times, with pauses; failed or interrupted work resumes when the API restarts, and you can retry manually. Keep a single API server process for the single local worker. Existing products are searched only when you queue them; importing another receipt reuses existing associations.

Optional environment variables (export them before `pnpm dev`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `SPENCER_ENRICHMENT_ENABLED` | `true` | Set `false` to stop background research. |
| `SPENCER_OLLAMA_MODEL` | `qwen3.5:9b` | Installed local model; cloud aliases are rejected. |
| `SPENCER_OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint. |
| `SPENCER_SEARCH_URL` | `http://127.0.0.1:8088` | Local SearXNG endpoint. |

Both service endpoints must be on localhost. Restart the API after changing these settings.

## Usage

1. Upload one or more Esselunga PDFs with selectable text, up to 15 MB and 10 pages each. Scanned receipts and photos are not supported yet.
2. Open **Da rivedere** to confirm readable names and assign categories. Unreviewed purchases are already included in spending totals.
3. Open **Prodotti** and select a product for its price history. Use the editor to link or separate receipt descriptions; only link identical products and pack sizes.
4. Open **Scontrini** to view purchase lines, the original PDF, or delete a receipt.

Duplicate receipts are skipped. Receipts with unrecognised lines or mismatched totals remain visible as failed imports and are excluded from analytics.

Products distinguish **Formato fisso**, **Peso variabile / sfuso**, and **Da determinare**. Only fixed-format products show price comparisons; variable-weight and unknown products retain spending and purchase history, showing total spending for each group of receipt lines rather than average package prices. Existing and newly imported products start as unknown. Product research can classify them on the next search, and manual corrections are protected. A visible package does not imply a fixed quantity. Weight and unit prices are not recorded, so €/kg comparisons are not available.

The overview shows **Esborso effettivo**, including receipt-wide vouchers and payment benefits. Product/category amounts reflect prices after product discounts, before receipt-wide benefits, which cannot be assigned to a specific product. Product history distinguishes full-price and promotional purchases; “full price” means no explicit product discount was printed. Mixed purchases on the same receipt remain separate. Prices are averages per receipt line, not €/kg or €/litre comparisons or current supermarket prices.

## Checks

```sh
pnpm test
pnpm check
pnpm lint
pnpm build
```

Tests use fictional PDFs, a real temporary SQLite database, and MSW for frontend HTTP responses. Three optional private-receipt regression cases are skipped unless `SPENCER_TEST_RECEIPTS` points to an untracked JSON manifest. Each entry contains `file` (relative to the manifest), `line_count`, `total_cents`, and `paid_cents`. Keep the manifest and original receipts outside Git.

## Local data

`data/spencer.sqlite3` stores purchases and product matches; `data/receipts/` stores uploaded PDFs. Both are excluded from Git. No receipts, databases, or credentials belong in the repository.

To back up or restore, stop the app and copy the entire `data/` directory. Set `SPENCER_DATA_DIR` to an absolute path before starting the app to use a different location.

This version runs on localhost without authentication. AI inference uses local Ollama; product research accesses external search engines and public product pages.
