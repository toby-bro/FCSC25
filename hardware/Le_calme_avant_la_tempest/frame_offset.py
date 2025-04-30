import numpy as np
from frame_length import reconstruct_test_image
from plotting import plot_corner_entropy_values, visualize_corner_entropy, visualize_final_offset
from tqdm import tqdm


def find_optimal_offset(
    data: np.ndarray,
    line_length: float,
    frame_height: int,
    analysis_dir: str,
) -> int:
    """
    Two-step grid search for optimal offset with entropy analysis focusing on the four corners.
    Looks for offsets where the entropy is maximized in the four corners and evenly distributed.
    """
    print('Starting offset detection with corner entropy analysis...')

    # Test different offsets across a full frame
    max_offset = int(line_length * frame_height)
    step_size = max(1, max_offset // 30)  # Test about 30 different offsets
    offsets_to_test = range(0, max_offset, step_size)
    offset_scores = []

    # Store entropy results for visualization
    corner_entropy_values = {}
    center_entropy_values = {}

    for offset in tqdm(offsets_to_test):
        # Extract two full frames for analysis
        test_data = data[offset : offset + int(line_length * frame_height * 2)]
        test_image = reconstruct_test_image(test_data, line_length, frame_height * 2)

        if test_image.shape[0] < frame_height * 1.5:
            offset_scores.append(0.0)
            continue

        # Analyze entropy in corners and center
        corner_entropy, center_entropy = analyze_corner_entropy(test_image, frame_height)

        # Store for visualization
        corner_entropy_values[offset] = corner_entropy
        center_entropy_values[offset] = center_entropy

        # Score based on corner entropy being high and evenly distributed
        score = calculate_corner_entropy_score(corner_entropy, center_entropy)
        offset_scores.append(score)

        # Save visualizations for top candidates
        if len(offset_scores) <= 3 or score > sorted(offset_scores[:-1])[-3]:
            visualize_corner_entropy(
                test_image,
                corner_entropy,
                center_entropy,
                offset,
                score,
                frame_height,
                analysis_dir,
            )

    # Find best offset
    if offset_scores:
        best_idx = np.argmax(offset_scores)
        best_offset = list(offsets_to_test)[best_idx]
        print(f'Best offset: {best_offset}')
    else:
        best_offset = 0
        print('Using default offset: 0')

    # Plot entropy distributions for all offsets
    plot_corner_entropy_values(
        list(offsets_to_test),
        offset_scores,
        corner_entropy_values,
        center_entropy_values,
        best_offset,
        analysis_dir,
    )

    # Save final result visualization
    test_data = data[best_offset : best_offset + int(line_length * frame_height * 2)]
    test_image = reconstruct_test_image(test_data, line_length, frame_height * 2)

    visualize_final_offset(frame_height, analysis_dir, test_image, best_offset)

    return best_offset


def analyze_corner_entropy(image: np.ndarray, frame_height: int) -> tuple[list[float], float]:
    """
    Calculate entropy in the four corners of the frame.
    Returns a list of 4 entropy values (top-left, top-right, bottom-left, bottom-right)
    and the center entropy.
    """
    # Focus on first frame for analysis
    analysis_height = min(image.shape[0], frame_height)
    frame = image[:analysis_height, :]
    height, width = frame.shape

    # Define corner regions (each corner is 15% of width/height)
    corner_size_h = int(height * 0.15)
    corner_size_w = int(width * 0.15)

    # Extract corners
    top_left = frame[:corner_size_h, :corner_size_w]
    top_right = frame[:corner_size_h, -corner_size_w:]
    bottom_left = frame[-corner_size_h:, :corner_size_w]
    bottom_right = frame[-corner_size_h:, -corner_size_w:]

    # Calculate center region (middle 50% of image)
    center_h_start = int(height * 0.25)
    center_h_end = int(height * 0.75)
    center_w_start = int(width * 0.25)
    center_w_end = int(width * 0.75)
    center = frame[center_h_start:center_h_end, center_w_start:center_w_end]

    # Calculate entropy for each region
    corner_entropies = [
        calculate_region_entropy(top_left),
        calculate_region_entropy(top_right),
        calculate_region_entropy(bottom_left),
        calculate_region_entropy(bottom_right),
    ]

    center_entropy = calculate_region_entropy(center)

    return corner_entropies, center_entropy


def calculate_region_entropy(region: np.ndarray) -> float:
    """Calculate entropy for an image region."""
    if region.size == 0:
        return 0.0

    # Quantize to 32 levels for histogram
    quantized = np.round(region * 31).astype(int)
    hist, _ = np.histogram(quantized, bins=32, range=(0, 31), density=True)

    # Calculate entropy (avoid log(0))
    hist = hist[hist > 0]
    if len(hist) > 0:
        entropy = -np.sum(hist * np.log2(hist))
        # Normalize to 0-5 range (max theoretical entropy for 32 bins is 5 bits)
        return float(entropy / 5.0)
    return 0.0


def calculate_corner_entropy_score(corner_entropy: list[float], center_entropy: float) -> float:
    """
    Calculate score based on corner entropy analysis.
    Ideal criteria:
    1. High entropy in all four corners
    2. Balanced/even entropy across all corners
    3. Lower entropy in the center relative to corners
    """
    if not corner_entropy:
        return 0.0

    # 1. Average corner entropy (higher is better)
    avg_corner = np.mean(corner_entropy)

    # 2. Corner entropy balance (lower standard deviation is better)
    corner_balance = 1.0 / (1.0 + np.std(corner_entropy) * 5.0)  # Invert and scale

    # 3. Corner-to-center entropy ratio (higher is better)
    if center_entropy > 0:
        corner_center_ratio = avg_corner / center_entropy
    else:
        corner_center_ratio = avg_corner * 2.0  # If center entropy is 0, this is good

    # Combined score - weighted for our specific criteria
    score = (
        avg_corner * 0.4  # High corner entropy
        + corner_balance * 0.4  # Even distribution between corners
        + min(corner_center_ratio, 3)  # type: ignore[call-overload]
        * 0.2  # Higher entropy in corners than center (capped)
    )

    return float(score)
