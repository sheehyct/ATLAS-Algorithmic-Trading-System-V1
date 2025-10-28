"""
Academic Statistical Jump Model - Optimization Solver (Phase B)

This module implements the coordinate descent optimization algorithm with dynamic
programming for state sequence optimization, as specified in "Downside Risk Reduction
Using Regime-Switching Signals: A Statistical Jump Model Approach" (Shu et al.,
Princeton, 2024).

Optimization Problem:
    min_{Theta,S} Σ_{t=0}^{T-1} l(x_t, θ_{s_t}) + λ * Σ_{t=1}^{T-1} 1_{s_t ≠ s_{t-1}}

Where:
    - l(x, θ) = (1/2) ||x - θ||_2^2 (scaled squared Euclidean distance)
    - Θ = {θ_0, θ_1} (2 centroids for bull/bear states)
    - S = {s_0, ..., s_{T-1}} (state sequence, each s_t ∈ {0,1})
    - λ ≥ 0 (jump penalty - controls regime persistence)

Algorithm:
    1. Initialize Θ using K-means clustering
    2. Coordinate descent: Alternate E-step (optimize S via DP) and M-step (optimize Θ)
    3. Convergence: |objective_new - objective_old| < 1e-6
    4. Multi-start: 10 random initializations, keep best result

Academic Foundation:
    - 33 years empirical validation (1990-2023)
    - Proven Sharpe improvements: +42% to +158%
    - MaxDD reduction: ~50% across S&P 500/DAX/Nikkei
    - O(T*K²) = O(2T) complexity for K=2 states

Implementation Reference:
    Section 3.4.2 "Online Inference" in academic paper
    GitHub: Yizhan-Oliver-Shu/jump-models (reference implementation)
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from regime.academic_features import calculate_features


def _compute_loss(features: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """
    Compute loss l(x, theta) = (1/2) ||x - theta||_2^2 for all x and theta.

    Args:
        features: (T, D) feature matrix
        theta: (K, D) centroid matrix

    Returns:
        loss: (T, K) loss matrix where loss[t, k] = l(x_t, theta_k)

    Note:
        Uses scaled squared Euclidean distance per paper specification.
    """
    T, D = features.shape
    K = theta.shape[0]

    # Compute ||x_t - theta_k||^2 for all t, k
    # Broadcasting: features[:, None, :] is (T, 1, D), theta[None, :, :] is (1, K, D)
    diff = features[:, None, :] - theta[None, :, :]  # (T, K, D)
    squared_dist = np.sum(diff ** 2, axis=2)  # (T, K)

    # Scale by 1/2 per paper
    loss = 0.5 * squared_dist

    return loss


def dynamic_programming(
    features: np.ndarray,
    theta: np.ndarray,
    lambda_penalty: float
) -> Tuple[np.ndarray, float]:
    """
    Dynamic programming algorithm for optimal state sequence given fixed centroids.

    Solves the optimization problem:
        min_S Σ_{t=0}^{T-1} l(x_t, θ_{s_t}) + λ * Σ_{t=1}^{T-1} 1_{s_t ≠ s_{t-1}}

    Algorithm:
        DP[0][k] = l(x_0, θ_k) for all k ∈ {0,1}
        DP[t][k] = l(x_t, θ_k) + min_j(DP[t-1][j] + λ*1_{j≠k})
        Backtrack from argmin_k(DP[T-1][k])

    Complexity: O(T*K²) = O(2T) for K=2 states

    Args:
        features: (T, D) feature matrix
        theta: (K, D) centroid matrix (K=2 for bull/bear)
        lambda_penalty: Jump penalty (controls regime persistence)

    Returns:
        state_sequence: (T,) array of state assignments {0,1}
        objective_value: Final objective function value

    Reference:
        Section 3.4.2 "Online Inference" in Shu et al., Princeton 2024

    Example:
        >>> features = np.random.randn(100, 3)
        >>> theta = np.array([[0, 0, 0], [1, 1, 1]])
        >>> states, obj = dynamic_programming(features, theta, lambda_penalty=50.0)
        >>> print(f"Objective: {obj:.2f}, Switches: {(states[1:] != states[:-1]).sum()}")
    """
    T, D = features.shape
    K = theta.shape[0]

    # Validate inputs
    if K != 2:
        raise ValueError(f"Expected K=2 states, got {K}")
    if theta.shape[1] != D:
        raise ValueError(f"Theta dimension {theta.shape[1]} != features dimension {D}")
    if lambda_penalty < 0:
        raise ValueError(f"Lambda penalty must be >= 0, got {lambda_penalty}")

    # Compute loss matrix l(x_t, theta_k) for all t, k
    loss = _compute_loss(features, theta)  # (T, K)

    # Initialize DP table and backpointers
    dp = np.zeros((T, K))  # dp[t][k] = min cost to reach state k at time t
    backpointer = np.zeros((T, K), dtype=int)  # backpointer[t][k] = argmin for DP[t][k]

    # Base case: t=0
    dp[0, :] = loss[0, :]

    # Forward pass: Fill DP table
    for t in range(1, T):
        for k in range(K):
            # Compute min_j(DP[t-1][j] + λ*1_{j≠k})
            # Penalty is 0 if j==k, lambda if j!=k
            transition_costs = dp[t-1, :].copy()
            for j in range(K):
                if j != k:
                    transition_costs[j] += lambda_penalty

            # DP recurrence
            best_prev_state = np.argmin(transition_costs)
            dp[t, k] = loss[t, k] + transition_costs[best_prev_state]
            backpointer[t, k] = best_prev_state

    # Backward pass: Backtrack to find optimal state sequence
    state_sequence = np.zeros(T, dtype=int)
    state_sequence[T-1] = np.argmin(dp[T-1, :])  # Best final state

    for t in range(T-2, -1, -1):
        state_sequence[t] = backpointer[t+1, state_sequence[t+1]]

    # Compute final objective value
    objective_value = np.min(dp[T-1, :])

    return state_sequence, objective_value


def coordinate_descent(
    features: np.ndarray,
    lambda_penalty: float,
    max_iter: int = 100,
    tol: float = 1e-6,
    random_seed: Optional[int] = None,
    verbose: bool = False
) -> Tuple[np.ndarray, np.ndarray, float, bool]:
    """
    Coordinate descent optimization alternating between theta and S.

    Algorithm:
        1. Initialize Θ using K-means clustering (λ=0)
        2. Loop until convergence or max_iter:
           E-step: Fix Θ, optimize S using dynamic_programming()
           M-step: Fix S, optimize Θ: θ_k = mean({x_t : s_t = k})
           Check: |objective_new - objective_old| < tol
        3. Return final Θ, S, objective, converged_flag

    Args:
        features: (T, D) feature matrix
        lambda_penalty: Jump penalty
        max_iter: Maximum iterations (default: 100)
        tol: Convergence tolerance (default: 1e-6)
        random_seed: Random seed for K-means initialization
        verbose: Print iteration progress

    Returns:
        theta: (K, D) optimal centroids
        state_sequence: (T,) optimal state assignments
        objective_value: Final objective function value
        converged: True if converged within max_iter

    Reference:
        Section 3.4, Shu et al., Princeton 2024
        "A coordinate descent algorithm...alternating between optimizing
        the model parameters Θ and the state sequence S"

    Example:
        >>> features = np.random.randn(200, 3)
        >>> theta, states, obj, conv = coordinate_descent(features, lambda_penalty=50.0)
        >>> print(f"Converged: {conv}, Final objective: {obj:.2f}")
    """
    T, D = features.shape
    K = 2  # Two states: bull (0) and bear (1)

    # Initialize Θ using K-means (equivalent to λ=0)
    if verbose:
        print(f"Initializing with K-means (K={K})...")

    kmeans = KMeans(n_clusters=K, random_state=random_seed, n_init=10)
    kmeans_labels = kmeans.fit_predict(features)
    theta = kmeans.cluster_centers_.copy()  # (K, D)

    # Initial state sequence from K-means
    state_sequence = kmeans_labels.astype(int)

    # Compute initial objective
    prev_objective = np.inf

    converged = False

    for iteration in range(max_iter):
        # E-step: Fix Θ, optimize S using dynamic programming
        state_sequence, current_objective = dynamic_programming(
            features, theta, lambda_penalty
        )

        # M-step: Fix S, optimize Θ by averaging features in each state
        for k in range(K):
            mask = (state_sequence == k)
            if np.sum(mask) > 0:
                theta[k, :] = np.mean(features[mask, :], axis=0)
            else:
                # Handle empty cluster (shouldn't happen with good initialization)
                # Reinitialize to random feature
                theta[k, :] = features[np.random.randint(T), :]
                if verbose:
                    print(f"  Warning: Empty cluster {k} at iteration {iteration}")

        # Check convergence
        objective_change = abs(current_objective - prev_objective)

        if verbose:
            print(f"Iter {iteration+1}: Objective={current_objective:.4f}, "
                  f"Delta={objective_change:.2e}")

        # Objective should decrease (or stay same)
        if current_objective > prev_objective + 1e-10:
            if verbose:
                print(f"  Warning: Objective increased from {prev_objective:.4f} "
                      f"to {current_objective:.4f}")

        if objective_change < tol:
            converged = True
            if verbose:
                print(f"Converged after {iteration+1} iterations")
            break

        prev_objective = current_objective

    if not converged and verbose:
        print(f"Did not converge after {max_iter} iterations "
              f"(final delta={objective_change:.2e})")

    return theta, state_sequence, current_objective, converged


def fit_jump_model_multi_start(
    features: np.ndarray,
    lambda_penalty: float,
    n_starts: int = 10,
    max_iter: int = 100,
    random_seed: int = 42,
    verbose: bool = False
) -> dict:
    """
    Multi-start optimization with multiple random initializations.

    Runs coordinate descent n_starts times with different random seeds
    and keeps the result with the lowest objective value.

    Args:
        features: (T, D) feature matrix
        lambda_penalty: Jump penalty
        n_starts: Number of random initializations (default: 10 per paper)
        max_iter: Maximum iterations per run
        random_seed: Base random seed
        verbose: Print progress for each run

    Returns:
        Dictionary with:
            - theta: (K, D) best centroids
            - state_sequence: (T,) best state sequence
            - objective: Best objective value
            - n_converged: Number of runs that converged
            - all_objectives: List of all final objectives
            - best_run: Index of best run (0-indexed)

    Reference:
        Section 3.4, Shu et al., Princeton 2024
        "We run the algorithm ten times and retain the fitting with
        the lowest objective value"

    Example:
        >>> features = np.random.randn(500, 3)
        >>> result = fit_jump_model_multi_start(features, lambda_penalty=50.0, n_starts=10)
        >>> print(f"Best objective: {result['objective']:.2f}")
        >>> print(f"Converged runs: {result['n_converged']}/{len(result['all_objectives'])}")
    """
    if verbose:
        print(f"Running {n_starts} random initializations...")

    best_objective = np.inf
    best_theta = None
    best_state_sequence = None
    all_objectives = []
    n_converged = 0
    best_run = -1

    for run in range(n_starts):
        # Use different seed for each run
        run_seed = random_seed + run if random_seed is not None else None

        if verbose:
            print(f"\nRun {run+1}/{n_starts} (seed={run_seed}):")

        # Run coordinate descent
        theta, state_seq, objective, converged = coordinate_descent(
            features=features,
            lambda_penalty=lambda_penalty,
            max_iter=max_iter,
            tol=1e-6,
            random_seed=run_seed,
            verbose=verbose
        )

        all_objectives.append(objective)
        if converged:
            n_converged += 1

        # Keep best result
        if objective < best_objective:
            best_objective = objective
            best_theta = theta.copy()
            best_state_sequence = state_seq.copy()
            best_run = run

    if verbose:
        print(f"\nBest run: {best_run+1}, Best objective: {best_objective:.4f}")
        print(f"Converged: {n_converged}/{n_starts} runs")
        obj_array = np.array(all_objectives)
        print(f"Objective range: [{obj_array.min():.4f}, {obj_array.max():.4f}]")
        print(f"Objective std: {obj_array.std():.4f}")

    return {
        'theta': best_theta,
        'state_sequence': best_state_sequence,
        'objective': best_objective,
        'n_converged': n_converged,
        'all_objectives': all_objectives,
        'best_run': best_run
    }


class AcademicJumpModel:
    """
    Academic Statistical Jump Model for market regime detection.

    Implements the clustering-based regime detection with temporal penalty
    as described in Shu et al., Princeton 2024.

    Key Features:
        - Coordinate descent optimization with dynamic programming
        - Multi-start initialization (10 runs) for global optimum
        - 3-dimensional features: Downside Deviation + 2 Sortino Ratios
        - Online inference with 3000-day lookback window
        - Temporal penalty (λ) controls regime persistence

    Academic Performance (from paper):
        - S&P 500: Sharpe 0.68 vs 0.48 B&H (+42%)
        - MaxDD reduction: ~50%
        - Regime switches: <1 per year with λ=50

    Attributes:
        lambda_penalty: Jump penalty (controls persistence)
        theta_: (K, D) fitted centroids {bull, bear}
        state_labels_: {0: 'bull', 1: 'bear'} mapping
        is_fitted_: Whether model has been fitted

    Reference:
        Shu et al., "Downside Risk Reduction Using Regime-Switching Signals:
        A Statistical Jump Model Approach", Princeton 2024

    Example:
        >>> model = AcademicJumpModel(lambda_penalty=50.0)
        >>> model.fit(spy_data)  # 3000-day OHLC data
        >>> regime = model.predict(spy_data)
        >>> print(f"Current regime: {regime.iloc[-1]}")
    """

    def __init__(self, lambda_penalty: float = 50.0):
        """
        Initialize Academic Jump Model.

        Args:
            lambda_penalty: Jump penalty (default: 50.0 per paper's typical value)
                           Higher values = more persistent regimes
                           lambda=5: ~2.7 switches/year
                           lambda=50-100: <1 switch/year
        """
        self.lambda_penalty = lambda_penalty
        self.theta_ = None
        self.state_labels_ = {0: 'bull', 1: 'bear'}
        self.is_fitted_ = False
        self._fit_info_ = None  # Store fit diagnostics

    def fit(
        self,
        data: pd.DataFrame,
        n_starts: int = 10,
        max_iter: int = 100,
        random_seed: int = 42,
        verbose: bool = False
    ) -> 'AcademicJumpModel':
        """
        Fit model on OHLC data using multi-start coordinate descent.

        Workflow:
            1. Calculate features using Phase A (academic_features.py)
            2. Run multi-start optimization (10 random initializations)
            3. Store best centroids (bull vs bear)
            4. Label states based on cumulative return

        Args:
            data: OHLC DataFrame with 'Close' column (3000 days recommended)
            n_starts: Number of random initializations (default: 10)
            max_iter: Maximum iterations per run (default: 100)
            random_seed: Base random seed for reproducibility
            verbose: Print optimization progress

        Returns:
            self (fitted model)

        Example:
            >>> from data.alpaca import fetch_alpaca_data
            >>> spy_data = fetch_alpaca_data('SPY', timeframe='1D', period_days=3000)
            >>> model = AcademicJumpModel(lambda_penalty=50.0)
            >>> model.fit(spy_data, verbose=True)
            >>> print(f"Bull centroid: {model.theta_[0]}")
            >>> print(f"Bear centroid: {model.theta_[1]}")
        """
        if verbose:
            print(f"Fitting Academic Jump Model (lambda={self.lambda_penalty})...")

        # Calculate features using Phase A
        features_df = calculate_features(
            close=data['Close'],
            risk_free_rate=0.03,  # 3% annual risk-free rate
            standardize=False  # Use raw features per reference implementation
        )

        # Drop NaN rows from warm-up period
        features_df = features_df.dropna()
        features = features_df.values  # Convert to numpy array

        if verbose:
            print(f"Features shape: {features.shape}")
            print(f"Feature ranges:")
            print(f"  Downside Dev: [{features[:, 0].min():.4f}, {features[:, 0].max():.4f}]")
            print(f"  Sortino 20d: [{features[:, 1].min():.2f}, {features[:, 1].max():.2f}]")
            print(f"  Sortino 60d: [{features[:, 2].min():.2f}, {features[:, 2].max():.2f}]")

        # Run multi-start optimization
        result = fit_jump_model_multi_start(
            features=features,
            lambda_penalty=self.lambda_penalty,
            n_starts=n_starts,
            max_iter=max_iter,
            random_seed=random_seed,
            verbose=verbose
        )

        self.theta_ = result['theta']
        self._fit_info_ = result

        # Label states: bull (0) has higher mean return, bear (1) has lower
        # Use state sequence from fitting to compute cumulative returns
        state_seq = result['state_sequence']
        returns = data['Close'].pct_change().dropna().values

        # Align returns with feature index (features drop NaN)
        returns_aligned = returns[-len(state_seq):]

        cum_return_0 = np.sum(returns_aligned[state_seq == 0])
        cum_return_1 = np.sum(returns_aligned[state_seq == 1])

        if cum_return_0 < cum_return_1:
            # Need to swap labels
            self.theta_ = self.theta_[[1, 0], :]
            self.state_labels_ = {0: 'bull', 1: 'bear'}
            if verbose:
                print("Swapped state labels (state 1 had higher returns)")
        else:
            self.state_labels_ = {0: 'bull', 1: 'bear'}

        self.is_fitted_ = True

        if verbose:
            print("\nFit complete!")
            print(f"Bull centroid (state 0): DD={self.theta_[0, 0]:.4f}, "
                  f"S20={self.theta_[0, 1]:.2f}, S60={self.theta_[0, 2]:.2f}")
            print(f"Bear centroid (state 1): DD={self.theta_[1, 0]:.4f}, "
                  f"S20={self.theta_[1, 1]:.2f}, S60={self.theta_[1, 2]:.2f}")

        return self

    def predict(self, data: pd.DataFrame) -> pd.Series:
        """
        Predict state sequence for data (requires fitted model).

        Uses dynamic programming with fitted centroids to assign states.

        Args:
            data: OHLC DataFrame with 'Close' column

        Returns:
            Series of state labels ('bull' or 'bear') with original data index

        Raises:
            ValueError: If model not fitted

        Example:
            >>> model.fit(train_data)
            >>> predictions = model.predict(test_data)
            >>> print(predictions.value_counts())
            bull    120
            bear     30
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted before prediction. Call fit() first.")

        # Calculate features
        features_df = calculate_features(
            close=data['Close'],
            risk_free_rate=0.03,
            standardize=False
        )

        # Drop NaN rows
        features_df = features_df.dropna()
        features = features_df.values

        # Run DP to get state sequence
        state_sequence, _ = dynamic_programming(
            features=features,
            theta=self.theta_,
            lambda_penalty=self.lambda_penalty
        )

        # Map numeric states to labels
        state_labels = [self.state_labels_[s] for s in state_sequence]

        # Return Series with original index
        return pd.Series(state_labels, index=features_df.index, name='regime')

    def online_inference(
        self,
        data: pd.DataFrame,
        lookback_window: int = 3000
    ) -> str:
        """
        Online inference with lookback window (Section 3.4.2).

        Uses the last lookback_window days to run DP and extracts the
        final state s_T as the current regime. This mimics real-time
        inference with limited historical data.

        Latency: Expected ~15 days per paper (tradeoff with accuracy)

        Args:
            data: OHLC DataFrame (at least lookback_window days)
            lookback_window: Days to use for inference (default: 3000 per paper)

        Returns:
            Current regime: 'bull' or 'bear'

        Raises:
            ValueError: If model not fitted or insufficient data

        Reference:
            Section 3.4.2 "Online Inference", Shu et al., Princeton 2024
            "We incorporate a lookback window...with l=3000...and run the
            dynamic programming algorithm...We then extract the last state
            s_t from the optimal state sequence as the online inferred
            prevailing regime."

        Example:
            >>> current_regime = model.online_inference(recent_data, lookback_window=3000)
            >>> print(f"Current market regime: {current_regime}")
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted before inference. Call fit() first.")

        # Take last lookback_window days
        if len(data) < lookback_window:
            raise ValueError(
                f"Insufficient data: {len(data)} days < {lookback_window} required"
            )

        lookback_data = data.iloc[-lookback_window:]

        # Run predict on lookback window
        regime_series = self.predict(lookback_data)

        # Return last state
        return regime_series.iloc[-1]

    def get_fit_info(self) -> dict:
        """
        Get diagnostic information from fitting process.

        Returns:
            Dictionary with:
                - objective: Best objective value
                - n_converged: Number of runs that converged
                - all_objectives: List of all final objectives
                - best_run: Index of best run

        Raises:
            ValueError: If model not fitted
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted first. Call fit().")

        return self._fit_info_
