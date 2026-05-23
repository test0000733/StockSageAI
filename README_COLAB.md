Colab 8-Model Training — Quick Run

- Open `Google_Colab_8model_training.ipynb` in Google Colab.
- Run the first cell to install dependencies.
- Edit the data-loading cell to point to your dataset (or use the default yfinance downloader in the notebook).
- Run the training cells (adjust `epochs`/`batch_size` as needed).
- After training completes the notebook saves model artifacts and `scalers.pkl` and `model_metadata.json` into a zip file named `stocksage_models_export.zip`.
- Use the Colab download cell (or `files.download`) to download the zip to your device.
- Unzip and copy the files into `StockSageAI/models/` in the repo:

```
unzip stocksage_models_export.zip -d StockSageAI/models/
```

- Restart the Streamlit app (or redeploy) so `StockSageAI/trained_model_manager.py` loads the new `.pkl` artifacts.

Local alternative: run `build_trained_models.py` to produce demo artifacts for testing:

```
python build_trained_models.py
```

Notes:
- Large model binaries may increase repo size; consider Git LFS for production artifacts.
- If you want me to commit the produced `.pkl` files to the repo, confirm and I'll add them (or add LFS config first).