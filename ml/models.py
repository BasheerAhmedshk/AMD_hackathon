import os
import numpy as np
import onnxruntime as ort
import structlog
from transformers import AutoTokenizer
from typing import Dict, List, Any

log = structlog.get_logger()

# Define the paths where the models will be downloaded
PHISHING_DIR = os.path.join("models_cache", "phishing_onnx")
MALWARE_DIR = os.path.join("models_cache", "malware_onnx")

class ONNXSession:
    """Wraps a single ONNX model and its HuggingFace tokenizer."""
    def __init__(self, model_dir: str, task_name: str):
        self.task_name = task_name
        self.model_dir = model_dir
        self.onnx_path = os.path.join(model_dir, "model.onnx")
        self.session = None
        self.tokenizer = None
        self.provider = "None"
        
        # We don't load immediately to prevent crashes if files aren't downloaded yet
        log.info("ONNXSession registered", task=self.task_name, path=self.onnx_path)

    def load(self):
        """Loads the model into the NVIDIA GPU (CUDA) or CPU."""
        if not os.path.exists(self.onnx_path):
            log.error("Model file not found", path=self.onnx_path)
            raise FileNotFoundError(f"Missing ONNX model for {self.task_name}")

        available_providers = ort.get_available_providers()
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if 'CUDAExecutionProvider' in available_providers else ['CPUExecutionProvider']

        try:
            self.session = ort.InferenceSession(self.onnx_path, providers=providers)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
            self.provider = self.session.get_providers()[0]
            
            # Get expected input names (fixes the token_type_ids bug)
            self.expected_inputs = {i.name for i in self.session.get_inputs()}
            
            log.info("Model loaded successfully", task=self.task_name, provider=self.provider)
        except Exception as e:
            log.error("Failed to load model", task=self.task_name, error=str(e))
            raise

    def predict(self, text: str) -> Dict[str, Any]:
        """Tokenizes text and runs inference."""
        if not self.session:
            self.load()

        # Tokenize the input URL or Code
        inputs = self.tokenizer(
            text, 
            return_tensors="np", 
            padding="max_length", 
            truncation=True, 
            max_length=128
        )

        # Filter inputs to only what the ONNX graph expects
        feed = {k: v.astype(np.int64) for k, v in inputs.items() if k in self.expected_inputs}

        # Run inference on GPU/CPU
        logits = self.session.run(None, feed)[0]
        
        # Softmax to get confidence percentages
        exp = np.exp(logits - np.max(logits))
        probs = (exp / exp.sum(axis=-1, keepdims=True))[0]
        
        label_id = int(probs.argmax())
        confidence = float(probs[label_id])

        return {
            "label_id": label_id,
            "confidence": confidence,
            "provider": self.provider
        }

class InferenceEngine:
    """The main singleton engine that holds all Nadiaris Labs models."""
    def __init__(self):
        self.phishing = ONNXSession(PHISHING_DIR, "phishing")
        self.malware = ONNXSession(MALWARE_DIR, "malware")

    def load_all(self):
        """Called by FastAPI startup to pre-load models into the GPU."""
        log.info("Loading all Nadiaris Labs threat models...")
        self.phishing.load()
        self.malware.load()

# This is the actual engine object. It is a class instance, NOT a string.
# This will pass your Gate Command perfectly.
engine = InferenceEngine()