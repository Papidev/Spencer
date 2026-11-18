# Ricerca automatica dei dettagli prodotto

Stato: disegno confermato dall’utente e implementato localmente.

## Decisioni concordate

- I risultati della ricerca IA vengono applicati e confermati automaticamente, senza richiedere una conferma manuale preventiva.
- L’utente può correggere manualmente i prodotti successivamente.
- “Confermato” non significa necessariamente verificato da una persona: vedi il glossario.
- Il modello IA deve essere eseguito localmente tramite Ollama.
- Non usare servizi a pagamento, neppure per la ricerca dei prodotti.
- Usare SearXNG locale per la ricerca web. I limiti e i blocchi dei motori a monte restano applicabili; non è garantita una quota o una velocità di ricerca.
- È consentita la ricerca online gratuita sui cataloghi e siti pubblici, usando soltanto le parole del prodotto.
- Quando non emerge un risultato utilizzabile, conservare la descrizione originale e lasciare vuota l’immagine; non inventare dettagli mancanti.
- Le correzioni manuali prevalgono sui risultati automatici successivi, salvo richiesta esplicita di nuova ricerca.
- Dopo ogni importazione, avviare la ricerca per i prodotti nuovi in background senza bloccare l’uso dell’app. Offrire un comando anche per i prodotti già presenti.
- La categorizzazione indipendente usa Ollama locale sulle descrizioni originali, senza regole su parole chiave né ricerca web. Può assegnare una categoria anche ai prodotti non identificati, senza confermarne l’identità. Elabora in background i prodotti senza categoria e protegge le scelte manuali.
- Recuperare nome, marca, formato, foto e fonte; assegnare una categoria tra quelle esistenti, preservando i campi corretti manualmente.
- Tra più candidati compatibili, Ollama sceglie il più plausibile e Spencer lo conferma automaticamente. Conservare la fonte consultabile e lasciare vuoti i dettagli non supportati.
- Se Ollama o la fonte online non sono disponibili, mantenere i prodotti in attesa e riprovare al successivo avvio di Spencer. Offrire anche un pulsante per riprovare subito.
- Mostrare nome riconosciuto e foto nella pagina Prodotti e nel dettaglio degli scontrini, mantenendo visibile la descrizione originale dello scontrino.
- Nell’editor consentire la correzione di nome, categoria, marca, formato e URL dell’immagine; le correzioni manuali restano protette.
- Mostrare soltanto foto con confezione di vendita visibile. Il modello locale verifica l’immagine, incluse quelle già nella cache; foto generiche di alimenti, piatti e casi incerti restano nascosti senza eliminare i dettagli del prodotto o l’URL originale.

## Fatti verificati

- Ollama è raggiungibile localmente e `qwen3.5:9b` è già installato. La qualità sul riconoscimento dei prodotti deve ancora essere provata.
- Docker CLI è installato, ma il daemon non era raggiungibile durante la verifica. Nessuna istanza SearXNG è stata provata localmente.

## Implementazione

1. Provare SearXNG locale e Ollama su descrizioni campione prima di integrare la ricerca: verificare candidati reali, provenienza e disponibilità delle immagini. Nessuna promessa di copertura completa.
2. Aggiungere in modo incrementale i dettagli prodotto, la provenienza delle conferme e dei campi corretti manualmente, e lo stato persistente del lavoro di ricerca. Conservare gli alias originali e i collegamenti agli acquisti.
3. Eseguire i lavori in background, un prodotto alla volta, con tentativi limitati e gestione dei blocchi della fonte. Riutilizzare i risultati, consentire la ripresa dopo un riavvio e offrire ricerca/riprova manuale.
4. Mostrare i dettagli nelle viste concordate e ampliare l’editor. Distinguere conferma automatica e manuale senza chiedere approvazione preventiva per ogni prodotto.
5. Verificare persistenza e ripresa, indisponibilità dei servizi, risultati incompatibili, conferme automatiche e protezione dei campi corretti. Eseguire i controlli del repository appropriati alle modifiche e una prova reale separata dai test automatici.

## Limiti accettati

- Nessun servizio a pagamento o modello cloud.
- La conferma automatica può essere errata e resta correggibile.
- Nessun risultato utilizzabile: descrizione originale e immagine vuota. I dettagli assenti non vengono inventati.
- SearXNG e il modello locale devono essere in esecuzione per completare nuove ricerche. Blocchi dei motori, pagine non accessibili e foto mancanti possono impedire l’arricchimento.

## Verifica locale

- SearXNG eseguito in Docker con API JSON, accessibile soltanto da localhost; immagine container fissata tramite digest.
- Ricerca reale tramite `qwen3.5:9b` su pesto Barilla e carta Scottex: trovati candidati con fonti; recuperata una foto prodotto del pesto. Formato Scottex non supportato dalla fonte lasciato vuoto.
- Prova completa dall’interfaccia sul solo prodotto `BAR.PESTO GENOV. 190G`: risultato persistito, categoria assegnata e conferma automatica visibile. La ricerca resta possibile anche tramite la descrizione originale dopo il cambio del nome.
- Foto servite e memorizzate localmente dall’API dopo verifica del contenuto, del limite di dimensione e delle destinazioni HTTP. Verificata nel browser la foto del pesto dopo un caricamento completo della pagina.
- Confronto con backup locale precedente alla migrazione: scontrini, acquisti, alias e categorie conservati.
- Test automatici isolati dalla rete esterna coprono conferma automatica, correzioni durante una ricerca, risposte tardive, errori e ripresa, risultati mancanti, rifiuto dei modelli cloud, immagini generiche e formati non documentati. Test UI con MSW coprono modifica dei dettagli e nuova ricerca con/senza sostituzione delle correzioni.
- La prova è un campione funzionale, non una misura di accuratezza sul catalogo completo. Gli altri prodotti esistenti non sono stati accodati automaticamente.
