# mpyc_task.py

import sys
import io
import time
import os
import json
from mpyc.runtime import mpc
from modules.mpc.linear import SecureLinearRegression
from modules.mpc.logistic import SecureLogisticRegression
from modules.psi.multiparty_psi import run_n_party_psi
from modules.psi.party import Party
from utils.cli_parser import parse_cli_args, print_log
from utils.data_loader import load_party_data_adapted
from utils.data_normalizer import normalize_features
from utils.visualization import plot_actual_vs_predicted, plot_logistic_evaluation_report
from utils.constant import RESULT_DIR, UPLOAD_DIR
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score
import math
import pickle

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def log(msg):
    print_log(mpc.pid, msg)

def get_session_id_from_csv_path(csv_path):
    """Extract session_id from the CSV path structure: uploads/{session_id}/{user_id}.csv"""
    path_parts = csv_path.split(os.sep)
    if len(path_parts) >= 3 and path_parts[-3] == UPLOAD_DIR:
        return path_parts[-2]
    return None

async def mpc_task():    
    args = parse_cli_args()
    csv_file = args["csv_file"]
    normalizer_type = args["normalizer_type"]
    regression_type = args["regression_type"]
    epochs = args["epochs"]
    lr = args["learning_rate"]
    is_logging = args["is_logging"]

    party_id = mpc.pid
    session_id = get_session_id_from_csv_path(csv_file)
    
    # Initialize milestone tracking
    milestones = []
    
    # [1] Data Normalization
    start_time = time.time()
    
    # Track data loading time
    user_ids, X_local, y_local, feature_names, label_name = load_party_data_adapted(csv_file)
    
    if normalizer_type:
        try:
            X_local = normalize_features(X_local, method=normalizer_type)
            log(f"✅ Applied '{normalizer_type}' normalization.")
        except ValueError as e:
            log(f"❌ Normalization error: {e}")
            sys.exit(1)
    else:
        log("⚠️ No normalization applied.")
    normalization_time = time.time() - start_time
    
    if party_id == 0:
        milestones.append({"phase": "Data Normalization", "time": normalization_time, "fill": "#1B4F91"})

    # Start MPC runtime
    await mpc.start()
    
    # [2] Secure ID Exchange
    start_time = time.time()

    if y_local is None and party_id == 0:
        log("❗ Warning: Expected label missing for Org A")
    elif y_local is not None and party_id != 0:
        log("❗ Warning: Label provided but will be ignored")
        
    # Send your local feature names to all other parties
    feature_names_all = await mpc.transfer(feature_names, senders=range(len(mpc.parties)))
    
    # Broadcast label name (only Party 0 has it)
    label_name_all = await mpc.transfer(label_name, senders=[0])
    label_name = label_name_all[0] if label_name_all else "Label"

    # Flatten in party order: assume feature_names_all[i] is from party i
    joined_feature_names = []
    for f_list in feature_names_all:
        joined_feature_names.extend(f_list)

    # Step 1: Private Set Intersection (PSI) - Find common user IDs across all parties
    # Step 1.1: Collect user ID lists from all parties
    log("🗂️ Collecting user ID from all parties...")
    gathered_user_ids = await mpc.transfer(user_ids, senders=range(len(mpc.parties)))

    # Step 1.2: Create Party instances for each list of user IDs
    parties = [Party(party_id, ids) for party_id, ids in enumerate(gathered_user_ids)]
    log("✅ Received user ID lists from all parties.")
    
    exchange_time = time.time() - start_time
    
    if party_id == 0:
        milestones.append({"phase": "Secure ID Exchange", "time": exchange_time, "fill": "#336699"})

    # Step 1.3: Run PSI to find the shared user IDs
    log("🔎 Computing intersection of user IDs...")
    
    # [3] Data Intersection
    start_time = time.time()
    intersection = run_n_party_psi(parties)
    elapsed_time = time.time() - start_time
    if is_logging:
        log(f"✅ Found intersected user IDs in {elapsed_time:.2f}s: {intersection}")
    else:
        log(f"✅ Found intersected user IDs in {elapsed_time:.2f}s.")
        
    if party_id == 0:
        milestones.append({"phase": "Data Intersection", "time": elapsed_time, "fill": "#005B8F"})
    
    # Step 2: Join attributes for intersecting users only
    log("🧩 Filtering data for intersected user IDs...")
    
    # [4] Privacy Filtering
    start_time = time.time()

    # Step 2.1: Create a mapping from user_id to index for filtering
    id_to_index = {uid: idx for idx, uid in enumerate(user_ids)}
    intersecting_indices = [id_to_index[uid] for uid in intersection if uid in id_to_index]

    # Step 2.2: Filter local features and labels (if any)
    X_filtered = [X_local[i] for i in intersecting_indices]
    y_filtered = [y_local[i] for i in intersecting_indices] if y_local is not None else None

    log(f"📦 Filtered {len(X_filtered)} records.")

    # Step 2.3: Transfer X and y across all parties
    X_joined = await mpc.transfer(X_filtered, senders=range(len(mpc.parties)))
    y_final = await mpc.transfer(y_filtered, senders=[0])

    # Step 2.4: Flatten and consolidate feature vectors
    X_all = []
    y_all = []

    for i in range(len(intersection)):
        features = []
        for party_features in X_joined:
            features.extend(party_features[i])
        X_all.append(features)
        y_all.append(y_final[0][i])

    log("✅ Completed data join.")
    
    filtering_time = time.time() - start_time
    
    if party_id == 0:
        milestones.append({"phase": "Privacy Filtering", "time": filtering_time, "fill": "#4A80B3"})
    
    # Step 2.5: Pretty print the final joined data 
    # Get all column names (features + Label)
    label_name = label_name or "Label"  # fallback if somehow None
    all_headers = joined_feature_names + [label_name]
    if is_logging:
        log("🧾 Final joined dataset (features + label):")
        
        # Combine features and label to determine column widths
        all_rows = []
        for features, label in zip(X_all, y_all):
            row = list(map(str, features)) + [str(round(label, 2))]
            all_rows.append(row)

        # Calculate max width for each column
        col_widths = []
        for col_idx in range(len(all_headers)):
            max_data_len = max(len(row[col_idx]) for row in all_rows)
            header_len = len(all_headers[col_idx])
            col_widths.append(max(max_data_len, header_len) + 2)

        # Create header line
        header = "idx".ljust(5) + "| " + " | ".join(
            [all_headers[i].ljust(col_widths[i]) for i in range(len(all_headers))]
        )
        separator = "-" * len(header)

        # Print header
        print(header, flush=True)
        print(separator, flush=True)

        # Print data rows
        for idx, row in enumerate(all_rows):
            row_str = " | ".join(
                [row[i].ljust(col_widths[i]) for i in range(len(row))]
            )
            print(str(idx).ljust(5) + "| " + row_str, flush=True)
    
    else:
        log(f"🧾 Final joined features + label: {all_headers}")

    # At this point:
    # X_all = [ [age, income, purchase_history, web_visits], ... ] for intersecting users
    # y_all = [ purchase_amount, ... ] only from Org A

    # Step 3: Do regression
    # Step 3.1: Add bias coeff to X
    X_all = [row + [1.0] for row in X_all]
    
    # Step 3.2: Run the regression
    log(f"⚙️ Running {regression_type} regression on the data...")
    
    # [5] Federated Training
    start_time = time.time()
    if regression_type == 'logistic':
        model = SecureLogisticRegression(epochs=epochs, lr=lr, is_logging=is_logging)
    else:
        model = SecureLinearRegression(epochs=epochs, lr=lr, is_logging=is_logging)
    
    training_time = time.time() - start_time
    if party_id == 0:
        milestones.append({"phase": "Federated Training", "time": training_time, "fill": "#002B5B"})
    
    # [6] Model Evaluation
    start_time = time.time()
    await model.fit([X_all], [y_all])

    # Step 4: Evaluation
    # predict the train data
    start_time = time.time()
    predictions = await model.predict([X_all][0])
    
    # Save session-specific plots
    if session_id:
        linear_plot_path = f"static/{session_id}_linear_plot.png"
        logistic_plot_path = f"static/{session_id}_logistic_roc.png"
    else:
        linear_plot_path = "static/linear_plot.png"
        logistic_plot_path = "static/logistic_roc.png"
    
    if regression_type == 'logistic':
        await plot_logistic_evaluation_report(y_all, predictions, mpc, is_logging, save_path=logistic_plot_path)
    else:
        await plot_actual_vs_predicted(y_all, predictions, mpc, save_path=linear_plot_path)
        
    evaluation_time = time.time() - start_time
    
    if party_id == 0:
        milestones.append({"phase": "Model Evaluation", "time": evaluation_time, "fill": "#3C6E91"})
    
    if party_id == 0:             
        # Save results for party 0 only
        if session_id:
            # Calculate metrics
            accuracy = None
            f1 = None
            
            if regression_type == 'linear':
                rmse = math.sqrt(mean_squared_error(y_all, predictions))
                r2 = r2_score(y_all, predictions)
            else:
                # For logistic regression, calculate accuracy and F1 score
                # Convert predictions to binary for classification metrics
                binary_predictions = [1 if p > 0.5 else 0 for p in predictions]
                binary_y_all = [int(y) for y in y_all]
                
                accuracy = accuracy_score(binary_y_all, binary_predictions)
                f1 = f1_score(binary_y_all, binary_predictions, average='binary', zero_division=0)
                
                # For logistic regression, RMSE and R2 are less meaningful
                rmse = math.sqrt(mean_squared_error(y_all, predictions))
                r2 = 0.0  # R2 is not typically used for classification
            
            # Prepare coefficients
            coefficients = []
            for i, feature in enumerate(joined_feature_names):
                coefficients.append({
                    "feature": feature,
                    "value": round(model.theta[i], 2),
                    "type": "feature"
                })
            # Add intercept (last theta value)
            coefficients.append({
                "feature": label_name,
                "value": round(model.theta[-1], 2),
                "type": "label"
            })
            
            # Save the trained model as a pickle file
            models_dir = os.path.join("models")
            os.makedirs(models_dir, exist_ok=True)
            model_filename = f"{session_id}_model.pkl"
            model_path = os.path.join(models_dir, model_filename)
            
            # Create a model dictionary with all necessary information
            model_data = {
                "theta": model.theta,
                "regression_type": regression_type,
                "feature_names": joined_feature_names,
                "label_name": label_name,
                "epochs": epochs,
                "learning_rate": lr,
                "normalizer": normalizer_type
            }
            
            with open(model_path, "wb") as f:
                pickle.dump(model_data, f)
            log(f"✅ Model saved to {model_path}")
            
            # Get model file size
            model_size_bytes = os.path.getsize(model_path)
            if model_size_bytes < 1024:
                model_size_str = f"{model_size_bytes} B"
            elif model_size_bytes < 1024 * 1024:
                model_size_str = f"{model_size_bytes / 1024:.1f} KB"
            else:
                model_size_str = f"{model_size_bytes / (1024 * 1024):.1f} MB"
            
            # Prepare result data
            result_data = {
                "summary": {
                    "model": "Linear Regression" if regression_type == 'linear' else "Logistic Regression",
                    "milestoneData": milestones,
                    "rmse": rmse,
                    "r2": r2,
                    "epochs": epochs,
                    "lr": lr,
                    "accuracy": accuracy,
                    "f1": f1,
                    "modelPath": model_filename,  # Store just the filename, not full path
                    "modelSize": model_size_str
                },
                "config": {
                    "dataCount": len(y_all),
                    "parties": len(mpc.parties)
                },
                "coefficients": coefficients,
                "actualVsPredicted": {
                    "actual": [round(float(y), 2) for y in y_all[:50]],  # Limit to first 50 for UI
                    "predicted": [round(float(p), 2) for p in predictions[:50]]
                }
            }
            
            # Save results
            results_dir = os.path.join(RESULT_DIR)
            os.makedirs(results_dir, exist_ok=True)
            result_file = os.path.join(results_dir, f"{session_id}.json")
            with open(result_file, "w") as f:
                json.dump(result_data, f, indent=2)
            log(f"✅ Results saved to {result_file}")

    await mpc.shutdown()
    log("🛑 MPyC shutdown")

# Use MPyC's loop-safe runner
mpc.run(mpc_task())
log("✅ MPyC task complete")