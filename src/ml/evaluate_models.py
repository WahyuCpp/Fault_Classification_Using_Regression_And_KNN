"""Model evaluation and metrics reporting."""
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

def evaluate_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute comprehensive evaluation metrics for multiclass motor fault classification."""
    acc = float(accuracy_score(y_true, y_pred))
    p_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    p_weighted = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))

    r_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    r_weighted = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))

    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    report = classification_report(y_true, y_pred, labels=labels, zero_division=0, output_dict=True)

    return {
        "accuracy": round(acc, 4),
        "precision_macro": round(p_macro, 4),
        "precision_weighted": round(p_weighted, 4),
        "recall_macro": round(r_macro, 4),
        "recall_weighted": round(r_weighted, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_weighted": round(f1_weighted, 4),
        "confusion_matrix": cm,
        "classification_report": report,
    }


def print_comparison_table(models_metrics: Dict[str, Dict[str, Any]]) -> None:
    """Print formatted comparison table across multiple models."""
    print("\n" + "=" * 70)
    print(f"{'Model':<24} {'Accuracy':<10} {'Precision':<12} {'Recall':<10} {'F1-Macro':<10}")
    print("-" * 70)
    for model_name, metrics in models_metrics.items():
        print(
            f"{model_name:<24} "
            f"{metrics.get('accuracy', 0.0):<10.4f} "
            f"{metrics.get('precision_macro', 0.0):<12.4f} "
            f"{metrics.get('recall_macro', 0.0):<10.4f} "
            f"{metrics.get('f1_macro', 0.0):<10.4f}"
        )
    print("=" * 70 + "\n")
