import mlflow
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class MLFlowClient:
    """MLflow tracking and model registry client"""
    
    def __init__(self):
        """Initialize MLflow client"""
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        logger.info(f"MLflow tracking URI set to {settings.MLFLOW_TRACKING_URI}")

    def start_run(self, experiment_name: str, run_name: str):
        """Start a new MLflow run"""
        try:
            mlflow.set_experiment(experiment_name)
            run = mlflow.start_run(run_name=run_name)
            logger.info(f"Started MLflow run: {run.info.run_id}")
            return run
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            raise

    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        try:
            for key, value in params.items():
                mlflow.log_param(key, value)
            logger.info(f"Logged {len(params)} parameters")
        except Exception as e:
            logger.error(f"Failed to log params: {e}")

    def log_metrics(self, metrics: Dict[str, float]):
        """Log metrics"""
        try:
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
            logger.info(f"Logged {len(metrics)} metrics")
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

    def log_artifact(self, local_path: str, artifact_path: str = "artifacts"):
        """Log artifact file"""
        try:
            mlflow.log_artifact(local_path, artifact_path)
            logger.info(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")

    def end_run(self, status: str = "FINISHED"):
        """End current run"""
        try:
            mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run with status: {status}")
        except Exception as e:
            logger.error(f"Failed to end run: {e}")

    def register_model(
        self,
        model_uri: str,
        model_name: str
    ) -> Optional[str]:
        """Register model in MLflow registry"""
        try:
            version = mlflow.register_model(model_uri, model_name)
            logger.info(f"Registered model: {model_name} version {version.version}")
            return version.version
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return None

    def get_best_run(self, experiment_name: str, metric: str = "mAP"):
        """Get best run by metric"""
        try:
            mlflow.set_experiment(experiment_name)
            experiment = mlflow.get_experiment_by_name(experiment_name)
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric} DESC"]
            )
            if runs.empty:
                return None
            return runs.iloc[0]
        except Exception as e:
            logger.error(f"Failed to get best run: {e}")
            return None

# Singleton instance
_mlflow_instance: Optional[MLFlowClient] = None

def get_mlflow() -> MLFlowClient:
    """Get or create MLflow client"""
    global _mlflow_instance
    if _mlflow_instance is None:
        _mlflow_instance = MLFlowClient()
    return _mlflow_instance
