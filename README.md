# Spencer

A local app for supermarket receipts and grocery spending, with an Italian interface.

- Import digital Esselunga PDF receipts.
- Track actual out-of-pocket spending by month.
- Review product names and categories; reuse confirmed matches on future imports.
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

## Usage

1. Upload one or more Esselunga PDFs with selectable text, up to 15 MB and 10 pages each. Scanned receipts and photos are not supported yet.
2. Open **Da rivedere** to confirm readable names and assign categories. Unreviewed purchases are already included in spending totals.
3. Open **Prodotti** and select a product for its price history. Use the editor to link or separate receipt descriptions; only link identical products and pack sizes.
4. Open **Scontrini** to view purchase lines, the original PDF, or delete a receipt.

Duplicate receipts are skipped. Receipts with unrecognised lines or mismatched totals remain visible as failed imports and are excluded from analytics.

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

This version runs on localhost without authentication. No cloud AI or external product catalogue is used.
