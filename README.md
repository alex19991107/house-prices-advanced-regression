# House Prices - Advanced Regression Techniques

Kaggle competition project for predicting home sale prices from the Ames Housing dataset.

Competition: https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques

## Final Result

Best public score in this project: `0.12485`

Best submission:

```text
submissions/09_submission_xgboost_seed_search.csv
```

Final approach:

- Remove obvious `GrLivArea` outliers from training data.
- Apply `log1p` to skewed numeric features.
- Blend LassoCV and tuned XGBoost.
- Final blend: `0.62 * Lasso + 0.38 * XGBoost(seed=23)`.

## Goal

Build a regression model that predicts `SalePrice` for each house in the test set. Kaggle evaluates submissions with root mean squared error on the logarithm of predicted and actual sale prices.

## Suggested Project Layout

```text
.
├── data/              # Kaggle CSV files, ignored by git
├── notebooks/         # Exploratory analysis and experiments
├── src/               # Reusable training and feature code
├── submissions/       # Generated submission CSV files, ignored by git
├── .gitignore
└── README.md
```

## Setup

Install the Kaggle CLI and configure your API token:

```powershell
pip install kaggle
```

Download the competition files:

```powershell
kaggle competitions download -c house-prices-advanced-regression-techniques -p data
Expand-Archive -Path data/house-prices-advanced-regression-techniques.zip -DestinationPath data -Force
```

Expected local files:

```text
data/train.csv
data/test.csv
data/sample_submission.csv
```

## Baseline Workflow

1. Load `train.csv` and `test.csv`.
2. Explore missing values, categorical columns, skewed numeric features, and outliers.
3. Build preprocessing for numeric and categorical features.
4. Train baseline models such as Ridge, Lasso, Random Forest, XGBoost, LightGBM, or CatBoost.
5. Evaluate with cross-validation using RMSLE-compatible scoring.
6. Generate a `submission.csv` with columns `Id` and `SalePrice`.

Available notebooks:

- `notebooks/00_eda_report.ipynb`: Chinese EDA report.
- `notebooks/02_data_cleaning_modeling.ipynb`: Chinese data cleaning, feature engineering, modeling, validation, and submission workflow.
- `notebooks/03_modeling_improve_from_baseline.ipynb`: small-step optimization experiments starting from the current baseline.
- `notebooks/04_modeling_advanced_linear.ipynb`: advanced regularized linear model experiments after the validated improvement.
- `notebooks/05_modeling_boosting_models.ipynb`: XGBoost, LightGBM, CatBoost, and blend experiments.
- `notebooks/06_modeling_weighted_blend.ipynb`: weighted blend search for Lasso, ElasticNet, and XGBoost.
- `notebooks/07_modeling_xgboost_tuning.ipynb`: XGBoost parameter tuning for the Lasso/XGBoost blend.
- `notebooks/08_modeling_second_level_blend.ipynb`: second-level blending of the strongest submission files.
- `notebooks/09_modeling_xgboost_seed_search.ipynb`: XGBoost random seed search for the tuned Lasso/XGBoost blend.
- `notebooks/10_modeling_xgboost_seed_ensemble.ipynb`: XGBoost multi-seed ensemble for the tuned Lasso/XGBoost blend.
- `notebooks/99_submission_score_analysis.md`: submission score comparison and next experiment notes.

Run the included Ridge baseline:

```powershell
python src/train_baseline.py
```

This writes:

```text
submissions/01_submission_baseline.csv
```

## Submission

```powershell
kaggle competitions submit -c house-prices-advanced-regression-techniques -f submissions/01_submission_baseline.csv -m "ridge baseline"
```
