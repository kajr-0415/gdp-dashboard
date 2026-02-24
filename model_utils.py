"""
Model utilities for PAN-MED.
Handles loading the Keras model and running inference.

TO USE YOUR OWN MODEL:
    Place your .h5 or .keras file in the same directory as this script,
    then set MODEL_PATH below to point to it.
"""

import numpy as np
import tensorflow as tf
from PIL import Image

# ─── Configuration ─────────────────────────────────────────────────────────
from pathlib import Path
_HERE = Path(__file__).resolve().parent

# Update the filename if yours differs
_MODEL_FILENAME = "model.keras"   # or "model.h5"
MODEL_PATH = _HERE / _MODEL_FILENAME
IMG_SIZE = (224, 224)
NUM_CLASSES = 13

# ─── Preprocessing ─────────────────────────────────────────────────────────
def preprocess_image(pil_image: Image.Image) -> np.ndarray:
    """Resize and normalize image for model input."""
    img = pil_image.resize(IMG_SIZE)
    img_array = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(img_array, axis=0)  # shape: (1, 224, 224, 3)


# ─── Model Loader ──────────────────────────────────────────────────────────
def load_model() -> tf.keras.Model:
    """
    Load the trained Keras model.
    Falls back to a dummy model if the file is not found (for development/demo).
    """
    if MODEL_PATH.exists():
        print(f"[PAN-MED] Loading model from {MODEL_PATH}...")
        model = tf.keras.models.load_model(str(MODEL_PATH))
        print("[PAN-MED] Model loaded successfully.")
        return model
    else:
        # Also try .keras extension
        keras_path = MODEL_PATH.with_suffix(".keras")
        if keras_path.exists():
            print(f"[PAN-MED] Loading model from {keras_path}...")
            return tf.keras.models.load_model(str(keras_path))
        print(f"[PAN-MED] No model file found at {MODEL_PATH}. Using DEMO model.")
        return _build_demo_model()


def _build_demo_model() -> tf.keras.Model:
    """
    Builds a lightweight demo CNN for UI testing without a real model file.
    Outputs 13-class softmax probabilities.
    Replace with your actual model.
    """
    inputs = tf.keras.Input(shape=(224, 224, 3), name="input_layer")
    x = tf.keras.layers.Conv2D(32, 3, activation="relu", padding="same", name="conv2d_1")(inputs)
    x = tf.keras.layers.MaxPooling2D()(x)
    x = tf.keras.layers.Conv2D(64, 3, activation="relu", padding="same", name="conv2d_2")(x)
    x = tf.keras.layers.MaxPooling2D()(x)
    x = tf.keras.layers.Conv2D(128, 3, activation="relu", padding="same", name="conv2d_3")(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    outputs = tf.keras.layers.Dense(NUM_CLASSES, activation="softmax", name="predictions")(x)
    model = tf.keras.Model(inputs, outputs, name="panmed_demo")
    return model


# ─── Inference ─────────────────────────────────────────────────────────────
def predict(model: tf.keras.Model, pil_image: Image.Image):
    """
    Run inference on a PIL image.

    Returns:
        diagnosis_idx  (int)   – index of the predicted class
        confidence     (float) – probability of the top class (0–1)
        all_probs      (np.array) – full softmax probability array
    """
    img_array = preprocess_image(pil_image)
    preds = model.predict(img_array, verbose=0)[0]  # shape: (NUM_CLASSES,)
    diagnosis_idx = int(np.argmax(preds))
    confidence = float(preds[diagnosis_idx])
    return diagnosis_idx, confidence, preds