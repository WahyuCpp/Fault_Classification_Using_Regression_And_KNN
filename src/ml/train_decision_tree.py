"""Train Decision Tree classifier for fault condition classification."""
from pathlib import Path
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit

from config.main_config import TRAINING_DATA_DIR
from config.ml_config import HYPERPARAMETERS, TEST_SIZE, RANDOM_STATE
from src.ml.evaluate_models import evaluate_classifier
from src.ml.model_utils import save_model
from src.utils.logger import get_logger

logger = get_logger("train_dt", "ml.log")

def train_decision_tree(
    features_csv: str | Path = TRAINING_DATA_DIR / "training_features.csv",
) -> Tuple[Pipeline, Dict[str, Any]]:
    """Train Decision Tree classifier pipeline."""
    df = pd.read_csv(features_csv)

    meta_cols = ["source_file", "segment_number", "fault_label"]
    feature_cols = [c for c in df.columns if c not in meta_cols]

    X = df[feature_cols].values
    y = df["fault_label"].values
    groups = df["source_file"].values

    unique_groups = np.unique(groups)
    if len(unique_groups) >= 4:
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
        train_idx, test_idx = next(gss.split(X, y, groups=groups))
    else:
        sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
        train_idx, test_idx = next(sss.split(X, y))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    params = HYPERPARAMETERS["decision_tree"]
    pipeline = Pipeline([
        ("classifier", DecisionTreeClassifier(**params)),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    classes = pipeline.named_steps["classifier"].classes_.tolist()
    metrics = evaluate_classifier(y_test, y_pred, labels=classes)

    save_model(
        model=pipeline,
        model_name="decision_tree",
        feature_names=feature_cols,
        classes=classes,
        metrics=metrics,
        hyperparameters=params,
    )

    logger.info("Trained Decision Tree: Accuracy=%.4f, F1-macro=%.4f", metrics["accuracy"], metrics["f1_macro"])
    print("\n[Decision Tree Results]")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision (macro): {metrics['precision_macro']:.4f}")
    print(f"Recall (macro): {metrics['recall_macro']:.4f}")
    print(f"F1-score (macro): {metrics['f1_macro']:.4f}")

    return pipeline, metrics


if __name__ == "__main__":
    train_decision_tree()

