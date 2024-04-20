import math

import numpy as np

from .base import CKABase

Array = np.ndarray


class CKANumPy(CKABase):
    def __init__(
        self, m: int, kernel: str, unbiased: bool = False, sigma: float = None
    ) -> None:
        super().__init__(m=m, kernel=kernel, unbiased=unbiased, sigma=sigma)

    def centering(self, K: Array) -> Array:
        """Centering of the gram matrix K."""
        if not np.allclose(K, K.T, rtol=1e-03, atol=1e-04):
            raise ValueError("\nInput array must be a symmetric matrix.\n")
        if self.unbiased:
            # This formulation of the U-statistic, from Szekely, G. J., & Rizzo, M.
            # L. (2014). Partial distance correlation with methods for dissimilarities.
            # The Annals of Statistics, 42(6), 2382-2412, seems to be more numerically
            # stable than the alternative from Song et al. (2007).
            n = K.shape[0]
            np.fill_diagonal(K, 0.0)
            means = np.sum(K, axis=0, dtype=np.float64) / (n - 2)
            means -= np.sum(means) / (2 * (n - 1))
            K -= means[:, None]
            K -= means[None, :]
            np.fill_diagonal(K, 0.0)
        else:
            means = np.mean(K, axis=0, dtype=np.float64)
            means -= np.mean(means) / 2
            K -= means[:, None]
            K -= means[None, :]
        return K

    def apply_kernel(self, X: Array) -> Array:
        """Compute the gram matrix K."""
        try:
            K = getattr(self, f"{self.kernel}_kernel")(X)
        except AttributeError:
            raise NotImplementedError
        return K

    def linear_kernel(self, X: Array) -> Array:
        return X @ X.T

    def rbf_kernel(self, X: Array, sigma: float = None) -> Array:
        GX = X @ X.T
        KX = np.diag(GX) - GX + (np.diag(GX) - GX).T
        if sigma is None:
            mdist = np.median(KX[KX != 0])
            sigma = math.sqrt(mdist)
        KX *= -0.5 / sigma**2
        KX = np.exp(KX)
        return KX

    def _hsic(self, X: Array, Y: Array) -> float:
        K = self.apply_kernel(X)
        L = self.apply_kernel(Y)
        K_c = self.centering(K)
        L_c = self.centering(L)
        # np.sum(K_c * L_c) is equivalent to K_c.flatten() @ L_c.flatten() or in math
        # sum_{i=0}^{m} sum_{j=0}^{m} K^{\prime}_{ij} * L^{\prime}_{ij} = vec(K_c)^{T}vec(L_c)
        return np.sum(K_c * L_c)

    def compare(self, X: Array, Y: Array) -> float:
        hsic_xy = self._hsic(X, Y)
        hsic_xx = self._hsic(X, X)
        hsic_yy = self._hsic(Y, Y)
        rho = hsic_xy / np.sqrt(hsic_xx * hsic_yy)
        return rho
