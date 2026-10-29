"""
SatyaDrishti - Convolutional Neural Network (CNN) Classifier
Implements Equations (1), (2), (4) from the IEEE Research Paper:
- Convolution operation: F = I * K (Eq. 1)
- ReLU activation: f(x) = max(0, x) (Eq. 2)
- Binary Cross Entropy Loss: L = -(1/N) sum[y*log(p) + (1-y)*log(1-p)] (Eq. 4)
- Sigmoid output for Fake (1) vs Genuine (0) classification probability
"""

import os
import numpy as np
from PIL import Image

class ComplaintCNNClassifier:
    def __init__(self, weights_path=None, target_size=(128, 128)):
        self.target_size = target_size
        self.weights_path = weights_path or os.path.join(os.path.dirname(__file__), "models", "cnn_weights.npz")
        
        # Convolution kernels for visual anomaly detection (Edge, Texture, Laplacian, Splicing Boundary)
        self.kernels = self._init_conv_kernels() # shape: (8, 3, 3)
        self.num_kernels = len(self.kernels)
        
        # Dense layer weights: feature map dimension -> hidden (64) -> output (1)
        # Downsampled 128x128 through 2x2 max pool -> 64x64, global pooling / spatial patches = 8 * 8 = 64
        self.input_dim = 64 * self.num_kernels
        self.hidden_dim = 32
        
        self.W1 = None
        self.b1 = None
        self.W2 = None
        self.b2 = None
        
        self._init_or_load_weights()

    def _init_conv_kernels(self):
        """
        Initializes 8 convolutional kernels designed for computer vision forensics:
        - Horizontal, Vertical, Diagonal Sobel edge detectors
        - Laplacian high-frequency noise filter
        - Unsharp mask / compression boundary detector
        - Texture variance kernel
        """
        k = [
            # 1. Sobel Horizontal (edge discontinuities)
            np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32),
            # 2. Sobel Vertical
            np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32),
            # 3. Laplacian (high-frequency noise / tampering residuals)
            np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32),
            # 4. Diagonal 45-degree edge
            np.array([[0, 1, 2], [-1, 0, 1], [-2, -1, 0]], dtype=np.float32),
            # 5. Diagonal 135-degree edge
            np.array([[2, 1, 0], [1, 0, -1], [0, -1, -2]], dtype=np.float32),
            # 6. High-pass filter (detects copy-paste boundary artifacts)
            np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float32),
            # 7. Subtle blur detector (detects Gaussian smoothing used to hide tampering)
            np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float32) / 16.0,
            # 8. Gradient divergence filter
            np.array([[-1, 0, 1], [0, 0, 0], [1, 0, -1]], dtype=np.float32)
        ]
        return np.array(k)

    def _init_or_load_weights(self):
        """Loads saved weights from file or initializes Xavier weights."""
        if os.path.exists(self.weights_path):
            try:
                data = np.load(self.weights_path)
                self.W1 = data["W1"]
                self.b1 = data["b1"]
                self.W2 = data["W2"]
                self.b2 = data["b2"]
                return
            except Exception:
                pass

        # Xavier initialization
        np.random.seed(42)
        self.W1 = np.random.randn(self.input_dim, self.hidden_dim).astype(np.float32) * np.sqrt(2.0 / self.input_dim)
        self.b1 = np.zeros((1, self.hidden_dim), dtype=np.float32)
        self.W2 = np.random.randn(self.hidden_dim, 1).astype(np.float32) * np.sqrt(2.0 / self.hidden_dim)
        self.b2 = np.zeros((1, 1), dtype=np.float32)

    def save_weights(self):
        """Saves weights to disk."""
        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
        np.savez(self.weights_path, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2)

    def preprocess_image(self, image_path: str):
        """
        Preprocesses uploaded image:
        - Resize to target size (128x128)
        - Normalization to [0, 1]
        - Grayscale conversion for kernel convolutions
        """
        img = Image.open(image_path).convert('RGB')
        img_resized = img.resize(self.target_size, Image.Resampling.BILINEAR)
        arr = np.array(img_resized, dtype=np.float32) / 255.0
        
        # Grayscale channel for convolution
        gray = 0.2989 * arr[:, :, 0] + 0.5870 * arr[:, :, 1] + 0.1140 * arr[:, :, 2]
        return arr, gray

    def _convolve2d(self, image: np.ndarray, kernel: np.ndarray):
        """Vectorized 2D Convolution (Eq. 1): F = I * K with valid/same padding."""
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
        
        # Strided window extraction
        sub_matrices = np.lib.stride_tricks.sliding_window_view(padded, (kh, kw))
        # Convolution is sum of element-wise product
        conv_res = np.sum(sub_matrices * kernel, axis=(-2, -1))
        return conv_res

    def _max_pool2d(self, feature_map: np.ndarray, pool_size=2):
        """2x2 Max Pooling layer."""
        h, w = feature_map.shape
        h_pool = h // pool_size
        w_pool = w // pool_size
        cropped = feature_map[:h_pool * pool_size, :w_pool * pool_size]
        reshaped = cropped.reshape(h_pool, pool_size, w_pool, pool_size)
        return reshaped.max(axis=(1, 3))

    def _relu(self, x):
        """ReLU activation (Eq. 2): f(x) = max(0, x)"""
        return np.maximum(0.0, x)

    def _sigmoid(self, z):
        """Sigmoid activation for binary classification."""
        return 1.0 / (1.0 + np.exp(-np.clip(z, -15.0, 15.0)))

    def extract_features(self, gray_image: np.ndarray):
        """
        Extracts feature vectors by applying convolution kernels, ReLU, max pooling,
        and spatial grid reduction.
        """
        feature_vectors = []
        for i in range(self.num_kernels):
            kernel = self.kernels[i]
            # Convolution (Eq. 1)
            f_map = self._convolve2d(gray_image, kernel)
            # ReLU (Eq. 2)
            act_map = self._relu(f_map)
            # Max pooling (Pool size 2)
            pooled = self._max_pool2d(act_map, pool_size=2) # 64x64
            
            # Spatial block pooling to 8x8 = 64 features per kernel
            block_h = pooled.shape[0] // 8
            block_w = pooled.shape[1] // 8
            blocks = pooled.reshape(8, block_h, 8, block_w).mean(axis=(1, 3))
            feature_vectors.append(blocks.flatten())
            
        concat_features = np.concatenate(feature_vectors).reshape(1, -1)
        return concat_features

    def forward(self, features: np.ndarray):
        """Forward pass through Dense layers."""
        z1 = np.dot(features, self.W1) + self.b1
        a1 = self._relu(z1)
        z2 = np.dot(a1, self.W2) + self.b2
        p_fake = self._sigmoid(z2)[0, 0]
        return float(p_fake)

    def predict(self, image_path: str):
        """
        Classifies an uploaded complaint image.
        Returns:
            s_img (float 0.0 - 1.0): Probability of fake / manipulated image
            confidence (float): Classification confidence
            feature_summary (dict): Detected visual anomaly metrics
        """
        try:
            _, gray = self.preprocess_image(image_path)
            features = self.extract_features(gray)
            
            # Compute raw CNN fake probability
            p_fake = self.forward(features)
            
            # Extract forensic visual indicators from features
            high_freq_energy = float(features[0, 64*2:64*3].mean()) # Laplacian
            edge_anomaly = float(features[0, :64*2].std()) # Sobel variance
            splicing_boundary = float(features[0, 64*5:64*6].mean()) # High pass
            
            # Refine s_img with direct texture & boundary anomaly signals
            anomaly_boost = 0.0
            if splicing_boundary > 0.4:
                anomaly_boost += 0.15
            if high_freq_energy > 0.35:
                anomaly_boost += 0.10
                
            s_img = min(1.0, max(0.0, p_fake * 0.75 + anomaly_boost))
            
            is_fake = s_img >= 0.50
            confidence = round(abs(s_img - 0.5) * 2.0 * 100, 1)

            return {
                "s_img": round(s_img, 4),
                "is_fake": bool(is_fake),
                "confidence_pct": confidence,
                "label": "Fake" if is_fake else "Genuine",
                "metrics": {
                    "edge_anomaly": round(edge_anomaly, 4),
                    "high_freq_noise": round(high_freq_energy, 4),
                    "boundary_artifact_score": round(splicing_boundary, 4)
                }
            }
        except Exception as e:
            return {
                "s_img": 0.25,
                "is_fake": False,
                "confidence_pct": 50.0,
                "label": "Genuine",
                "error": str(e),
                "metrics": {}
            }

    def train_step(self, features_list, labels, lr=0.01):
        """
        Single training step using Binary Cross Entropy Loss (Eq. 4)
        """
        X = np.vstack(features_list)
        y = np.array(labels, dtype=np.float32).reshape(-1, 1)
        N = X.shape[0]

        # Forward
        z1 = np.dot(X, self.W1) + self.b1
        a1 = self._relu(z1)
        z2 = np.dot(a1, self.W2) + self.b2
        p = self._sigmoid(z2)

        # Loss (Eq. 4)
        eps = 1e-7
        loss = -np.mean(y * np.log(p + eps) + (1.0 - y) * np.log(1.0 - p + eps))

        # Backward
        dz2 = (p - y) / N
        dW2 = np.dot(a1.T, dz2)
        db2 = np.sum(dz2, axis=0, keepdims=True)

        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * (z1 > 0)
        dW1 = np.dot(X.T, dz1)
        db1 = np.sum(dz1, axis=0, keepdims=True)

        # Update weights
        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        self.W2 -= lr * dW2
        self.b2 -= lr * db2

        return float(loss)
