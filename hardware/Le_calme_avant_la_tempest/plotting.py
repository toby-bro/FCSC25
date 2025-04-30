import os
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Colormap
from matplotlib.patches import Rectangle


def plot_comprehensive_search_progress(
    all_search_histories: list[dict[str, dict[float, float]]],
    output_dir: str,
    title: str,
    output_filename: str,
    x_label: str = 'Length',
) -> None:
    """
    Create a comprehensive plot showing the entire search progression across all search phases.

    Args:
        all_search_histories: list of search history dictionaries from different search phases
        output_dir: Directory to save the plot
        title: Title for the plot
        output_filename: Filename for the output plot
        x_label: Label for x-axis
    """
    plt.figure(figsize=(20, 12))

    # Use a range of distinct colors for different phases - updated to fix deprecation warning
    colors = plt.colormaps.get_cmap('tab20')
    markers = ['o', 's', '^', 'x', 'd', '*', 'p', 'h', 'v', '>']

    # Track the best overall point to highlight
    best_overall_x = None
    best_overall_y = -float('inf')
    best_overall_phase = None

    # Flatten all search histories for final annotation
    all_points: dict[float, float] = {}

    # Keep track of the overall phase index
    overall_idx = 0

    # Process each search history dictionary
    best_overall_x, best_overall_y, best_overall_phase = plot_search_phase_progress(
        all_search_histories,
        colors,
        markers,
        best_overall_y,
        all_points,
        overall_idx,
    )

    # Create an inset with zoomed view of the best region
    if best_overall_x is not None:
        # Determine zoom range (focus on the best region)
        plot_best_region_zoom(all_search_histories, colors, best_overall_x, best_overall_y)

    # Add labels and legend for the main plot
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('Quality Score', fontsize=14)
    plt.title(f'{title} - Full Search Progression', fontsize=16)
    plt.grid(True)

    # Create a more organized legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles, strict=False))
    plt.legend(
        by_label.values(),
        by_label.keys(),
        loc='upper center',
        bbox_to_anchor=(0.5, -0.08),
        fancybox=True,
        shadow=True,
        ncol=4,
        fontsize=10,
    )

    # Annotate the best overall value
    if best_overall_x is not None:
        plt.annotate(
            f'Best Value: {best_overall_x:.2f}\nScore: {best_overall_y:.4f}\nPhase: {best_overall_phase}',
            xy=(best_overall_x, best_overall_y),
            xytext=(0.02, 0.98),
            textcoords='axes fraction',
            arrowprops={'facecolor': 'black', 'shrink': 0.05, 'width': 1.5, 'headwidth': 8},
            bbox={'boxstyle': 'round,pad=0.5', 'fc': 'yellow', 'alpha': 0.7},
            horizontalalignment='left',
            verticalalignment='top',
            fontsize=12,
        )

    plt.savefig(os.path.join(output_dir, output_filename), dpi=150)
    plt.close()
    print(f'Comprehensive {title.lower()} search plot saved to {os.path.join(output_dir, output_filename)}')


def plot_best_region_zoom(
    all_search_histories: list[dict[str, dict[float, float]]],
    colors: Colormap,
    best_overall_x: float,
    best_overall_y: float,
) -> None:
    x_range = plt.xlim()[1] - plt.xlim()[0]
    zoom_width = min(50, x_range * 0.15)  # Zoom to 15% of full range or 50 units, whichever is smaller
    zoom_left = max(plt.xlim()[0], best_overall_x - zoom_width)
    zoom_right = min(plt.xlim()[1], best_overall_x + zoom_width)

    # Create inset axes
    axins = plt.axes((0.55, 0.2, 0.35, 0.35))  # [left, bottom, width, height]

    # Plot all data in the inset
    for search_history in all_search_histories:
        for phase_name, scores in search_history.items():
            # Only plot points in the zoom range
            filtered_x = [x for x in scores.keys() if zoom_left <= x <= zoom_right]
            if not filtered_x:
                continue

            filtered_y = [scores[x] for x in filtered_x]
            color = colors(list(search_history.keys()).index(phase_name) % 20)

            # Sort for proper line connection
            sorted_pairs = sorted(zip(filtered_x, filtered_y, strict=False))
            sorted_x, sorted_y = zip(*sorted_pairs, strict=False) if sorted_pairs else ([], [])

            axins.plot(sorted_x, sorted_y, '.-', color=color, alpha=0.7)

    # Highlight the best overall point in the inset
    axins.plot(
        best_overall_x,
        best_overall_y,
        'o',
        color='red',
        markersize=10,
        markeredgecolor='black',
        markeredgewidth=2,
    )

    # Set inset limits
    axins.set_xlim(zoom_left, zoom_right)

    # Find y-range in the zoomed region
    all_y_in_range = []
    for search_history in all_search_histories:
        for scores in search_history.values():
            all_y_in_range.extend([y for x, y in scores.items() if zoom_left <= x <= zoom_right])

    if all_y_in_range:
        y_min = min(all_y_in_range) * 0.95
        y_max = max(all_y_in_range) * 1.05
        axins.set_ylim(y_min, y_max)

    axins.set_title(f'Zoom around best value: {best_overall_x:.2f}')
    axins.grid(True)


def highlight_best_phase_point(
    best_overall_y: float,
    all_points: dict[float, float],
    phase_name: str,
    x_sorted: list[float],
    y_sorted: list[float],
    color: tuple[float, float, float, float],
) -> tuple[float, float, str]:
    best_idx = np.argmax(y_sorted)
    best_x = x_sorted[best_idx]
    best_y = y_sorted[best_idx]

    # Add to all points dictionary
    all_points[best_x] = all_points.get(best_x, 0)

    # Update overall best if this is better
    if best_y > best_overall_y:
        best_overall_x = best_x
        best_overall_y = best_y
        best_overall_phase = phase_name

        # Highlight the best point in this phase
    plt.plot(
        best_x,
        best_y,
        'o',
        color=color,
        markersize=10,
        markeredgecolor='black',
        markeredgewidth=2,
    )

    return best_overall_y, best_overall_x, best_overall_phase


def plot_search_phase_progress(
    all_search_histories: list[dict[str, dict[float, float]]],
    colors: Colormap,
    markers: list[str],
    best_overall_y: float,
    all_points: dict[float, float],
    overall_idx: int,
) -> tuple[float, float, str]:
    for search_history in all_search_histories:
        for phase_name, scores in search_history.items():
            # Sort values for plotting
            x = list(scores.keys())
            y = list(scores.values())
            sorted_pairs = sorted(zip(x, y, strict=False))
            x_sorted, y_sorted = zip(*sorted_pairs, strict=False) if sorted_pairs else ([], [])
            if TYPE_CHECKING:
                assert isinstance(x_sorted, list)
                assert isinstance(y_sorted, list)

            # Get color and marker for this phase
            color = colors(overall_idx % 20)
            marker = markers[overall_idx % len(markers)]

            # Plot this phase
            plt.plot(
                x_sorted,
                y_sorted,
                label=f'{phase_name}',
                color=color,
                marker=marker,
                markersize=6,
                linestyle='-' if 'Binary' not in phase_name else '--',  # Dashed for binary search
                alpha=0.8,
                linewidth=2,
            )

            # Find and highlight the best point in this phase
            if y_sorted:
                best_overall_y, best_overall_x, best_overall_phase = highlight_best_phase_point(
                    best_overall_y,
                    all_points,
                    phase_name,
                    x_sorted,
                    y_sorted,
                    color,
                )

            overall_idx += 1
    return best_overall_x, best_overall_y, best_overall_phase


def plot_autocorrelation(
    analysis_dir: str,
    autocorr: Any,
    peaks: np.ndarray[tuple[int], np.dtype[np.intp]],
    frame_height: int,
) -> None:
    plt.figure(figsize=(15, 6))
    plt.plot(autocorr)
    plt.plot(peaks, autocorr[peaks], 'rx')
    plt.axvline(x=frame_height, color='g', linestyle='--')
    plt.title('Row-Mean Autocorrelation for Height Detection')
    plt.xlabel('Lag (pixels)')
    plt.ylabel('Autocorrelation')
    plt.grid(True)
    plt.savefig(f'{analysis_dir}/height_autocorrelation.png')
    plt.close()


def plot_candidate_frames(
    analysis_dir: str,
    num_candidates: int,
    diff_scores: list,
    height: int,
    frames: list,
    score: float | np.floating,
) -> None:
    if len(diff_scores) <= num_candidates or score > sorted(diff_scores[:-1])[-num_candidates]:
        plt.figure(figsize=(15, 10))
        for i in range(min(2, len(frames))):
            plt.subplot(1, 2, i + 1)
            plt.imshow(frames[i], cmap='gray')
            plt.title(f'Frame {i+1}')
        plt.suptitle(f'Height: {height}, Similarity Score: {score:.6f}')
        plt.tight_layout()
        plt.savefig(f'{analysis_dir}/frame_diff_height_{height}.png')
        plt.close()


def plot_similarity_scores(
    analysis_dir: str,
    potential_heights: list[int],
    diff_scores: list,
) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(potential_heights, diff_scores, 'o-')
    plt.grid(True)
    plt.xlabel('Frame Height')
    plt.ylabel('Frame Similarity Score (higher is better)')
    plt.title('Frame Height vs. Inter-Frame Similarity')
    plt.savefig(f'{analysis_dir}/height_similarity_scores.png')
    plt.close()


def plot_best_frame_results(analysis_dir: str, height: np.int_ | int, frames: list, score: float) -> None:
    plt.figure(figsize=(15, 10))
    for i in range(min(2, len(frames))):
        plt.subplot(1, 2, i + 1)
        plt.imshow(frames[i], cmap='gray')
        plt.title(f'Frame {i+1}')
    plt.suptitle(f'New Best - Height: {height}, Similarity: {score:.6f}')
    plt.tight_layout()
    plt.savefig(f'{analysis_dir}/best_height_{height}.png')
    plt.close()


def visualize_final_offset(frame_height: int, analysis_dir: str, test_image: np.ndarray, best_offset: int) -> None:
    plt.figure(figsize=(12, 10))
    plt.imshow(test_image, cmap='gray')
    plt.axhline(y=frame_height, color='r', linestyle='--', label='Frame Boundary')
    plt.title(f'Final Optimal Offset: {best_offset}')
    plt.legend()
    plt.savefig(f'{analysis_dir}/final_optimal_offset.png')
    plt.close()


def visualize_corner_entropy(
    image: np.ndarray,
    corner_entropy: list[float],
    center_entropy: float,
    offset: int,
    score: float,
    frame_height: int,
    analysis_dir: str,
) -> None:
    """Visualize frame with corner and center entropy regions highlighted."""
    # Focus on first frame
    analysis_height = min(image.shape[0], frame_height)
    frame = image[:analysis_height, :]
    height, width = frame.shape

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(frame, cmap='gray')

    # Define corner regions
    corner_size_h = int(height * 0.15)
    corner_size_w = int(width * 0.15)

    # Define center region
    center_h_start = int(height * 0.25)
    center_h_end = int(height * 0.75)
    center_w_start = int(width * 0.25)
    center_w_end = int(width * 0.75)

    # Highlight regions with rectangles
    # Top-left
    tl_rect = Rectangle((0, 0), corner_size_w, corner_size_h, linewidth=2, edgecolor='r', facecolor='none')
    ax.add_patch(tl_rect)
    ax.text(
        5,
        15,
        f'TL: {corner_entropy[0]:.3f}',
        color='white',
        fontsize=10,
        bbox={'facecolor': 'black', 'alpha': 0.5},
    )

    # Top-right
    tr_rect = Rectangle(
        (width - corner_size_w, 0),
        corner_size_w,
        corner_size_h,
        linewidth=2,
        edgecolor='g',
        facecolor='none',
    )
    ax.add_patch(tr_rect)
    ax.text(
        width - corner_size_w + 5,
        15,
        f'TR: {corner_entropy[1]:.3f}',
        color='white',
        fontsize=10,
        bbox={'facecolor': 'black', 'alpha': 0.5},
    )

    # Bottom-left
    bl_rect = Rectangle(
        (0, height - corner_size_h),
        corner_size_w,
        corner_size_h,
        linewidth=2,
        edgecolor='b',
        facecolor='none',
    )
    ax.add_patch(bl_rect)
    ax.text(
        5,
        height - corner_size_h + 15,
        f'BL: {corner_entropy[2]:.3f}',
        color='white',
        fontsize=10,
        bbox={'facecolor': 'black', 'alpha': 0.5},
    )

    # Bottom-right
    br_rect = Rectangle(
        (width - corner_size_w, height - corner_size_h),
        corner_size_w,
        corner_size_h,
        linewidth=2,
        edgecolor='y',
        facecolor='none',
    )
    ax.add_patch(br_rect)
    ax.text(
        width - corner_size_w + 5,
        height - corner_size_h + 15,
        f'BR: {corner_entropy[3]:.3f}',
        color='white',
        fontsize=10,
        bbox={'facecolor': 'black', 'alpha': 0.5},
    )

    # Center region
    center_rect = Rectangle(
        (center_w_start, center_h_start),
        center_w_end - center_w_start,
        center_h_end - center_h_start,
        linewidth=2,
        edgecolor='cyan',
        facecolor='none',
    )
    ax.add_patch(center_rect)
    ax.text(
        center_w_start + 5,
        center_h_start + 15,
        f'Center: {center_entropy:.3f}',
        color='cyan',
        fontsize=10,
        bbox={'facecolor': 'black', 'alpha': 0.5},
    )

    # Add title with stats
    mean_corner = np.mean(corner_entropy)
    std_corner = np.std(corner_entropy)
    ax.set_title(
        f'Offset: {offset}, Score: {score:.4f}\n'
        f'Corner Mean: {mean_corner:.3f}, Std: {std_corner:.3f}, Ratio: {mean_corner/max(0.001, center_entropy):.2f}',
    )

    # Save figure
    plt.tight_layout()
    plt.savefig(f'{analysis_dir}/corner_entropy_offset_{offset}.png')
    plt.close(fig)


def plot_corner_entropy_values(
    offsets: list[int],
    scores: list[float],
    corner_values: dict[int, list[float]],
    center_values: dict[int, float],
    best_offset: int,
    analysis_dir: str,
) -> None:
    """Create a summary plot of corner entropy values and scores for all offsets."""
    # Create multi-panel figure
    fig, axs = plt.subplots(3, 1, figsize=(14, 15), gridspec_kw={'height_ratios': [1, 1, 1]})

    # Plot 1: Offset scores
    axs[0].plot(offsets, scores, 'o-')
    axs[0].axvline(x=best_offset, color='r', linestyle='--', label=f'Best Offset: {best_offset}')
    axs[0].set_title('Offset Quality Scores')
    axs[0].set_xlabel('Offset')
    axs[0].set_ylabel('Score')
    axs[0].grid(True)
    axs[0].legend()

    # Plot 2: Corner entropy values
    if corner_values:
        offset_list = sorted(corner_values.keys())

        # Extract values for each corner
        tl_values = [corner_values[offset][0] for offset in offset_list]
        tr_values = [corner_values[offset][1] for offset in offset_list]
        bl_values = [corner_values[offset][2] for offset in offset_list]
        br_values = [corner_values[offset][3] for offset in offset_list]
        center_vals = [center_values.get(offset, 0) for offset in offset_list]

        # Calculate mean and std
        corner_means = [
            (a + b + c + d) / 4 for a, b, c, d in zip(tl_values, tr_values, bl_values, br_values, strict=False)
        ]
        corner_stds = [
            np.std([a, b, c, d]) for a, b, c, d in zip(tl_values, tr_values, bl_values, br_values, strict=False)
        ]

        # Plot individual corner values
        axs[1].plot(offset_list, tl_values, 'r-', label='Top-Left', alpha=0.7)
        axs[1].plot(offset_list, tr_values, 'g-', label='Top-Right', alpha=0.7)
        axs[1].plot(offset_list, bl_values, 'b-', label='Bottom-Left', alpha=0.7)
        axs[1].plot(offset_list, br_values, 'y-', label='Bottom-Right', alpha=0.7)
        axs[1].plot(offset_list, center_vals, 'c-', label='Center', alpha=0.7)
        axs[1].axvline(x=best_offset, color='r', linestyle='--')
        axs[1].set_title('Corner Entropy Values by Offset')
        axs[1].set_xlabel('Offset')
        axs[1].set_ylabel('Entropy')
        axs[1].grid(True)
        axs[1].legend()

        # Plot 3: Corner statistics - mean, std, ratio to center
        ax3 = axs[2]
        ax3.plot(offset_list, corner_means, 'm-', label='Corner Mean', linewidth=2)
        ax3.fill_between(
            offset_list,
            [m - s for m, s in zip(corner_means, corner_stds, strict=False)],
            [m + s for m, s in zip(corner_means, corner_stds, strict=False)],
            color='m',
            alpha=0.2,
            label='±1 Std Dev',
        )

        # Plot corner-to-center ratio on secondary y-axis
        ax3_twin = ax3.twinx()
        ratio_values = [m / max(0.001, c) for m, c in zip(corner_means, center_vals, strict=False)]
        ax3_twin.plot(offset_list, ratio_values, 'g-', label='Corner/Center Ratio')
        ax3_twin.set_ylabel('Corner/Center Ratio', color='g')
        ax3_twin.tick_params(axis='y', colors='g')

        # Highlight best offset
        ax3.axvline(x=best_offset, color='r', linestyle='--')
        ax3.set_title('Corner Entropy Statistics')
        ax3.set_xlabel('Offset')
        ax3.set_ylabel('Entropy Mean & Std')
        ax3.grid(True)

        # Create combined legend
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    # Save figure
    plt.tight_layout()
    plt.savefig(f'{analysis_dir}/corner_entropy_summary.png')
    plt.close(fig)


def plot_line_length_image(output_dir: str, line_length: np.floating, image: np.ndarray, combined_score: float) -> None:
    plt.figure(figsize=(10, 8))
    plt.imshow(image, cmap='gray')
    plt.title(f'Line Length: {line_length:.2f} (Score: {combined_score:.4f})')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/line_length_{line_length:.2f}.png')
    plt.close()


def plot_sample_image(actual_max_height: int, sample_image: np.ndarray, analysis_dir: str) -> None:
    plt.figure(figsize=(12, min(24, actual_max_height / 50)))
    plt.imshow(sample_image, cmap='gray')
    plt.title(f'Analysis Image ({actual_max_height} lines)')
    plt.savefig(f'{analysis_dir}/analysis_image.png', bbox_inches='tight')
    plt.close()


def save_reconstructed_image(
    output_dir: str,
    line_length: float,
    best_height: int,
    best_offset: int,
    final_image: np.ndarray,
) -> None:
    plt.figure(figsize=(12, 10))
    plt.imshow(final_image, cmap='gray')
    plt.title(
        f'Reconstructed TEMPEST Signal\nLine Length: {line_length:.2f}, Offset: {best_offset}, Height: {best_height}',
    )
    plt.tight_layout()
    plt.savefig(f'{output_dir}/final_image.png')
    plt.close()
