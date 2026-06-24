from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import TransformedTargetRegressor


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SUBMISSION_DIR = ROOT / "submissions"


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def rmsle(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_pred = np.maximum(y_pred, 0)
    return float(np.sqrt(np.mean((np.log1p(y_true) - np.log1p(y_pred)) ** 2)))


def build_model(X: pd.DataFrame) -> TransformedTargetRegressor:
    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = X.select_dtypes(exclude=["number"]).columns.tolist()

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", make_one_hot_encoder()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )

    regressor = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", RidgeCV(alphas=np.logspace(-3, 3, 13))),
        ]
    )

    return TransformedTargetRegressor(
        regressor=regressor,
        func=np.log1p,
        inverse_func=np.expm1,
    )


def cross_validate(model: TransformedTargetRegressor, X: pd.DataFrame, y: pd.Series) -> float:
    scores = []
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    for train_idx, valid_idx in cv.split(X):
        fold_model = clone(model)
        X_train, X_valid = X.iloc[train_idx], X.iloc[valid_idx]
        y_train, y_valid = y.iloc[train_idx], y.iloc[valid_idx]

        fold_model.fit(X_train, y_train)
        predictions = fold_model.predict(X_valid)
        scores.append(rmsle(y_valid.to_numpy(), predictions))

    return float(np.mean(scores))


def main() -> None:
    train = pd.read_csv(DATA_DIR / "train.csv")
    test = pd.read_csv(DATA_DIR / "test.csv")

    X = train.drop(columns=["SalePrice"])
    y = train["SalePrice"]
    test_ids = test["Id"]

    X = X.drop(columns=["Id"])
    X_test = test.drop(columns=["Id"])

    model = build_model(X)
    score = cross_validate(model, X, y)
    print(f"5-fold CV RMSLE: {score:.5f}")

    model.fit(X, y)
    predictions = np.maximum(model.predict(X_test), 0)

    SUBMISSION_DIR.mkdir(exist_ok=True)
    submission = pd.DataFrame({"Id": test_ids, "SalePrice": predictions})
    output_path = SUBMISSION_DIR / "01_submission_baseline.csv"
    submission.to_csv(output_path, index=False)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
