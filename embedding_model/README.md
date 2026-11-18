# Local embedding weights

The app does not load this folder unless you point it here.

`EMBEDDING_MODEL_PATH` defaults to `sentence-transformers/all-mpnet-base-v2`. The first run downloads that model from Hugging Face into the local Sentence Transformers cache.

To use a copy you already have on disk, set `EMBEDDING_MODEL_PATH` in `.env` to this directory (or any other folder that contains a Sentence Transformers model). The vector size must stay 768, or you must also change `EMBEDDING_DIMENSION` and recreate the OpenSearch index.
