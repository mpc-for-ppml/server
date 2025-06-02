# utils/data_loader.py

import csv
import pandas as pd
from utils.data_preprocessor import DataPreprocessor

def load_party_data(filename):
    """Loads a party's data from a CSV file into X and y."""
    X_local, y_local = [], []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            *features, label = map(float, row)
            X_local.append(features)
            y_local.append(label)
    return X_local, y_local

def load_party_data_adapted(filename, preferred_label=None,
                           verbose=False):
    """
    Dynamically loads CSV data for a party and returns:
    - user_ids: list of user_id values
    - X_local: list of feature vectors
    - y_local: list of labels (if available, else None)
    - feature_names: names of features (excluding user_id and label)
    - label_name: the name of the label column (if available, else None)
    
    Args:
        filename: Path to the CSV file
        preferred_label: Preferred label column name, with fallback to default candidates
        apply_preprocessing: Whether to apply data preprocessing
        preprocessing_config: Dict with preprocessing configuration
        verbose: Whether to print preprocessing details
    """
    # Load data into pandas DataFrame for preprocessing
    df = pd.read_csv(filename)
    
    # Ensure user_id column exists
    if "user_id" not in df.columns:
        raise ValueError("CSV file must contain 'user_id' column")
    
    # Identify label column
    label_name = None
    if preferred_label and preferred_label in df.columns:
        label_name = preferred_label
    else:
        # Fallback to default candidates
        label_col_candidates = ["will_purchase", "purchase_amount"]
        for col in label_col_candidates:
            if col in df.columns:
                label_name = col
                break
    
    # Apply preprocessing if requested
    preprocessing_report = None
    
    # Data pre-processing
    # Store user_ids before preprocessing
    user_ids_series = df["user_id"].copy()
    
    # Default preprocessing configuration
    default_config = {
        "remove_duplicates": False,
        "handle_missing": "drop",
        "remove_outliers": True,
        "outlier_method": "iqr",
        "outlier_threshold": 1.5,
        "drop_high_missing_cols": True,
        "missing_threshold": 0.5,
        "drop_constant_cols": True,
        "drop_high_correlation": True,
        "correlation_threshold": 0.95
    }
    
    # Create preprocessor
    preprocessor = DataPreprocessor(verbose=verbose)
    
    # Temporarily remove user_id for preprocessing
    df_without_userid = df.drop(columns=["user_id"])
    
    # Apply preprocessing
    df_preprocessed = preprocessor.preprocess(
        df_without_userid,
        label_column=label_name,
        **default_config
    )
    
    # Get preprocessing report
    preprocessing_report = preprocessor.get_preprocessing_report()
    
    # Re-align user_ids with preprocessed data
    # Get the index of rows that remained after preprocessing
    remaining_indices = df_preprocessed.index
    df = df_preprocessed
    user_ids_series = user_ids_series.loc[remaining_indices]
    
    # Print report if verbose
    if verbose:
        preprocessor.print_report()
    
    # Extract user_ids
    user_ids = user_ids_series.tolist()
    
    # Identify feature columns (excluding user_id and label)
    feature_cols = [col for col in df.columns if col != "user_id" and col != label_name]
    
    # Extract features and labels
    X_local = df[feature_cols].values.tolist()
    y_local = df[label_name].values.tolist() if label_name else None
    
    # Get feature names
    feature_names = feature_cols
    
    # Store preprocessing report if we want to access it later
    if preprocessing_report and verbose:
        print(f"\n📋 Preprocessing summary for {filename}:", flush=True)
        print(f"  📏 Original samples: {preprocessing_report['original_shape'][0]}", flush=True)
        print(f"  ✅ Final samples: {preprocessing_report['final_shape'][0]}", flush=True)
        print(f"  🗑️  Samples removed: {preprocessing_report['rows_removed']}", flush=True)
    
    return user_ids, X_local, y_local, feature_names, label_name

