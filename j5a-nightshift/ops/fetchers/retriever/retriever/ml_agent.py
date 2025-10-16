"""
MLAgent - Machine Learning model inference with scikit-learn, PyTorch, TensorFlow
"""
from __future__ import annotations
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np
from .base import BaseAgent

logger = logging.getLogger(__name__)


class MLAgent(BaseAgent):
    """
    Runs inference with ML models (scikit-learn, PyTorch, TensorFlow)

    Supports:
    - scikit-learn models (pickle/joblib)
    - PyTorch models (.pt, .pth)
    - TensorFlow/Keras models (.h5, SavedModel)
    - Batch prediction
    - Model metadata extraction
    - Feature preprocessing
    """

    def __init__(
        self,
        model_cache_dir: Optional[str] = None,
        batch_size: int = 32,
        device: str = 'cpu'
    ):
        """
        Initialize MLAgent

        Args:
            model_cache_dir: Directory to cache loaded models
            batch_size: Batch size for predictions
            device: Device for PyTorch/TensorFlow ('cpu', 'cuda', 'mps')
        """
        self.model_cache_dir = Path(model_cache_dir) if model_cache_dir else None
        self.batch_size = batch_size
        self.device = device
        self.loaded_models = {}  # Model cache

    def supports(self, target: Any) -> bool:
        """Check if target is an ML operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        return target_type in ('ml', 'model', 'inference', 'predict')

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Run ML model inference

        Target structure:
            {
                'type': 'ml',
                'model_path': '/path/to/model.pkl',
                'framework': 'sklearn' | 'pytorch' | 'tensorflow' (optional, auto-detected),
                'operation': 'predict' | 'predict_proba' | 'info' (default 'predict'),
                'input_data': [[...], [...]] or np.array,
                'preprocess': 'standardize' | 'normalize' | None,
                'postprocess': 'argmax' | 'sigmoid' | 'softmax' | None,
                'batch_size': 32 (optional)
            }

        Returns:
            {
                'predictions': [...],
                'prediction_count': 100,
                'model_info': {
                    'framework': 'sklearn',
                    'model_type': 'RandomForestClassifier',
                    'input_shape': (None, 10),
                    'output_shape': (None, 2)
                },
                'meta': {
                    'method': 'ml',
                    'operation': 'predict',
                    'inference_time_ms': 123
                }
            }
        """
        import time

        start_time = time.time()

        model_path = target.get('model_path')
        if not model_path:
            raise ValueError("model_path required")

        operation = target.get('operation', 'predict').lower()

        # Load model
        model, framework = self._load_model(model_path, target.get('framework'))

        if operation == 'info':
            # Return model information only
            model_info = self._get_model_info(model, framework)
            return {
                'model_info': model_info,
                'meta': {
                    'method': 'ml',
                    'operation': 'info',
                    'framework': framework
                }
            }

        # Get input data
        input_data = target.get('input_data')
        if input_data is None:
            raise ValueError("input_data required for prediction")

        # Convert to numpy array
        if not isinstance(input_data, np.ndarray):
            input_data = np.array(input_data)

        # Preprocess if specified
        preprocess = target.get('preprocess')
        if preprocess:
            input_data = self._preprocess(input_data, preprocess)

        # Run inference
        predictions = self._predict(model, framework, input_data, operation, target)

        # Postprocess if specified
        postprocess = target.get('postprocess')
        if postprocess:
            predictions = self._postprocess(predictions, postprocess)

        inference_time_ms = int((time.time() - start_time) * 1000)

        model_info = self._get_model_info(model, framework)

        return {
            'predictions': predictions.tolist() if isinstance(predictions, np.ndarray) else predictions,
            'prediction_count': len(predictions),
            'model_info': model_info,
            'meta': {
                'method': 'ml',
                'operation': operation,
                'framework': framework,
                'inference_time_ms': inference_time_ms
            }
        }

    def _load_model(self, model_path: str, framework_hint: Optional[str] = None):
        """Load model from disk"""
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Check cache
        cache_key = str(model_path.resolve())
        if cache_key in self.loaded_models:
            logger.info(f"Using cached model: {model_path}")
            return self.loaded_models[cache_key]

        # Auto-detect framework if not specified
        if not framework_hint:
            framework_hint = self._detect_framework(model_path)

        logger.info(f"Loading {framework_hint} model from {model_path}")

        if framework_hint == 'sklearn':
            model = self._load_sklearn(model_path)
        elif framework_hint == 'pytorch':
            model = self._load_pytorch(model_path)
        elif framework_hint == 'tensorflow':
            model = self._load_tensorflow(model_path)
        else:
            raise ValueError(f"Unknown framework: {framework_hint}")

        # Cache model
        self.loaded_models[cache_key] = (model, framework_hint)

        return model, framework_hint

    def _detect_framework(self, model_path: Path) -> str:
        """Auto-detect ML framework from file extension"""
        suffix = model_path.suffix.lower()

        if suffix in ('.pkl', '.pickle', '.joblib'):
            return 'sklearn'
        elif suffix in ('.pt', '.pth'):
            return 'pytorch'
        elif suffix in ('.h5', '.keras'):
            return 'tensorflow'
        elif model_path.is_dir():
            # TensorFlow SavedModel format
            if (model_path / 'saved_model.pb').exists():
                return 'tensorflow'

        raise ValueError(f"Cannot auto-detect framework for {model_path}")

    def _load_sklearn(self, model_path: Path):
        """Load scikit-learn model"""
        import joblib

        if model_path.suffix == '.joblib':
            return joblib.load(model_path)
        else:
            with open(model_path, 'rb') as f:
                return pickle.load(f)

    def _load_pytorch(self, model_path: Path):
        """Load PyTorch model"""
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch not installed - install with: pip install torch")

        model = torch.load(model_path, map_location=self.device)

        # Handle different save formats
        if isinstance(model, dict):
            # State dict format - need model architecture
            raise ValueError("PyTorch state_dict requires model architecture")

        model.eval()  # Set to evaluation mode
        return model

    def _load_tensorflow(self, model_path: Path):
        """Load TensorFlow/Keras model"""
        try:
            import tensorflow as tf
        except ImportError:
            raise ImportError("TensorFlow not installed - install with: pip install tensorflow")

        if model_path.is_dir():
            # SavedModel format
            return tf.keras.models.load_model(str(model_path))
        else:
            # HDF5 format
            return tf.keras.models.load_model(str(model_path))

    def _predict(
        self,
        model,
        framework: str,
        input_data: np.ndarray,
        operation: str,
        target: Dict[str, Any]
    ):
        """Run model inference"""
        batch_size = target.get('batch_size', self.batch_size)

        if framework == 'sklearn':
            return self._predict_sklearn(model, input_data, operation)
        elif framework == 'pytorch':
            return self._predict_pytorch(model, input_data, batch_size)
        elif framework == 'tensorflow':
            return self._predict_tensorflow(model, input_data, batch_size)

    def _predict_sklearn(self, model, input_data: np.ndarray, operation: str):
        """Predict with scikit-learn model"""
        if operation == 'predict_proba' and hasattr(model, 'predict_proba'):
            return model.predict_proba(input_data)
        else:
            return model.predict(input_data)

    def _predict_pytorch(self, model, input_data: np.ndarray, batch_size: int):
        """Predict with PyTorch model"""
        import torch

        model.eval()
        predictions = []

        with torch.no_grad():
            # Process in batches
            for i in range(0, len(input_data), batch_size):
                batch = input_data[i:i + batch_size]
                batch_tensor = torch.tensor(batch, dtype=torch.float32).to(self.device)

                output = model(batch_tensor)

                # Move to CPU and convert to numpy
                predictions.append(output.cpu().numpy())

        return np.vstack(predictions)

    def _predict_tensorflow(self, model, input_data: np.ndarray, batch_size: int):
        """Predict with TensorFlow model"""
        return model.predict(input_data, batch_size=batch_size, verbose=0)

    def _preprocess(self, data: np.ndarray, method: str) -> np.ndarray:
        """Preprocess input data"""
        if method == 'standardize':
            # Z-score normalization
            mean = data.mean(axis=0)
            std = data.std(axis=0)
            return (data - mean) / (std + 1e-8)

        elif method == 'normalize':
            # Min-max normalization
            min_val = data.min(axis=0)
            max_val = data.max(axis=0)
            return (data - min_val) / (max_val - min_val + 1e-8)

        return data

    def _postprocess(self, predictions: np.ndarray, method: str) -> np.ndarray:
        """Postprocess predictions"""
        if method == 'argmax':
            return np.argmax(predictions, axis=1)

        elif method == 'sigmoid':
            return 1 / (1 + np.exp(-predictions))

        elif method == 'softmax':
            exp_preds = np.exp(predictions - predictions.max(axis=1, keepdims=True))
            return exp_preds / exp_preds.sum(axis=1, keepdims=True)

        return predictions

    def _get_model_info(self, model, framework: str) -> Dict[str, Any]:
        """Extract model metadata"""
        info = {
            'framework': framework,
            'model_type': type(model).__name__
        }

        if framework == 'sklearn':
            # Get feature count if available
            if hasattr(model, 'n_features_in_'):
                info['n_features'] = model.n_features_in_
            if hasattr(model, 'n_classes_'):
                info['n_classes'] = model.n_classes_

        elif framework == 'pytorch':
            import torch
            # Count parameters
            if isinstance(model, torch.nn.Module):
                info['parameter_count'] = sum(p.numel() for p in model.parameters())

        elif framework == 'tensorflow':
            # Get input/output shapes
            if hasattr(model, 'input_shape'):
                info['input_shape'] = model.input_shape
            if hasattr(model, 'output_shape'):
                info['output_shape'] = model.output_shape

        return info
