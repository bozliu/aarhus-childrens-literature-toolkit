## Modern Stack

| module                | status    | purpose                         | detail                                  |
| --------------------- | --------- | ------------------------------- | --------------------------------------- |
| transformers          | available | modern sentiment backend        | import ok                               |
| sentence_transformers | missing   | embedding and retrieval backend | No module named 'sentence_transformers' |
| bertopic              | missing   | embedding topic modeling        | No module named 'bertopic'              |
| gliner                | missing   | local named entity recognition  | No module named 'gliner'                |
| torch                 | available | accelerated local inference     | import ok                               |
| networkx              | available | entity co-occurrence graphing   | import ok                               |

### Benchmark Framing

| component              | repo_metric                                                   | legacy_2016_baseline                                    | external_reference                              | published_reference_or_sota        | comparability_note                                                                |
| ---------------------- | ------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| Sentiment              | afinn-fallback; mean window score 0.02                        | AFINN cohort means: men -13.76 / women 13.88            | distilbert-base-uncased-finetuned-sst-2-english | Official model card only           | No directly comparable literary benchmark in the local archive.                   |
| Topic modeling         | Guided themes + sklearn LDA; mean dominant topic share 0.844  | topicmodels::LDA perplexity men 3,369.3 / women 4,628.3 | bertopic                                        | Method docs only                   | Cross-corpus SOTA numbers are not directly comparable to this literary corpus.    |
| NER                    | heuristic-titlecase; top-10 entity mean density 41.60 per 10k | Incomplete openNLP sketch                               | gliner                                          | Upstream docs                      | Local entity density and co-occurrence are project-specific.                      |
| Embeddings / retrieval | tfidf-fallback; mean top-1 neighbor cosine 0.151              | not available                                           | Qwen/Qwen3-Embedding-0.6B                       | Model card / MTEB-style references | Neighbor quality is corpus-specific; external numbers are only reference context. |

### Corpus Snapshot

| corpus_split  | n_books | total_words | mean_words_per_book | median_words_per_book | mean_afinn_per_10k_tokens | mean_type_token_ratio |
| ------------- | ------- | ----------- | ------------------- | --------------------- | ------------------------- | --------------------- |
| expanded-core | 5       | 285618      | 57123.6             | 60770.0               | 201.88                    | 0.0874                |
| legacy-core   | 20      | 1046864     | 52343.2             | 50005.0               | 169.58                    | 0.1353                |
