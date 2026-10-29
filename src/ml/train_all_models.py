"""Train all 3 classifiers and display comparison table."""
from src.ml.train_logistic_regression import train_logistic_regression
from src.ml.train_decision_tree import train_decision_tree
from src.ml.train_knn import train_knn
from src.ml.evaluate_models import print_comparison_table

def train_and_compare_all():
    print("=" * 70)
    print("MONTREAL-VT: Training and Evaluating All Models")
    print("=" * 70)

    _, lr_metrics = train_logistic_regression()
    _, dt_metrics = train_decision_tree()
    _, knn_metrics = train_knn()

    comparison = {
        "Logistic Regression": lr_metrics,
        "Decision Tree": dt_metrics,
        "KNN": knn_metrics,
    }

    print_comparison_table(comparison)

if __name__ == "__main__":
    train_and_compare_all()

