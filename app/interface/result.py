from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MilestoneData(BaseModel):
    phase: str
    time: float
    fill: str

class Summary(BaseModel):
    model: str
    milestoneData: List[MilestoneData]
    rmse: Optional[float] = None  # Optional for linear regression
    r2: Optional[float] = None  # Optional for linear regression
    accuracy: Optional[float] = None  # Optional for logistic regression
    f1: Optional[float] = None  # Optional for logistic regression
    epochs: int
    lr: float
    modelPath: Optional[str] = None  # Path to saved model pickle file
    modelSize: Optional[str] = None  # Size of model file (e.g., "1.5 KB", "2.3 MB")

class Config(BaseModel):
    dataCount: int
    parties: int

class Coefficient(BaseModel):
    feature: str
    value: float
    type: str

class ActualVsPredicted(BaseModel):
    actual: List[float]
    predicted: List[float]

class AucRocData(BaseModel):
    fpr: List[float]  # False Positive Rate
    tpr: List[float]  # True Positive Rate
    auc: float    # Area Under Curve

class SessionResult(BaseModel):
    summary: Summary
    config: Config
    coefficients: List[Coefficient]
    actualVsPredicted: ActualVsPredicted
    aucRocData: Optional[AucRocData] = None  # Optional, only for logistic regression