# User Workflows

## UCI Metro Interstate Traffic Volume

This demonstration uses the UCI Metro Interstate Traffic Volume dataset: hourly westbound I-94 counts from 2012–2018 with weather, holiday, and local-time fields. UCI lists 48,204 observations, eight input features, and no missing values. The target is `traffic_volume`.

Dataset source: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume). Cite as: Hogue, J. (2019). *Metro Interstate Traffic Volume* [Dataset]. UCI Machine Learning Repository. [https://doi.org/10.24432/C5X60B](https://doi.org/10.24432/C5X60B). UCI identifies the license as Creative Commons Attribution 4.0 International (CC BY 4.0); credit the dataset author and UCI when sharing results.

The raw file is the uncompressed `data/Metro_Interstate_Traffic_Volume.csv`. The `data/` directory is ignored by Git in this repository, so a new checkout can retrieve and extract the official archive with:

```bash
cd $(git rev-parse --show-toplevel) && script/download_dataset.sh
```

The downloader refuses to overwrite an existing raw file. It downloads the archive linked from UCI, decompresses the CSV, and saves it in plain-text CSV format.

### Run the complete workflow

```bash
cd $(git rev-parse --show-toplevel) && script/run_all_workflows.sh
```

All reports, figures, processed data, and model artifacts are written under `output/metro_traffic_volume/`. To use another raw-data directory or output root, pass `--data_path VALUE` and/or `--output_path VALUE` to the runner or an individual workflow script. Pass `--config_path VALUE` to select a different JSON configuration.

### Five workflow stages

| Workflow | Shell entry point | Input | Main outputs |
|---|---|---|---|
| 1. Data understanding | `script/workflow_1_data_understanding/workflow_1_data_understanding.sh` | Raw CSV | `data_overview.md`, `data_overview.json`: dimensions, types, missingness, exact duplicates, ranges, and summaries |
| 2. Visualization | `script/workflow_2_visualization/workflow_2_visualization.sh` | Raw CSV | Three scalable SVG figures: average volume by hour, weekday, and main weather category |
| 3. Feature engineering | `script/workflow_3_feature_engineering/workflow_3_feature_engineering.sh` | Raw CSV | ML-ready CSV plus a feature dictionary; derives `hour`, `weekday`, `month`, and `is_weekend` |
| 4. Model training | `script/workflow_4_model_training/workflow_4_model_training.sh` | Workflow 3 CSV | Random forest, chronological holdout metrics (MAE, RMSE, R²), predictions, observed-vs-predicted scatter, and time-series SVGs |
| 5. Model interpretation | `script/workflow_5_model_interpretation/workflow_5_model_interpretation.sh` | Workflow 3 CSV and workflow 4 model | Held-out permutation-importance CSV, SVG figure, and plain-language interpretation |

Code is organized directly under matching `workflow_1_...` through `workflow_5_...` directories in `script/` and `src/`. Python data and plotting utilities shared by multiple workflows are kept in `src/common/` and `web/common/`. Figure entry points live beside the workflows that use them in `web/workflow_2_visualization/`, `web/workflow_4_model_training/`, and `web/workflow_5_model_interpretation/`.

Each stage can also be run on its own from the repository root. Workflows 1–3 default to `data/`; workflows 4–5 default to `output/metro_traffic_volume/feature_engineering/` and require the earlier stages to have completed.

### Workflow configuration

Each workflow reads its default JSON file from its matching `config/workflow_N_.../config.json` directory when `--config_path` is omitted. This applies to the shell entry points and direct Python/Node entry points. Pass `--config_path` to select an alternative file. For example:

```bash
script/workflow_4_model_training/workflow_4_model_training.sh \
  --config_path config/workflow_4_model_training/config.json
```

`--config_path` accepts an absolute path or a path relative to the repository root. The optional `--data_path` and `--output_path` arguments override those two top-level values in the selected JSON file; all other runtime settings come from that file. The workflow JSON files hold dataset filenames and schema, feature definitions, report settings, model and interpretation parameters, output names, and figure labels, dimensions, colors, and layout values.

`script/run_all_workflows.sh` also accepts `--config_path`. Its default is `config/run_all_workflows/config.json`, which maps each of the five workflow names to its own JSON file. A custom run-all JSON can point to another set of workflow configs. A run-all `--data_path` supplies the raw input to workflows 1–3. A run-all `--output_path` overrides each workflow's output root and directs workflows 4–5 to the feature directory declared by the selected workflow 3 config.

Workflow 4 and workflow 5 deliberately keep separate `split.test_fraction` values in their own JSON files. Changing the training holdout does not silently change the period used for workflow 5's permutation-importance analysis.
