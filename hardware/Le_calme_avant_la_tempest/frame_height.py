import os
from typing import TYPE_CHECKING, Any

import numpy as np
from frame_length import reconstruct_test_image
from frame_offset import find_optimal_offset
from plotting import (
    plot_autocorrelation,
    plot_best_frame_results,
    plot_candidate_frames,
    plot_sample_image,
    plot_similarity_scores,
)
from scipy import signal
from tqdm import tqdm


def detect_frame_periodicity(data: np.ndarray, line_length: float, max_height: int | None = None) -> tuple[int, int]:
    """
    Detect frame height and offset by analyzing periodicity in a large chunk of data.
    When periodicity fails, tries to find the height that minimizes inter-frame differences.
    Uses entire data set by default.

    Args:
        data: The source TEMPEST signal data
        line_length: The optimal line length
        max_height: Maximum height to consider for analysis (defaults to maximum possible)

    Returns:
        tuple of (optimal_frame_height, optimal_offset)
    """
    # Calculate the maximum possible height based on data length and line length
    if max_height is None:
        total_possible_height = len(data) // int(line_length)
        # Set a practical upper limit to avoid memory issues (adjust based on available RAM)
        max_practical_height = min(total_possible_height, 20000)
        print('\nAnalyzing frame periodicity using entire data set')
        print(f'Total possible height: {total_possible_height} lines')
        print(f'Using practical maximum: {max_practical_height} lines')
        max_height = max_practical_height

    # Create a large sample image to analyze - use entire data if possible
    sample_size_limit = 50000000  # 50M samples limit to prevent memory issues
    max_sample_size = min(int(line_length * max_height), sample_size_limit, len(data))
    sample_data = data[:max_sample_size]
    actual_max_height = min(max_height, int(max_sample_size / line_length))
    print(f'Using {actual_max_height} lines for periodicity analysis (from {len(sample_data)} samples)')

    sample_image = reconstruct_test_image(sample_data, line_length, actual_max_height)

    # Directory for saving analysis results
    analysis_dir = 'frame_analysis'
    os.makedirs(analysis_dir, exist_ok=True)

    # Save the sample image for inspection
    plot_sample_image(actual_max_height, sample_image, analysis_dir)

    # Try autocorrelation-based detection first
    frame_height, periodicity_found = detect_frame_height_by_autocorrelation(
        sample_image,
        analysis_dir,
    )

    # If autocorrelation fails, try minimizing inter-frame differences with progressive refinement
    if not periodicity_found:
        print('No clear periodicity detected. Trying to minimize inter-frame differences...')
        # Step 1: Coarse search to find top candidates
        top_heights, top_scores = find_top_frame_height_candidates(data, line_length, analysis_dir)

        # Step 2: Refine with binary search between top candidates
        frame_height = refine_frame_height_with_binary_search(data, line_length, top_heights, top_scores, analysis_dir)

    # Test different offsets to find the best frame alignment
    best_offset = find_optimal_offset(data, line_length, frame_height, analysis_dir)

    return frame_height, best_offset


def calculate_frame_similarity_scores(
    data: np.ndarray,
    line_length: float,
    analysis_dir: str,
    num_candidates: int,
    potential_heights: list[int],
) -> list[float]:
    diff_scores = []

    for height in tqdm(potential_heights):
        # Extract 3 consecutive frames (we need at least 2, use 3 for robustness)
        frame_size = int(line_length * height)
        num_frames = min(3, len(data) // frame_size)

        if num_frames < 2:
            print(f'Not enough data for height {height}')
            diff_scores.append(float('inf'))
            continue

        frames = []
        for i in range(num_frames):
            start_idx = i * frame_size
            end_idx = start_idx + frame_size
            frame_data = data[start_idx:end_idx]
            frame = reconstruct_test_image(frame_data, line_length, height)
            frames.append(frame)

        # Calculate differences between consecutive frames
        frame_diffs = []
        for i in range(len(frames) - 1):
            # Mean squared error
            mse = np.mean((frames[i] - frames[i + 1]) ** 2)

            # Also consider structural patterns - look at row and column means
            row_means_diff = np.mean(np.abs(np.mean(frames[i], axis=1) - np.mean(frames[i + 1], axis=1)))
            col_means_diff = np.mean(np.abs(np.mean(frames[i], axis=0) - np.mean(frames[i + 1], axis=0)))

            # Combined difference score - lower is better
            frame_diff = mse + row_means_diff + col_means_diff
            frame_diffs.append(frame_diff)

        # Use the average difference - invert to make higher score better for consistency
        avg_diff = np.mean(frame_diffs)
        # Invert to convert to similarity score (higher is better)
        score = 1.0 / (1.0 + avg_diff)
        diff_scores.append(score)

        # Save example frames for top candidates
        plot_candidate_frames(analysis_dir, num_candidates, diff_scores, height, frames, score)

    # Create a plot of similarity scores
    plot_similarity_scores(analysis_dir, potential_heights, diff_scores)
    return diff_scores


def binary_search_frame_height(
    data: np.ndarray,
    line_length: float,
    left: int,
    right: int,
    analysis_dir: str,
    iterations: int = 3,
) -> tuple[int, float]:
    """
    Find optimal frame height using grid search with refinement.
    Evaluates 10 points per iteration and narrows the search range
    based on the top-performing region.

    Args:
        data: Source data
        line_length: Line length
        left: Lower bound of search range
        right: Upper bound of search range
        analysis_dir: Directory to save analysis results
        iterations: Number of search iterations

    Returns:
        tuple of (optimal_height, score)
    """
    print(f'Grid searching for optimal frame height between {left} and {right}...')

    if left > right:
        left, right = right, left

    # Keep track of all evaluated heights
    evaluated_heights: dict[int, float] = {}

    # Track best result
    global_best_height = None
    global_best_score = -float('inf')

    for iteration in range(iterations):
        # Create 10 evenly spaced test points in the current range
        # Using linspace and rounding to get integer heights
        test_points = np.unique(np.round(np.linspace(left, right, 10))).astype(int)

        # Evaluate all test points
        global_best_height, global_best_score, scores = evaluate_frame_heights(
            data,
            line_length,
            analysis_dir,
            evaluated_heights,
            global_best_score,
            global_best_height,
            test_points,
        )

        # Sort by score (descending) and keep the top 3
        scores.sort(key=lambda x: x[1], reverse=True)
        top_three = scores[:3]

        # Print current state
        print(f'  Iteration {iteration+1}: Best values {[f"{h} ({s:.6f})" for h, s in top_three[:3]]}')

        # Update the search range based on top three points
        if len(top_three) >= 2:
            # Define new range from the min and max of the top points
            top_heights = [h for h, _ in top_three]
            new_left = min(top_heights)
            new_right = max(top_heights)

            # Maintain the focused range without expanding
            left = new_left
            right = new_right

            print(f'  New search range: [{left}, {right}]')

    # Return the best height found across all iterations
    if global_best_height is None:
        # This shouldn't happen if there were any valid evaluations
        print('Warning: No valid frame height found. Using the middle of the range.')
        if TYPE_CHECKING:
            avg = int((left + right)) // 2
        else:
            avg = (left + right) // 2
        return avg, 0.0

    print(f'Best overall frame height: {global_best_height} with score {global_best_score:.6f}')
    return global_best_height, global_best_score


def evaluate_frame_heights(
    data: np.ndarray,
    line_length: float,
    analysis_dir: str,
    evaluated_heights: dict[int, float],
    global_best_score: float,
    global_best_height: int | None,
    test_points: np.ndarray[Any, np.dtype[int]],  # type: ignore[type-var]
) -> tuple[int | None, float, list[tuple[int, float]]]:
    scores = []
    for height in test_points:
        # Skip if already evaluated
        if height in evaluated_heights:
            scores.append((height, evaluated_heights[height]))
            continue

            # Extract frames for testing
        frame_size = int(line_length * height)
        num_frames = min(2, len(data) // frame_size)

        if num_frames < 2:
            evaluated_heights[height] = -float('inf')
            scores.append((height, -float('inf')))
            continue

        frames, score = compute_frame_scores(data, line_length, height, frame_size, num_frames)

        evaluated_heights[height] = score
        scores.append((height, score))

        # Update global best
        if score > global_best_score:
            global_best_score = score
            global_best_height = height

            # Save the new best result
            plot_best_frame_results(analysis_dir, height, frames, score)
    return global_best_height, global_best_score, scores


def compute_frame_scores(
    data: np.ndarray,
    line_length: float,
    height: int,
    frame_size: int,
    num_frames: int,
) -> tuple[list[np.ndarray], float]:
    frames = []
    for i in range(num_frames):
        start_idx = i * frame_size
        end_idx = start_idx + frame_size
        frame_data = data[start_idx:end_idx]
        frame = reconstruct_test_image(frame_data, line_length, height)
        frames.append(frame)

        # Calculate similarity between frames (inverse of difference)
    mse = np.mean((frames[0] - frames[1]) ** 2)
    row_diff = np.mean(np.abs(np.mean(frames[0], axis=1) - np.mean(frames[1], axis=1)))
    col_diff = np.mean(np.abs(np.mean(frames[0], axis=0) - np.mean(frames[1], axis=0)))

    # Convert to similarity score (higher is better)
    diff = mse + row_diff + col_diff
    score = 1.0 / (1.0 + diff)
    return frames, score


def detect_frame_height_by_min_difference(
    data: np.ndarray,
    line_length: float,
    analysis_dir: str,
) -> int:
    """
    Detect frame height by finding the height that minimizes differences
    between consecutive frames. Using a three-step approach:
    1. Find top candidates
    2. Refine with binary search
    3. Return best result

    Returns:
        Estimated frame height
    """
    # Find top candidate heights
    top_heights, top_scores = find_top_frame_height_candidates(data, line_length, analysis_dir)

    # Refine with binary search
    final_height = refine_frame_height_with_binary_search(data, line_length, top_heights, top_scores, analysis_dir)

    return final_height  # noqa: RET504


def refine_frame_height_with_binary_search(
    data: np.ndarray,
    line_length: float,
    top_heights: list[int],
    top_scores: list[float],
    analysis_dir: str,
) -> int:
    """
    Refine frame height detection by performing grid searches between potential candidates.

    Args:
        data: Source data
        line_length: Line length to use for reconstruction
        top_heights: List of top candidate frame heights
        top_scores: Scores corresponding to the top heights
        analysis_dir: Directory to save analysis results

    Returns:
        Final optimal frame height
    """
    if not top_heights:
        print('No valid frame heights to refine. Using default height.')
        return 768  # Default to a common height

    if len(top_heights) == 1:
        return top_heights[0]  # Only one candidate, no refinement needed

    # Sort heights for better range definition
    heights_and_scores = sorted(zip(top_heights, top_scores, strict=False))
    sorted_heights = [h for h, _ in heights_and_scores]

    print(f'Refining frame height using {len(sorted_heights)} candidate heights: {sorted_heights}')

    # If we have multiple candidates, perform grid search between min and max
    min_height = min(sorted_heights)
    max_height = max(sorted_heights)

    # Only perform search if there's a meaningful range
    if max_height - min_height > 5:
        # Expand range slightly to ensure we don't miss optimal values
        search_min = max(1, min_height - int((max_height - min_height) * 0.1))
        search_max = max_height + int((max_height - min_height) * 0.1)

        print(f'Performing grid search between {search_min} and {search_max}')
        best_height, best_score = binary_search_frame_height(
            data,
            line_length,
            search_min,
            search_max,
            analysis_dir,
        )

        # Compare with original candidates
        best_original_idx = np.argmax(top_scores)
        best_original_height = top_heights[best_original_idx]
        best_original_score = top_scores[best_original_idx]

        print(f'Best from grid search: {best_height} (score: {best_score:.6f})')
        print(f'Best from original candidates: {best_original_height} (score: {best_original_score:.6f})')

        # Return whichever is better
        if best_score > best_original_score:
            return best_height
        return best_original_height
    # Range too small, just return the best of the candidates
    best_idx = np.argmax(top_scores)
    return top_heights[best_idx]


def detect_frame_height_by_autocorrelation(
    sample_image: np.ndarray,
    analysis_dir: str,
) -> tuple[int, bool]:
    """
    Detect frame height using autocorrelation of row means.

    Returns:
        tuple of (estimated_frame_height, success_flag)
    """
    # Analyze row means to detect repetitive patterns
    row_means = np.mean(sample_image, axis=1)

    # Try to detect periodicity using autocorrelation
    autocorr = signal.correlate(row_means, row_means, mode='full')
    autocorr = autocorr[len(autocorr) // 2 :]  # Only use the positive lags

    # Normalize for better peak detection
    if np.max(autocorr) > 0:
        autocorr = autocorr / np.max(autocorr)  # type: ignore[assignment]

    # Find peaks in autocorrelation, ignoring very small lags
    min_lag = 300  # Minimum reasonable frame height
    prominence = 0.1

    try:
        peaks, _ = signal.find_peaks(autocorr[min_lag:], height=0.2, distance=50, prominence=prominence)
        peaks = peaks + min_lag  # Adjust indices for skipped values
    except Exception as e:
        print(f'Error finding peaks in autocorrelation: {e}')
        return 768, False  # Default height, not found

    if len(peaks) < 2:
        print('Not enough peaks found in autocorrelation for height detection')
        return 768, False  # Default height, not found

    # The first peak is likely to be the frame height
    frame_height = int(peaks[0])
    print(f'Detected frame height: {frame_height} from autocorrelation')

    # Save the autocorrelation plot
    plot_autocorrelation(analysis_dir, autocorr, peaks, frame_height)

    return frame_height, True


def find_top_frame_height_candidates(
    data: np.ndarray,
    line_length: float,
    analysis_dir: str,
    num_candidates: int = 3,
) -> tuple[list[int], list[float]]:
    """
    Find the top N frame height candidates by testing a range of values and minimizing
    inter-frame differences.

    Returns:
        tuple of (top_heights, top_scores)
    """
    # Test a range of potential frame heights
    # Focus on common values with some padding
    potential_heights = [480, 600, 640, 720, 768, 800, 900, 1024, 1050, 1080, 1200]

    # If data size permits, also test some values in between
    if len(data) > line_length * 3000:  # Ensure we have enough data
        # Add heights in between the common ones
        for i in range(len(potential_heights) - 1):
            middle = (potential_heights[i] + potential_heights[i + 1]) // 2
            potential_heights.append(middle)
        potential_heights.sort()

    print(f'Testing {len(potential_heights)} potential frame heights...')

    # For each height, extract multiple consecutive frames and measure differences
    diff_scores = calculate_frame_similarity_scores(data, line_length, analysis_dir, num_candidates, potential_heights)

    # Find the top N heights
    top_indices = np.argsort(diff_scores)[-num_candidates:][::-1]  # Highest scores first
    top_heights = [potential_heights[i] for i in top_indices]
    top_scores = [diff_scores[i] for i in top_indices]

    print(f'Top {num_candidates} frame heights:')
    for i, (height, score) in enumerate(zip(top_heights, top_scores, strict=False)):
        print(f'  #{i+1}: Height {height} (score: {score:.6f})')

    return top_heights, top_scores
