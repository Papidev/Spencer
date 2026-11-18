# Collegamento tra scontrini e catalogo Esselunga

Verifica: 16 novembre 2026. Ricerca sulle pagine pubbliche ufficiali; nessun accesso a un account Esselunga e nessuna verifica delle risposte riservate del servizio.

## Risultato

Non è stato individuato un collegamento pubblico documentato che trasformi la descrizione abbreviata di una riga dello scontrino in un identificativo di catalogo, nome completo e immagine. Questo è un limite della verifica, non una prova che il collegamento non esista nei sistemi interni o nelle risposte dell'area personale.

## Cosa confermano le fonti ufficiali

- Le [FAQ Esselunga](https://www.esselunga.it/it-it/servizio-clienti/faq.html), nella sezione Scontrini, indicano che lo scontrino integrale si consulta nell'area personale, in “La Spesa > Scontrini > I tuoi scontrini”, dopo l'attivazione del servizio. Non documentano i campi tecnici delle singole righe, un export strutturato o un collegamento al catalogo.
- Il [comunicato Esselunga del 22 novembre 2024](https://www.esselunga.it/it-it/area-stampa/comunicati/2024/11/esselunga-lancia-la-nuova-versione-dell-app.html) conferma la ricerca dei prodotti in assortimento nell'app, oltre alla consultazione degli scontrini virtuali. Non afferma che le righe degli scontrini siano apribili come schede prodotto né che la ricerca accetti le abbreviazioni dello scontrino.
- La [pagina ufficiale dell'app](https://www.esselunga.it/it-it/servizi-utili/app-esselunga.html) descrive la scansione dei prodotti in Presto Spesa e la consultazione dello scontrino virtuale. L'esistenza di entrambe le funzioni non dimostra che un identificativo articolo sia disponibile nell'esportazione PDF.

## API e limiti

Le ricerche mirate su esselunga.it e spesaonline.esselunga.it non hanno individuato documentazione ufficiale di un'API pubblica per sviluppatori che esponga il collegamento tra scontrini e catalogo. I servizi di terzi che si presentano come “Esselunga API” non costituiscono documentazione Esselunga e non sono stati usati come prova.

La risposta resa disponibile allo strumento web dalla [pagina del supermercato online](https://spesaonline.esselunga.it/commerce/nav/supermercato/) non contiene testo leggibile. Questo esito non consente di valutare da solo il contenuto caricato nel browser o le chiamate effettuate dal sito.

## Verifica necessaria per concludere

Esaminare una riga di uno scontrino nell'area personale autenticata e stabilire se il servizio restituisce, oltre alla descrizione, un codice articolo/EAN o un link alla scheda prodotto. Se presente, verificare su più righe che il codice identifichi esattamente variante e formato nel catalogo. Se resta soltanto la descrizione abbreviata, la ricerca testuale produce candidati e richiede conferma: non è una corrispondenza certa.

## Verifica locale e prova nel browser

- Esaminati i tre PDF originali presenti in `data/receipts/` con pdfplumber: nessuna sequenza numerica di 8–14 cifre nel testo delle righe prodotto, nessun hyperlink e nessuna annotazione PDF. Sono presenti immagini, che non sono state decodificate per ricercare barcode. Quindi non è stato identificato un codice utilizzabile per articolo; non si esclude in assoluto un'informazione contenuta nelle immagini.
- Il parser corrente (`apps/api/src/spencer/parser.py`) estrae descrizione e importi, senza identificativo di catalogo.
- Aperto il catalogo ufficiale in un browser senza sessione autenticata, sia direttamente sia dopo la homepage istituzionale. Rimane una struttura incompleta senza prodotti o ricerca; il log segnala cookie XSRF mancante e inizializzazione fallita. Anche “I miei acquisti” mostra solo la struttura della pagina. È un blocco di questa sessione, non prova che il catalogo richieda sempre login o sia indisponibile ad altri utenti.
- Nessuna associazione o modifica ai dati dei prodotti è stata applicata.

## Esperimento di ricerca dalla descrizione — 16 novembre 2026

Precisazione rispetto alla verifica proposta sopra: i PDF locali sono già stati scaricati dall'area autenticata Esselunga. Che la stessa area esponga ulteriori dati strutturati o identificativi resta un'ipotesi non verificata; il solo accesso all'area personale non garantisce informazioni aggiuntive rispetto ai PDF disponibili.

È stata provata manualmente la ricerca di candidati dalla sola descrizione dello scontrino, confrontando le parole riconoscibili con pagine prodotto sul web. Gli esempi seguenti sono un campione scelto per esplorare la fattibilità, non un benchmark di accuratezza o copertura. Le pagine e i candidati sono stati verificati dall'agente principale; nessuna corrispondenza è stata confermata mediante un identificativo dell'acquisto.

| Descrizione sullo scontrino | Candidato e fonte | Evidenza e limite |
| --- | --- | --- |
| `BAR.PESTO GENOV. 190G` | [Barilla Pesto alla Genovese 190 g](https://www.barilla.com/it-it/prodotti/pesti/pesti/pesto-alla-genovese) | Marca plausibile, tipo e formato coincidono: candidato forte, ancora non confermato. |
| `YOMO FRUT.FR/BA/AL/FB` | [Yomo 8 × 125 g su CoopShop](https://www.coopshop.it/product/yomo-int-fra-ba-alb-fb-8x125g), [scheda Coop a Casa](https://coopacasa.coopetruria.coop.it/yogurt-e-dessert/yogurt-intero/1179700.html) | Marca e abbreviazioni suggeriscono un assortimento di gusti; il formato 8 × 125 g è inferito, non presente nella riga. La seconda pagina presenta un'incongruenza tra il titolo con frutti di bosco e gli ingredienti con ciliegia/amarena: non basta per confermare variante e confezione. |
| `SCOT.C.CASA QUANTOBAS` | [Scottex Quanto Basta](https://www.it.scottex.com/prodotti/carta-casa/scottex-quanto-basta) | La linea è riconoscibile; il numero di rotoli o altro formato della confezione resta ignoto. |
| `RITTER WHITE LEMON` | Ritter Sport Funky White Lemon 100 g; [pagina ufficiale con foto](https://vinnamed.ritter-sport.se/forside/) | Nome distintivo compatibile con il candidato. Il peso di 100 g è inferito, non ricavato dallo scontrino. |

L'esperimento mostra che alcune descrizioni distintive permettono di recuperare candidati utili e immagini di riferimento. Non dimostra che quei candidati siano gli articoli effettivamente acquistati, né che una descrizione generica o abbreviata consenta sempre di distinguere varianti e formati. Non sono stati applicati nomi, immagini o associazioni ai dati locali.

## Fonti tecniche gratuite — 16 novembre 2026

Vincoli di progettazione: Ollama locale con `qwen3.5:9b`, nessun servizio a pagamento; possono uscire dal computer soltanto le parole necessarie a cercare un prodotto. Il modello può proporre termini e confrontare candidati recuperati; non costituisce una fonte per foto o identità certe.

### Open Food Facts

La [documentazione ufficiale](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/) descrive un catalogo alimentare collaborativo riutilizzabile, con dati e foto che possono mancare o essere inesatti. Le letture non richiedono autenticazione; è richiesto uno User-Agent personalizzato nel formato `AppName/Version (ContactEmail)`. Limiti correnti: 10 ricerche/minuto/IP e 15 letture prodotto/minuto/IP; evitare richieste a ogni tasto e conservare i risultati già ottenuti.

Attenzione all'endpoint: `/api/v2/search` applica filtri strutturati, non ricerca libera. La ricerca testuale esiste nel legacy `/cgi/search.pl`; le nuove API v3 non la includono. La documentazione indirizza verso Search-a-licious. Database ODbL, contenuti DbCL, immagini CC BY-SA: mantenere provenienza e attribuzione e valutare gli obblighi di riuso prima di distribuire un catalogo derivato.

Prova minima eseguita senza dati personali nell'ambiente staging ufficiale `world.openfoodfacts.net`: richiesta GET a `/cgi/search.pl` con `search_terms=barilla pesto 190g`, `search_simple=1`, `action=process`, `json=1`, `page_size=5`, campi `code,product_name,brands,quantity,image_front_url,url`, User-Agent identificativo e autenticazione di test pubblica indicata dalla documentazione. HTTP 200, quattro risultati: Calabrese, Genovese senza aglio, basilico/mozzarella e un record “Barilla pesto genovese 190g” senza foto. Tre risultati contenevano `image_front_url`. È una prova dell'accessibilità del canale legacy in staging, non della copertura o dell'affidabilità della produzione. Mostra anche perché nome e peso da soli non confermano una variante.

### Ricerca web generale

- [SearXNG](https://github.com/searxng/searxng) è un metamotore gratuito eseguibile localmente. Espone un'[API HTTP](https://docs.searxng.org/dev/search_api.html) con `/search?q=...&format=json` quando JSON è abilitato. Molte istanze pubbliche lo disabilitano. Richiede un servizio aggiuntivo e dipende comunque dai motori interrogati; la [documentazione](https://docs.searxng.org/own-instance.html) descrive possibili CAPTCHA e blocchi delle istanze pubbliche. Non garantisce ricerca illimitata o stabile e non è stato installato né provato.
- DuckDuckGo documenta [versioni HTML e Lite senza JavaScript](https://duckduckgo.com/duckduckgo-help-pages/features/non-javascript), che sono pagine di ricerca per browser. La loro esistenza non è una garanzia di API JSON, permesso di riuso delle foto o stabilità di un'integrazione che analizzi l'HTML. Non promettere scraping stabile di DuckDuckGo o Google.
- Le [FAQ ufficiali Brave Search API](https://api-dashboard.search.brave.com/documentation/resources/help-feedback) dichiarano che non esiste un piano autonomo gratuito: ci sono crediti mensili, attivazione con carta e chiave API. La stessa pagina limita la conservazione dei risultati. Escluso dalla prima proposta per il vincolo sui servizi a pagamento.

Scelta iniziale più semplice: Open Food Facts per candidati alimentari con nome, formato, foto e fonte, con gestione esplicita di assenza e ambiguità. Per prodotti casa/persona e alimenti mancanti non è stata verificata una fonte gratuita altrettanto semplice e completa: la ricerca web gratuita automatica richiede accettare un componente aggiuntivo o un'integrazione fragile. Non assumere che Open Food Facts copra l'intero assortimento Esselunga. Nessuna integrazione o modifica ai dati applicata.
