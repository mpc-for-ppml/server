# modules/mpc/linear.py

from mpyc.runtime import mpc
from utils.cli_parser import print_log
from utils.constant import DEFAULT_EPOCHS, DEFAULT_LR

def log(msg):
    print_log(mpc.pid, msg)
    
class SecureLinearRegression:
    def __init__(self, epochs=DEFAULT_EPOCHS, lr=DEFAULT_LR, is_logging=False):
        self.epochs = epochs
        self.lr = lr
        self.is_logging = is_logging
        self.theta = None  # Model parameters
        self.secfx = mpc.SecFxp()

    async def fit(self, X_parts, y_parts):
        """Securely train linear regression using gradient descent.

        Args:
            X_parts (List[List[List[secfx]]]): List of X matrices from parties (all combined).
            y_parts (List[List[secfx]]): List of y vectors from parties (all combined).
        """
        
        # Concatenate data from all parties (already flattened)
        X = X_parts[0]  # shape: (n_samples, n_features)
        y = y_parts[0]  # shape: (n_samples,)
        n_samples = len(y)
        n_features = len(X[0])

        log(f"✅ Loaded {n_samples} samples, {n_features} features")
        
        # Initialize theta (model weights) to zeros
        theta = [self.secfx(0) for _ in range(n_features)]
        lr_sec = self.secfx(self.lr)

        log(f"🔎 Start learning with {self.epochs} iterations and learning rate {self.lr}")
        if not self.is_logging:
            log("🧮 Please wait, the training process is currently on progress...")
            
        for epoch in range(self.epochs):
            # Compute predictions: y_pred = X @ theta
            y_pred = [sum(x_i[j] * theta[j] for j in range(n_features)) for x_i in X]
            
            # Compute error = y_pred - y
            error = [y_pred[i] - y[i] for i in range(n_samples)]

            # Compute gradients
            gradients = []
            for j in range(n_features):
                grad_j = sum(error[i] * X[i][j] for i in range(n_samples)) / n_samples
                gradients.append(grad_j)

            # Update theta
            theta = [theta[j] - lr_sec * gradients[j] for j in range(n_features)]
            
            # Logging: Print theta every 10 iterations
            if self.is_logging:
                if epoch % 10 == 0 or epoch == self.epochs - 1:
                    theta_debug = await mpc.output(theta)
                    log(f"🧮 Epoch {epoch + 1}: theta = {[float(t) for t in theta_debug]}")

        # Reveal model weights to all parties
        log(f"⌛ Reaching final training epoch...")
        try:
            theta_open = await mpc.output(theta)
            self.theta = [float(t) for t in theta_open]
            if self.is_logging:
                log(f"✅ Training complete. Model weights: {self.theta}")
            else:
                log("✅ Training complete.")
        except Exception as e:
            log(f"❗ ERROR during mpc.output: {e}")
            self.theta = []

    async def predict(self, X_input):
        """Securely predict using the trained model.

        Args:
            X_input (List[List[secfx]]): New input data (securely shared, same format).

        Returns:
            List[float]: Predicted values.
        """
        if self.theta is None:
            raise ValueError("Model not trained. Call fit() before predict().")

        theta_sec = [self.secfx(t) for t in self.theta]
        predictions = [sum(x_i[j] * theta_sec[j] for j in range(len(theta_sec))) for x_i in X_input]

        try:
            preds_open = await mpc.output(predictions)
            return [float(p) for p in preds_open]
        except Exception as e:
            log(f"❗ ERROR during prediction output: {e}")
            return []
