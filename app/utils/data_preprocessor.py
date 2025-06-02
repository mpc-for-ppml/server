# utils/data_preprocessor.py

import pandas as pd
import numpy as np
from mpyc.runtime import mpc
from typing import Optional, Dict, Any

from utils.cli_parser import print_log

def log(msg):
    print_log(mpc.pid, msg)
    
class DataPreprocessor:
    """Comprehensive data preprocessing for ML pipelines"""
    
    def __init__(self, verbose: bool = False, party_id: int = 0):
        self.verbose = verbose
        self.party_id = party_id
        self.preprocessing_report = {
            "original_shape": None,
            "final_shape": None,
            "steps_applied": [],
            "rows_removed": 0,
            "columns_removed": 0,
            "null_values_handled": 0,
            "duplicates_removed": 0,
            "outliers_removed": 0
        }
    
    def preprocess(self, 
                   df: pd.DataFrame, 
                   label_column: Optional[str] = None,
                   remove_duplicates: bool = True,
                   handle_missing: str = "drop",  # "drop", "mean", "median", "mode", "zero"
                   remove_outliers: bool = True,
                   outlier_method: str = "iqr",  # "iqr", "zscore"
                   outlier_threshold: float = 1.5,  # IQR multiplier or z-score threshold
                   drop_high_missing_cols: bool = True,
                   missing_threshold: float = 0.5,  # Drop columns with >50% missing
                   drop_constant_cols: bool = True,
                   drop_high_correlation: bool = True,
                   correlation_threshold: float = 0.95) -> pd.DataFrame:
        """
        Apply comprehensive preprocessing steps to the dataframe.
        
        Args:
            df: Input dataframe
            label_column: Name of the label column (if any) to preserve
            remove_duplicates: Whether to remove duplicate rows
            handle_missing: How to handle missing values
            remove_outliers: Whether to remove outliers
            outlier_method: Method for outlier detection
            outlier_threshold: Threshold for outlier detection
            drop_high_missing_cols: Whether to drop columns with high missing values
            missing_threshold: Threshold for dropping columns
            drop_constant_cols: Whether to drop constant columns
            drop_high_correlation: Whether to drop highly correlated features
            correlation_threshold: Threshold for correlation
            
        Returns:
            Preprocessed dataframe
        """
        self.preprocessing_report["original_shape"] = df.shape
        original_rows = len(df)
        
        # Step 1: Remove exact duplicates
        if remove_duplicates:
            before_rows = len(df)
            df = self._remove_duplicates(df)
            removed = before_rows - len(df)
            self.preprocessing_report["duplicates_removed"] = removed
            if removed > 0:
                self.preprocessing_report["steps_applied"].append(f"🔄 Removed {removed} duplicate rows")
        
        # Step 2: Handle columns with high missing values
        if drop_high_missing_cols:
            cols_before = len(df.columns)
            df = self._drop_high_missing_columns(df, missing_threshold, label_column)
            cols_removed = cols_before - len(df.columns)
            if cols_removed > 0:
                self.preprocessing_report["columns_removed"] += cols_removed
                self.preprocessing_report["steps_applied"].append(
                    f"🗑️  Dropped {cols_removed} columns with >{missing_threshold*100}% missing values"
                )
        
        # Step 3: Handle missing values
        before_missing = df.isnull().sum().sum()
        df = self._handle_missing_values(df, method=handle_missing, label_column=label_column)
        handled_missing = before_missing - df.isnull().sum().sum()
        if handled_missing > 0:
            self.preprocessing_report["null_values_handled"] = handled_missing
            self.preprocessing_report["steps_applied"].append(
                f"🔧 Handled {handled_missing} missing values using '{handle_missing}' method"
            )
        
        # Step 4: Remove constant columns
        if drop_constant_cols:
            cols_before = len(df.columns)
            df = self._remove_constant_columns(df, label_column)
            cols_removed = cols_before - len(df.columns)
            if cols_removed > 0:
                self.preprocessing_report["columns_removed"] += cols_removed
                self.preprocessing_report["steps_applied"].append(
                    f"🔒 Removed {cols_removed} constant columns"
                )
        
        # Step 5: Remove highly correlated features
        if drop_high_correlation and len(df.columns) > 2:  # Need at least 3 columns
            cols_before = len(df.columns)
            df = self._remove_highly_correlated(df, correlation_threshold, label_column)
            cols_removed = cols_before - len(df.columns)
            if cols_removed > 0:
                self.preprocessing_report["columns_removed"] += cols_removed
                self.preprocessing_report["steps_applied"].append(
                    f"🔗 Removed {cols_removed} highly correlated columns (>{correlation_threshold})"
                )
        
        # Step 6: Remove outliers (only from numeric columns, excluding label)
        if remove_outliers and len(df) > 10:  # Need sufficient data
            before_rows = len(df)
            df = self._remove_outliers(df, method=outlier_method, threshold=outlier_threshold, 
                                     label_column=label_column)
            removed = before_rows - len(df)
            if removed > 0:
                self.preprocessing_report["outliers_removed"] = removed
                self.preprocessing_report["steps_applied"].append(
                    f"📊 Removed {removed} rows with outliers using '{outlier_method}' method"
                )
        
        # Final shape
        self.preprocessing_report["final_shape"] = df.shape
        self.preprocessing_report["rows_removed"] = original_rows - len(df)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove exact duplicate rows"""
        return df.drop_duplicates()
    
    def _drop_high_missing_columns(self, df: pd.DataFrame, threshold: float, 
                                   label_column: Optional[str]) -> pd.DataFrame:
        """Drop columns with missing values above threshold"""
        missing_ratio = df.isnull().sum() / len(df)
        cols_to_drop = missing_ratio[missing_ratio > threshold].index.tolist()
        
        # Never drop the label column
        if label_column and label_column in cols_to_drop:
            cols_to_drop.remove(label_column)
        
        if cols_to_drop:
            log(f"🗑️ Dropping columns with >{threshold*100}% missing: {cols_to_drop}")
        
        return df.drop(columns=cols_to_drop)
    
    def _handle_missing_values(self, df: pd.DataFrame, method: str, 
                              label_column: Optional[str]) -> pd.DataFrame:
        """Handle missing values based on specified method"""
        if method == "drop":
            return df.dropna()
        
        elif method in ["mean", "median", "mode", "zero"]:
            df_filled = df.copy()
            
            for col in df.columns:
                if df[col].isnull().any():
                    if df[col].dtype in ['float64', 'int64']:
                        if method == "mean":
                            df_filled[col].fillna(df[col].mean(), inplace=True)
                        elif method == "median":
                            df_filled[col].fillna(df[col].median(), inplace=True)
                        elif method == "zero":
                            df_filled[col].fillna(0, inplace=True)
                        elif method == "mode":
                            mode_val = df[col].mode()
                            if len(mode_val) > 0:
                                df_filled[col].fillna(mode_val[0], inplace=True)
                    else:
                        # For non-numeric columns, use mode or forward fill
                        mode_val = df[col].mode()
                        if len(mode_val) > 0:
                            df_filled[col].fillna(mode_val[0], inplace=True)
                        else:
                            df_filled[col].fillna(method='ffill', inplace=True)
                            df_filled[col].fillna(method='bfill', inplace=True)
            
            return df_filled
        
        return df
    
    def _remove_constant_columns(self, df: pd.DataFrame, 
                                label_column: Optional[str]) -> pd.DataFrame:
        """Remove columns with constant values"""
        constant_cols = []
        for col in df.columns:
            if col != label_column and df[col].nunique() <= 1:
                constant_cols.append(col)
        
        if constant_cols:
            log(f"🔒 Removing constant columns: {constant_cols}")
        
        return df.drop(columns=constant_cols)
    
    def _remove_highly_correlated(self, df: pd.DataFrame, threshold: float,
                                  label_column: Optional[str]) -> pd.DataFrame:
        """Remove highly correlated features"""
        # Get numeric columns only
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove label column from correlation analysis
        if label_column and label_column in numeric_cols:
            numeric_cols.remove(label_column)
        
        if len(numeric_cols) < 2:
            return df
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr().abs()
        
        # Find highly correlated pairs
        upper_tri = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Find features to drop
        to_drop = []
        for column in upper_tri.columns:
            if column in to_drop:
                continue
            correlated_features = list(upper_tri.index[upper_tri[column] > threshold])
            to_drop.extend(correlated_features)
        
        to_drop = list(set(to_drop))
        
        if to_drop:
            log(f"🔗 Removing highly correlated features: {to_drop}")
        
        return df.drop(columns=to_drop)
    
    def _remove_outliers(self, df: pd.DataFrame, method: str, threshold: float,
                        label_column: Optional[str]) -> pd.DataFrame:
        """Remove outliers using specified method"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Don't remove outliers from label column
        if label_column and label_column in numeric_cols:
            numeric_cols.remove(label_column)
        
        if not numeric_cols:
            return df
        
        if method == "iqr":
            # IQR method
            Q1 = df[numeric_cols].quantile(0.25)
            Q3 = df[numeric_cols].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            # Create mask for outliers
            mask = True
            for col in numeric_cols:
                mask = mask & (df[col] >= lower_bound[col]) & (df[col] <= upper_bound[col])
            
            return df[mask]
        
        elif method == "zscore":
            # Z-score method
            z_scores = np.abs((df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std())
            mask = (z_scores < threshold).all(axis=1)
            return df[mask]
        
        return df
    
    def get_preprocessing_report(self) -> Dict[str, Any]:
        """Get a summary report of preprocessing steps applied"""
        return self.preprocessing_report
    
    def print_report(self):
        """Print a formatted preprocessing report"""
        report = self.preprocessing_report
        log("\n" + "="*50)
        log("📊 DATA PREPROCESSING REPORT")
        log("="*50)
        log(f"📏 Original shape: {report['original_shape']}")
        log(f"✅ Final shape: {report['final_shape']}")
        log(f"🗑️  Total rows removed: {report['rows_removed']}")
        log(f"📉 Total columns removed: {report['columns_removed']}")
        log("\n📋 Steps applied:")
        for step in report['steps_applied']:
            log(f"  ✔️  {step}")
        log("="*50 + "\n")