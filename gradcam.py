"""
Grad-CAM for PAN-MED.
Matches the exact logic from the training notebook (MobileNet backbone).
Returns both the raw heatmap overlay AND a side-by-side PIL image
(original | heatmap | overlay) identical to the Kaggle visualization.
"""

import numpy as np
import tensorflow as tf
import cv2
from PIL import Image


# ─── Layer Discovery ──────────────────────────────────────────────────────────

def _find_last_conv_layer(model):
    """
    Robustly find the last Conv2D layer name, even inside nested sub-models
    (e.g. MobileNetV2 / EfficientNet backbone wrapped in a Functional model).

    Strategy (mirrors the Kaggle notebook):
      1. Walk model.layers in reverse.
      2. If a layer IS a Conv2D → done.
      3. If a layer IS itself a Model (backbone) → recurse into its layers.
    Returns the (layer_name, owner_model) tuple so we can build the grad_model correctly.
    """

    # Pass 1: direct Conv2D in the top-level model
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name, model

    # Pass 2: Conv2D inside a nested sub-model (MobileNet, EfficientNet, etc.)
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.Model):
            for sublayer in reversed(layer.layers):
                if isinstance(sublayer, tf.keras.layers.Conv2D):
                    # We need to expose this sub-layer through the nested model
                    return sublayer.name, layer   # (conv_name, backbone_model)

    return None, None


# ─── Core Grad-CAM ────────────────────────────────────────────────────────────

def make_gradcam_heatmap(img_array, model, last_conv_layer_name, pred_class=None):
    """
    Exact port of the Kaggle make_gradcam_heatmap function.

    Args:
        img_array:            np.array shape (1, 224, 224, 3), float32, scaled 0-1
        model:                loaded tf.keras.Model
        last_conv_layer_name: str name of the Conv2D layer to hook
        pred_class:           int index of class to explain (None = argmax)

    Returns:
        heatmap: np.array (H, W) float32 in [0, 1]
    """
    # Build grad model — output is [conv_feature_map, final_predictions]
    grad_model = tf.keras.models.Model(
        inputs=model.inputs,
        outputs=[model.get_layer(last_conv_layer_name).output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        if pred_class is None:
            pred_class = tf.argmax(predictions[0]).numpy()
        class_channel = predictions[:, pred_class]

    # Gradients of predicted class score w.r.t. conv feature map
    grads = tape.gradient(class_channel, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # Weight each channel by its gradient magnitude
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    # ReLU + normalize to [0, 1]  — same as Kaggle code
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_gradcam_overlay(model, pil_image: Image.Image,
                              img_size=(224, 224)) -> Image.Image:
    """
    Generate a Grad-CAM overlay image (what gets shown in the Streamlit app).

    Uses cv2.addWeighted(original, 0.6, heatmap, 0.4, 0) — identical to Kaggle.

    Returns:
        PIL Image of the blended overlay at img_size resolution.
    """
    try:
        # ── Preprocess ──────────────────────────────────────────────────────
        img_resized = pil_image.resize(img_size)
        img_array  = np.array(img_resized, dtype=np.float32) / 255.0
        img_batch  = np.expand_dims(img_array, axis=0)        # (1,224,224,3)

        # ── Find last conv layer ─────────────────────────────────────────────
        conv_name, owner = _find_last_conv_layer(model)

        if conv_name is None:
            print("[GradCAM] No Conv2D layer found — returning fallback.")
            return _fallback_overlay(pil_image, img_size)

        print(f"[GradCAM] Using layer: '{conv_name}'")

        # ── Generate heatmap ─────────────────────────────────────────────────
        # If conv layer lives inside a nested backbone, expose it through that model
        target_model = model  # default: use top-level model
        try:
            model.get_layer(conv_name)          # works if layer is at top level
        except ValueError:
            # Layer is inside a nested sub-model — build a pass-through model
            # that reaches the backbone's conv output
            for layer in model.layers:
                if isinstance(layer, tf.keras.Model):
                    try:
                        layer.get_layer(conv_name)
                        # Build a model: original inputs → backbone conv → top output
                        target_model = tf.keras.models.Model(
                            inputs=model.inputs,
                            outputs=[layer.get_layer(conv_name).output, model.output]
                        )
                        # Use simplified heatmap path below
                        return _heatmap_from_prebuilt_grad_model(
                            target_model, img_batch, img_resized
                        )
                    except ValueError:
                        continue

        heatmap = make_gradcam_heatmap(img_batch, target_model, conv_name)

        # ── Resize heatmap → colormap → blend ────────────────────────────────
        return _blend(img_resized, heatmap, img_size)

    except Exception as e:
        print(f"[GradCAM] Error: {e}")
        import traceback; traceback.print_exc()
        return _fallback_overlay(pil_image, img_size)


def generate_gradcam_triplet(model, pil_image: Image.Image,
                              img_size=(224, 224)) -> Image.Image:
    """
    Returns a side-by-side PIL image: [Original | Heatmap | Overlay]
    Matches the Kaggle matplotlib visualization exactly.
    """
    try:
        img_resized = pil_image.resize(img_size)
        img_array  = np.array(img_resized, dtype=np.float32) / 255.0
        img_batch  = np.expand_dims(img_array, axis=0)

        conv_name, _ = _find_last_conv_layer(model)
        if conv_name is None:
            return _fallback_overlay(pil_image, img_size)

        try:
            model.get_layer(conv_name)
            heatmap = make_gradcam_heatmap(img_batch, model, conv_name)
        except ValueError:
            return _fallback_overlay(pil_image, img_size)

        # Build individual panels
        original_np = np.array(img_resized)

        h_resized   = cv2.resize(heatmap, img_size)
        h_uint8     = np.uint8(255 * h_resized)
        h_color_bgr = cv2.applyColorMap(h_uint8, cv2.COLORMAP_JET)
        h_color_rgb = cv2.cvtColor(h_color_bgr, cv2.COLOR_BGR2RGB)

        overlay = cv2.addWeighted(original_np, 0.6, h_color_rgb, 0.4, 0)

        # Concatenate horizontally
        triplet = np.concatenate([original_np, h_color_rgb, overlay], axis=1)
        return Image.fromarray(triplet.astype(np.uint8))

    except Exception as e:
        print(f"[GradCAM triplet] Error: {e}")
        return _fallback_overlay(pil_image, img_size)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _heatmap_from_prebuilt_grad_model(grad_model, img_batch, img_resized):
    """Used when conv layer is accessed via a pre-built grad model directly."""
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_batch)
        pred_class = tf.argmax(predictions[0])
        class_channel = predictions[:, pred_class]

    grads = tape.gradient(class_channel, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    return _blend(img_resized, heatmap.numpy(), (224, 224))


def _blend(img_resized: Image.Image, heatmap: np.ndarray, img_size) -> Image.Image:
    """Resize heatmap, apply JET colormap, blend with original — Kaggle style."""
    original_np = np.array(img_resized)

    h_resized   = cv2.resize(heatmap, img_size)
    h_uint8     = np.uint8(255 * h_resized)
    h_color_bgr = cv2.applyColorMap(h_uint8, cv2.COLORMAP_JET)
    h_color_rgb = cv2.cvtColor(h_color_bgr, cv2.COLOR_BGR2RGB)

    # cv2.addWeighted(src1, alpha, src2, beta, gamma)
    # original*0.6 + heatmap*0.4 — exact Kaggle formula
    overlay = cv2.addWeighted(original_np, 0.6, h_color_rgb, 0.4, 0)
    return Image.fromarray(overlay)


def _fallback_overlay(pil_image: Image.Image, img_size=(224, 224)) -> Image.Image:
    """Graceful fallback — returns original image resized."""
    return pil_image.resize(img_size)