import pickle
import os
from typing import List, Dict
import math

class PredictionService:
    """Service for making predictions using trained MPC models outside of MPC runtime"""
    
    @staticmethod
    def sigmoid(x: float) -> float:
        """Standard sigmoid function"""
        return 1 / (1 + math.exp(-x))
    
    @staticmethod
    def predict_linear(theta: List[float], features: List[float]) -> float:
        """
        Linear regression prediction: y = X @ theta
        Matches the logic in SecureLinearRegression.predict()
        """
        if len(features) != len(theta):
            raise ValueError(f"Feature dimension mismatch: got {len(features)}, expected {len(theta)}")
        
        # Compute dot product
        prediction = sum(features[i] * theta[i] for i in range(len(theta)))
        return prediction
    
    @staticmethod
    def predict_logistic(theta: List[float], features: List[float]) -> float:
        """
        Logistic regression prediction: binary classification based on sigmoid(X @ theta)
        Matches the logic in SecureLogisticRegression.predict()
        Note: In the MPC version, bias is included as the last element of theta
        Returns: 0 or 1 (binary prediction)
        """
        if len(features) != len(theta):
            raise ValueError(f"Feature dimension mismatch: got {len(features)}, expected {len(theta)}")
        
        # Compute dot product
        dot_product = sum(features[i] * theta[i] for i in range(len(theta)))
        
        # Apply sigmoid
        probability = PredictionService.sigmoid(dot_product)
        
        # Convert to binary prediction (0 or 1)
        return 1 if probability >= 0.5 else 0
    
    @staticmethod
    def load_model_and_predict(model_path: str, data_points: List[Dict[str, float]]) -> List[float]:
        """
        Load a trained model and make predictions on multiple data points
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load model data
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)
        
        theta = model_data["theta"]
        regression_type = model_data["regression_type"]
        feature_names = model_data["feature_names"]
        
        predictions = []
        
        for data_point in data_points:
            # Extract features in the correct order
            features = [data_point[feature] for feature in feature_names]
            
            # Add bias term (always 1.0)
            features.append(1.0)
            
            # Make prediction based on model type
            if regression_type == "linear":
                prediction = PredictionService.predict_linear(theta, features)
            else:  # logistic
                prediction = PredictionService.predict_logistic(theta, features)
            
            predictions.append(prediction)
        
        return predictions