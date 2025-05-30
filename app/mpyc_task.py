# mpyc_task.py

import sys
import io
import time
from mpyc.runtime import mpc
from modules.mpc.linear import SecureLinearRegression
from modules.mpc.logistic import SecureLogisticRegression
from modules.psi.multiparty_psi import run_n_party_psi
from modules.psi.party import Party
from utils.cli_parser import parse_cli_args, print_log
from utils.data_loader import load_party_data_adapted
from utils.data_normalizer import normalize_features
from utils.visualization import plot_actual_vs_predicted, plot_logistic_evaluation_report

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def log(msg):
    print_log(mpc.pid, msg)

async def mpc_task():    
    args = parse_cli_args()
    csv_file = args["csv_file"]
    normalizer_type = args["normalizer_type"]
    regression_type = args["regression_type"]
    epochs = args["epochs"]
    lr = args["learning_rate"]
    is_logging = args["is_logging"]

    party_id = mpc.pid
    user_ids, X_local, y_local, feature_names, label_name = load_party_data_adapted(csv_file)

    # Normalize features
    if normalizer_type:
        try:
            X_local = normalize_features(X_local, method=normalizer_type)
            log(f"✅ Applied '{normalizer_type}' normalization.")
        except ValueError as e:
            log(f"❌ Normalization error: {e}")
            sys.exit(1)
    else:
        log("⚠️ No normalization applied.")

    # Start MPC runtime
    await mpc.start()

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

    # Step 1.3: Run PSI to find the shared user IDs
    log("🔎 Computing intersection of user IDs...")
    start_time = time.time()
    intersection = run_n_party_psi(parties)
    elapsed_time = time.time() - start_time
    if is_logging:
        log(f"✅ Found intersected user IDs in {elapsed_time:.2f}s: {intersection}")
    else:
        log(f"✅ Found intersected user IDs in {elapsed_time:.2f}s.")
    
    # Step 2: Join attributes for intersecting users only
    log("🧩 Filtering data for intersected user IDs...")

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
    if regression_type == 'logistic':
        model = SecureLogisticRegression(epochs=epochs, lr=lr, is_logging=is_logging)
    else:
        model = SecureLinearRegression(epochs=epochs, lr=lr, is_logging=is_logging)
    
    await model.fit([X_all], [y_all])

    # Step 4: Evaluation
    # predict the train data
    predictions = await model.predict([X_all][0])        
    if regression_type == 'logistic':
        await plot_logistic_evaluation_report(y_all, predictions, mpc, is_logging, save_path="static/logistic_roc.png")
    else:
        await plot_actual_vs_predicted(y_all, predictions, mpc, save_path="static/linear_plot.png")

    await mpc.shutdown()
    log("🛑 MPyC shutdown")

# Use MPyC's loop-safe runner
mpc.run(mpc_task())
log("✅ MPyC task complete")