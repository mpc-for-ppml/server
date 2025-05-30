# utils/visualization.py

import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score, classification_report, roc_curve, roc_auc_score
import math
import os
    
def plot_actual_vs_predicted(y_true, y_pred, mpc, save_path="linear_regression_plot.png"):
    """
    Plot actual vs predicted target values and show RMSE & R² Score.

    Args:
        y_pred: Labels predicted by the model.
        y_true: True binary labels.
        mpc: MPyC runtime object (used for awaiting outputs).
        save_path: File path to save the plot.
    """
    async def evaluate():
        # ROC-AUC Curve (only on Party 0)
        if mpc.pid == 0:
            print(f"[Party {mpc.pid}] 📊 Saving the evaluation report...", flush=True)

            # Calculate metrics
            mse = mean_squared_error(y_true, y_pred)
            rmse = math.sqrt(mse)
            r2 = r2_score(y_true, y_pred)

            # Plot: Actual vs Predicted
            plt.figure(figsize=(8, 6))
            plt.scatter(y_true, y_pred, alpha=0.7, edgecolors='k')
            plt.plot([min(y_true), max(y_true)], [min(y_true), max(y_true)], 'r--', label="Ideal")

            # Metrics text
            metrics_text = f"RMSE: {rmse:.3f}\nR² Score: {r2:.3f}"
            plt.gca().text(0.05, 0.95, metrics_text, transform=plt.gca().transAxes,
                        fontsize=10, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

            plt.xlabel("Actual")
            plt.ylabel("Predicted")
            plt.title("Actual vs Predicted (Linear Regression)")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            plt.close()
            
        print(f"[Party {mpc.pid}] ✅ Evaluation complete.", flush=True)

    return evaluate()

def plot_logistic_evaluation_report(y_true, y_pred, mpc, is_logging, save_path="logistic_regression_roc.png"):
    """
    Evaluate and visualize logistic regression results and save the ROC curve as an image.

    Args:
        y_pred: Labels predicted by the model.
        y_true: True binary labels.
        mpc: MPyC runtime object (used for awaiting outputs).
        save_path: File path to save the ROC plot.
    """
    async def evaluate():
        # Classification report
        report = classification_report(y_true, y_pred, zero_division=0)
        print(f"[Party {mpc.pid}] 📊 Saving the evaluation report...", flush=True)
        if is_logging:
            print(report)

        # ROC-AUC Curve (only on Party 0)
        if mpc.pid == 0:
            fpr, tpr, _ = roc_curve(y_true, y_pred)
            roc_auc = roc_auc_score(y_true, y_pred)

            plt.figure(figsize=(6, 6))
            plt.plot(fpr, tpr, color='blue', label=f"AUC = {roc_auc:.2f}")
            plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title("AUC-ROC Curve")
            plt.legend(loc="lower right")
            plt.grid(True)
            plt.tight_layout()

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            plt.close()
            
        print(f"[Party {mpc.pid}] ✅ Evaluation complete.", flush=True)

    return evaluate()
