from typing import Dict, Any
import psutil
import platform
import time
from datetime import datetime, timezone
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

# Store start time for uptime calculation
start_time = time.time()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint that returns the current status of the application.
    """
    current_time = time.time()
    uptime_seconds = current_time - start_time
    
    # Get system information
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu_percent = psutil.cpu_percent(interval=1)
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "uptime_human": format_uptime(uptime_seconds),
        "version": "1.0.0",
        "service": "MPC PPML Server",
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 2)
            }
        }
    }
    
    return health_data

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes/container orchestration.
    """
    try:
        # Add any specific readiness checks here
        # For example: database connectivity, external service availability, etc.
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "application": "ready"
                # Add more checks as needed:
                # "database": "ready",
                # "redis": "ready",
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )

@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes/container orchestration.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def format_uptime(seconds: float) -> str:
    """Format uptime in human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {secs}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"