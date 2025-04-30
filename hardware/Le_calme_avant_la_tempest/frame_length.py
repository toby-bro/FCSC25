import os

import numpy as np
from plotting import plot_comprehensive_search_progress, plot_line_length_image
from scipy import signal
from tqdm import tqdm


def find_approx_line_length(
    data: np.ndarray,
    search_range: tuple[float, float] = (550.0, 650.0),
    step: float = 1.0,
) -> tuple[float, dict[str, dict[float, float]]]:
    """
    Find the optimal line length by testing a range of values and evaluating image quality.
    Uses multiple metrics for more reliable detection. Supports floating-point line lengths.

    Returns:
        tuple of (best_line_length, search_history)
    """
    print(f'Searching for optimal line length between {search_range[0]} and {search_range[1]} with step {step}...')

    search_history: dict[str, dict[float, float]] = {
        f'Search {search_range[0]:.1f}-{search_range[1]:.1f}': {},
    }

    # Use numpy's arange for floating-point ranges
    line_lengths = np.arange(search_range[0], search_range[1] + step / 2, step)

    # Calculate a test height that uses as much data as possible
    # Use the middle of the range to estimate
    mid_length = (search_range[0] + search_range[1]) / 2
    max_possible_height = len(data) // int(mid_length)
    # Set a reasonable limit to avoid memory issues
    test_height = min(max_possible_height, 5000)

    print(f'Using test height of {test_height} lines (out of {max_possible_height} possible)')

    ac_scores = []
    image_scores = []
    combined_scores = []

    output_dir = 'line_length_tests'
    os.makedirs(output_dir, exist_ok=True)

    for line_length in tqdm(line_lengths):
        # Use the closest integer for autocorrelation which expects an integer
        ac_score = auto_correlation_metric(data, round(line_length))
        ac_scores.append(ac_score)

        # Reconstruct with the exact float value
        image = reconstruct_test_image(data, float(line_length), test_height)
        image_score = evaluate_homogeneity(image)
        image_scores.append(image_score)
        combined_score = (ac_score * 0.4) + (image_score * 0.6)
        combined_scores.append(combined_score)
        search_history[f'Search {search_range[0]:.1f}-{search_range[1]:.1f}'][float(line_length)] = combined_score

        if len(combined_scores) <= 5 or combined_score > sorted(combined_scores[:-1])[-5]:
            plot_line_length_image(output_dir, line_length, image, combined_score)

    # Find best line length
    best_idx = np.argmax(combined_scores)
    best_line_length = float(line_lengths[best_idx])
    best_score = combined_scores[best_idx]

    print(f'Best line length: {best_line_length:.2f} with score {best_score:.4f}')

    return best_line_length, search_history


def auto_correlation_metric(data: np.ndarray, line_length: int, num_lines: int = 100) -> float:
    """
    Use auto-correlation to detect repeating patterns at the line frequency.
    Strong peaks at multiples of line_length indicate good alignment.
    """
    max_samples = min(len(data), line_length * num_lines)
    analysis_data = data[:max_samples]

    auto_corr = signal.correlate(analysis_data, analysis_data, mode='full')
    auto_corr = auto_corr[len(auto_corr) // 2 :]

    if auto_corr[0] != 0:
        auto_corr = auto_corr / auto_corr[0]

    line_multiple_scores = []
    for i in range(1, min(10, len(auto_corr) // line_length)):
        idx = i * line_length
        if idx < len(auto_corr):
            peak_val = auto_corr[idx]
            line_multiple_scores.append(peak_val)

    if line_multiple_scores:
        return float(np.mean(line_multiple_scores))
    return 0.0


def evaluate_homogeneity(image: np.ndarray) -> float:
    """
    Evaluate image quality based on the presence of large homogeneous regions.
    Fixed to ensure scores are not all zero.
    """
    height, width = image.shape
    block_size = 30

    blocks_checked = 0
    low_variance_blocks = 0

    blocks_checked, low_variance_blocks = count_low_variance_blocks(image, height, width, block_size)

    homogeneity_ratio = low_variance_blocks / max(1, blocks_checked)
    alternating_pattern_penalty = 0.0

    row_means = np.mean(image, axis=1)
    row_diffs = np.abs(np.diff(row_means))

    alternating_rows = 0
    for i in range(0, len(row_diffs) - 1, 2):
        if row_diffs[i] > 0.1 and (i + 1 < len(row_diffs) and row_diffs[i + 1] > 0.1):
            alternating_rows += 1

    if alternating_rows > height / 10:
        alternating_pattern_penalty += 0.6

    score = homogeneity_ratio - min(0.5, alternating_pattern_penalty)
    return max(0.01, score)


def count_low_variance_blocks(image: np.ndarray, height: int, width: int, block_size: int) -> tuple[int, int]:
    blocks_checked = 0
    low_variance_blocks = 0
    for y_start in range(0, height - block_size, block_size):
        for x_start in range(0, width - block_size, block_size):
            blocks_checked += 1
            block = image[y_start : y_start + block_size, x_start : x_start + block_size]
            block_variance = np.var(block)

            if block_variance < 0.01:
                low_variance_blocks += 1
    return blocks_checked, low_variance_blocks


def evaluate_vertical_alignment(image: np.ndarray) -> float:
    """
    Specifically evaluates how well-aligned vertical features are in the image.
    Returns a score where higher means better vertical alignment.
    """
    height, width = image.shape

    # 1. Measure column-wise consistency
    col_scores = calculate_column_consistency(image, height, width)

    # Average column consistency
    avg_col_consistency = np.mean(col_scores)

    # 2. Detect vertical lines by looking for consistent intensities in columns
    vertical_line_strength = calculate_vertical_line_strength(image, width)

    # 3. Check for diagonal artifacts by comparing shifted columns
    diagonal_penalty = calculate_diagonal_penalty(image, height, width)

    # Final vertical alignment score: combine metrics and penalize diagonals
    vertical_score = avg_col_consistency * 0.6 + vertical_line_strength * 0.4 - diagonal_penalty * 0.5

    # Ensure the score is in a valid range
    return max(0.0, min(1.0, float(vertical_score)))


def calculate_diagonal_penalty(image: np.ndarray, height: int, width: int) -> float:
    diagonal_penalty = 0.0
    for shift in range(1, min(10, height // 4)):
        # For each potential diagonal slope
        shift_correlations: list[float] = []
        for col in range(width - 1):
            # Compare each column with the next column, shifted by 'shift' pixels
            col1 = image[shift:, col]  # Current column, shifted down
            col2 = image[:-shift, col + 1]  # Next column, not shifted

            calculate_shift_correlation(shift_correlations, col1, col2)

        # If we found strong correlations when shifted, it indicates diagonal artifacts
        if shift_correlations:
            diagonal_penalty = max(diagonal_penalty, float(np.mean(shift_correlations)))
    return diagonal_penalty


def calculate_shift_correlation(shift_correlations: list[float], col1: np.ndarray, col2: np.ndarray) -> None:
    if len(col1) > 0 and len(col2) > 0:
        try:
            # Calculate correlation between the shifted columns
            corr = np.corrcoef(col1, col2)[0, 1]
            if not np.isnan(corr):
                shift_correlations.append(abs(corr))
        except Exception as e:
            print(f'Error calculating correlation: {e}')


def calculate_vertical_line_strength(image: np.ndarray, width: int) -> float:
    vertical_line_strength = 0.0
    for col in range(1, width - 1):
        # Compare this column with neighbors
        col_data = image[:, col]
        left_col = image[:, col - 1]
        right_col = image[:, col + 1]

        # If this column is consistently different from neighbors,
        # it's likely a vertical edge/line
        left_diff = np.mean(np.abs(col_data - left_col))
        right_diff = np.mean(np.abs(col_data - right_col))

        # High difference with neighbors but consistency within column
        # indicates a strong vertical line
        if left_diff > 0.1 and right_diff > 0.1 and np.var(col_data) < 0.05:
            vertical_line_strength += 1.0

    # Normalize by width
    vertical_line_strength /= max(1, width - 2)
    return vertical_line_strength


def calculate_column_consistency(image: np.ndarray, height: int, width: int) -> list[float]:
    col_scores = []
    for col in range(width):
        column = image[:, col]

        # Calculate gradients (changes between adjacent pixels)
        gradients = np.abs(np.diff(column))

        # Count sharp transitions (edges)
        sharp_transitions = np.sum(gradients > 0.2)

        # Fewer transitions = more consistent column = better vertical alignment
        consistency = 1.0 - (sharp_transitions / max(1, height - 1))
        col_scores.append(consistency)
    return col_scores


def binary_search_line_length(
    data: np.ndarray,
    left: float,
    right: float,
    test_height: int | None = None,
    iterations: int = 3,
) -> tuple[float, float]:
    """
    Find optimal line length using grid search with refinement.
    Evaluates 10 points per iteration and narrows the search range
    based on the top-performing region.

    Args:
        data: Source data
        left: Lower bound of search range
        right: Upper bound of search range
        test_height: Height for test images (defaults to maximum possible)
        iterations: Number of search iterations

    Returns:
        tuple of (optimal_line_length, score)
    """
    print(f'Grid searching for optimal line length between {left:.2f} and {right:.2f}...')

    # Use maximum possible height if none is specified
    if test_height is None:
        avg_line_length = (left + right) / 2
        test_height = min(len(data) // int(avg_line_length), 10000)
        print(f'Using maximum practical height: {test_height} lines for analysis')

    # Keep track of all evaluated points
    evaluated_points: dict[float, float] = {}

    # Track the best result found
    global_best_length = None
    global_best_score = -float('inf')

    for iteration in range(iterations):
        # Create 10 evenly spaced test points in the current range
        test_points = np.linspace(left, right, 10)
        scores = []

        # Evaluate all test points
        for length in test_points:
            # Skip if already evaluated
            if length in evaluated_points:
                scores.append((length, evaluated_points[length]))
                continue

            # Evaluate this line length
            ac_score = auto_correlation_metric(data, round(length))
            image = reconstruct_test_image(data, length, test_height)
            image_score = evaluate_homogeneity(image)
            vertical_score = evaluate_vertical_alignment(image)

            # Combined score
            score = (ac_score * 0.5) + (image_score * 0.4) + (vertical_score * 1)
            evaluated_points[length] = score
            scores.append((length, score))

            # Update global best
            if score > global_best_score:
                global_best_score = score
                global_best_length = length

        # Sort by score (descending) and keep the top 3
        scores.sort(key=lambda x: x[1], reverse=True)
        top_three = scores[:3]

        # Print current state
        print(f'  Iteration {iteration+1}: Best values {[f"{length:.2f} ({s:.4f})" for length, s in top_three[:3]]}')

        # Update the search range based on top three points
        if len(top_three) >= 2:
            # Define new range from the min and max of the top points
            top_lengths = [length for length, _ in top_three]
            new_left = min(top_lengths)
            new_right = max(top_lengths)

            # Maintain the focused range without expanding
            left = new_left
            right = new_right

            print(f'  New search range: [{left:.2f}, {right:.2f}]')

    # Return the best length found across all iterations
    if global_best_length is None:
        # This shouldn't happen if there were any valid evaluations
        print('Warning: No valid line length found. Using the middle of the range.')
        return (left + right) / 2, 0.0

    print(f'Best overall line length: {global_best_length:.2f} with score {global_best_score:.4f}')
    return global_best_length, global_best_score


def reconstruct_test_image(data: np.ndarray, line_length: float, num_lines: int | np.int_) -> np.ndarray:
    """
    Simplified image reconstruction focusing on straight vertical alignment.
    Uses precise integer math to avoid interpolation artifacts.
    """
    samples_per_line = round(line_length)
    image = np.zeros((int(num_lines), samples_per_line), dtype=np.float32)

    for line in range(int(num_lines)):
        start_idx = round(line * line_length)
        end_idx = min(len(data), start_idx + samples_per_line)

        if start_idx >= len(data):
            break

        line_data = data[start_idx:end_idx]
        image[line, : len(line_data)] = line_data

    # Normalize the image to [0, 1] range
    if np.max(image) > np.min(image):
        image = (image - np.min(image)) / (np.max(image) - np.min(image))  # type: ignore[assignment]

    return image


def find_optimal_line_length(data: np.ndarray) -> float:
    coarse_line_length, coarse_history = find_approx_line_length(data, search_range=(256.0, 1200.0), step=4.0)
    print(f'Best coarse line length: {coarse_line_length:.2f}')

    # Use a finer step for the refined search
    search_min = max(256.0, coarse_line_length - 10.0)
    search_max = min(1200.0, coarse_line_length + 10.0)

    print(f'\nRefining search in range {search_min:.1f}-{search_max:.1f} with step=0.5...')
    line_length, refined_history = find_approx_line_length(data, search_range=(search_min, search_max), step=0.5)
    print(f'Best refined line length: {line_length:.2f}')

    # Use binary search for final refinement instead of small steps
    final_min = max(256.0, line_length - 2.0)
    final_max = min(1200.0, line_length + 2.0)

    print(f'\nFinal binary search refinement in range {final_min:.2f}-{final_max:.2f}...')
    line_length, best_score = binary_search_line_length(data, final_min, final_max, iterations=10)
    print(f'Final optimal line length: {line_length:.2f} with score {best_score:.4f}')

    # Create comprehensive plot of the entire line length search process
    plot_comprehensive_search_progress(
        [coarse_history, refined_history],
        'line_length_tests',
        'Line Length Search',
        'comprehensive_line_length_search.png',
        'Line Length',
    )

    return line_length
