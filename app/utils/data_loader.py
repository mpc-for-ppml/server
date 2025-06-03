# utils/data_loader.py

import csv
import pandas as pd
from utils.data_preprocessor import DataPreprocessor
from interface.identifier_config import IdentifierConfig, IdentifierMode

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
                           identifier_config=None,
                           verbose=False):
    """
    Dynamically loads CSV data for a party and returns:
    - identifiers: list of identifier values (based on identifier_config)
    - X_local: list of feature vectors
    - y_local: list of labels (if available, else None)
    - feature_names: names of features (excluding identifier columns and label)
    - label_name: the name of the label column (if available, else None)
    
    Args:
        filename: Path to the CSV file
        preferred_label: Preferred label column name, with fallback to default candidates
        identifier_config: IdentifierConfig object specifying how to create identifiers
        verbose: Whether to print preprocessing details
    """
    # Load data into pandas DataFrame for preprocessing
    df = pd.read_csv(filename)
    
    # Default to user_id if no config provided
    if identifier_config is None:
        identifier_config = IdentifierConfig(
            mode=IdentifierMode.SINGLE,
            columns=["user_id"]
        )
    
    # Validate identifier columns exist
    missing_cols = [col for col in identifier_config.columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV file must contain identifier columns: {missing_cols}")
    
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
    # Create identifiers before preprocessing
    identifiers_list = []
    for _, row in df.iterrows():
        identifier = identifier_config.create_identifier(row.to_dict())
        identifiers_list.append(identifier)
    identifiers_series = pd.Series(identifiers_list, index=df.index)
    
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
    
    # Temporarily remove identifier columns for preprocessing
    df_without_identifiers = df.drop(columns=identifier_config.columns)
    
    # Filter out non-numeric columns (except label column)
    numeric_columns = df_without_identifiers.select_dtypes(include=['number']).columns.tolist()
    if label_name and label_name not in numeric_columns:
        # Keep label column even if it's not numeric (for binary classification)
        numeric_columns.append(label_name)
    
    # Keep only numeric columns and label for preprocessing
    if verbose:
        all_columns = df_without_identifiers.columns.tolist()
        non_numeric_cols = [col for col in all_columns if col not in numeric_columns]
        if non_numeric_cols:
            print(f"🗑️ Dropping non-numeric columns: {non_numeric_cols}", flush=True)
    
    df_numeric_only = df_without_identifiers[numeric_columns]
    
    # Apply preprocessing
    df_preprocessed = preprocessor.preprocess(
        df_numeric_only,
        label_column=label_name,
        **default_config
    )
    
    # Get preprocessing report
    preprocessing_report = preprocessor.get_preprocessing_report()
    
    # Re-align identifiers with preprocessed data
    # Get the index of rows that remained after preprocessing
    remaining_indices = df_preprocessed.index
    df = df_preprocessed
    identifiers_series = identifiers_series.loc[remaining_indices]
    
    # Print report if verbose
    if verbose:
        preprocessor.print_report()
    
    # Extract identifiers
    identifiers = identifiers_series.tolist()
    
    # Identify feature columns (excluding identifier columns and label)
    excluded_cols = set(identifier_config.columns) | {label_name} if label_name else set(identifier_config.columns)
    feature_cols = [col for col in df.columns if col not in excluded_cols]
    
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
    
    return identifiers, X_local, y_local, feature_names, label_name

