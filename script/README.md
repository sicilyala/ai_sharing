# User Workflows

## Dataset preparation

- **Purpose:** Obtain the UCI Metro Interstate Traffic Volume dataset.
- **Input:** None; the script retrieves the dataset.
- **Output:** `data/Metro_Interstate_Traffic_Volume.csv`.
- **Usage:** From the repository root, run `script/download_dataset.sh`. To save it in another directory, use `script/download_dataset.sh --data_path DIR`.

## Analysis workflows

Run each command from the repository root. By default, workflows 1–3 read the raw CSV from `data/`; workflows 4–5 read the feature CSV from `output/metro_traffic_volume/feature_engineering/`. All workflows write under `output/metro_traffic_volume/` by default.

Each command accepts optional `--config_path FILE`, `--data_path DIR`, and `--output_path DIR` arguments to select a configuration file, input directory, or output root.

### 1. Data understanding

- **Purpose:** Summarize the dataset's structure and contents.
- **Input:** `Metro_Interstate_Traffic_Volume.csv`.
- **Output:** `data_understanding/data_overview.md` and `data_understanding/data_overview.json`.
- **Usage:** `script/workflow_1_data_understanding/workflow_1_data_understanding.sh`

### 2. Visualization

- **Purpose:** Show traffic-volume patterns across time and weather categories.
- **Input:** `Metro_Interstate_Traffic_Volume.csv`.
- **Output:** `visualization/average_traffic_by_hour.svg`, `visualization/average_traffic_by_weekday.svg`, and `visualization/average_traffic_by_weather.svg`.
- **Usage:** `script/workflow_2_visualization/workflow_2_visualization.sh`

### 3. Feature engineering

- **Purpose:** Prepare the dataset for model training.
- **Input:** `Metro_Interstate_Traffic_Volume.csv`.
- **Output:** `feature_engineering/metro_traffic_features.csv` and `feature_engineering/feature_dictionary.md`.
- **Usage:** `script/workflow_3_feature_engineering/workflow_3_feature_engineering.sh`

### 4. Model training

- **Purpose:** Train and evaluate a traffic-volume prediction model.
- **Input:** `feature_engineering/metro_traffic_features.csv` produced by workflow 3.
- **Output:** `model_training/model.joblib`, `model_training/metrics.json`, `model_training/test_predictions.csv`, `model_training/observed_vs_predicted.svg`, and `model_training/predictions_over_time.svg`.
- **Usage:** `script/workflow_4_model_training/workflow_4_model_training.sh`

### 5. Model interpretation

- **Purpose:** Summarize which model inputs the trained model relies on.
- **Input:** `feature_engineering/metro_traffic_features.csv` from workflow 3 and `model_training/model.joblib` from workflow 4.
- **Output:** `model_interpretation/feature_importance.csv`, `model_interpretation/interpretation.md`, and `model_interpretation/feature_importance.svg`.
- **Usage:** `script/workflow_5_model_interpretation/workflow_5_model_interpretation.sh`
