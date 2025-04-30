import os
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
from frame_height import detect_frame_periodicity
from frame_length import find_optimal_line_length, reconstruct_test_image
from plotting import save_reconstructed_image
from tqdm import tqdm


def load_data(filename: str) -> np.ndarray:
    """Load the captured data from a binary file."""
    try:
        data = np.fromfile(filename, dtype=np.int16)
        print(f'Loaded {len(data)} samples')
        return data
    except Exception as e:
        print(f'Error loading data: {e}')
        sys.exit(1)


def extract_video_frames(
    data: np.ndarray,
    line_length: float,
    offset: int,
    height: int,
    output_dir: str,
    max_frames: int = 0,
) -> str:
    """
    Extract all frames from the data and save them sequentially for video reconstruction.
    Ensures frames have dimensions divisible by 2 for H.264 compatibility.

    Args:
        data: The source TEMPEST signal data
        line_length: The optimal line length
        offset: The optimal offset
        height: The height of each frame in lines
        output_dir: Directory to save the frames
        max_frames: Maximum number of frames to extract (0 = all)

    Returns:
        Path to the frames directory
    """
    print('Extracting frames for video reconstruction...')

    # Create frames directory
    frames_dir = os.path.join(output_dir, 'video_frames')
    os.makedirs(frames_dir, exist_ok=True)

    # Calculate frame size in samples
    frame_size = int(line_length * height)

    # Calculate how many complete frames we can extract
    data_with_offset = data[offset:]
    num_frames = len(data_with_offset) // frame_size

    if max_frames > 0 and max_frames < num_frames:
        num_frames = max_frames

    print(f'Extracting {num_frames} frames...')

    # Check if dimensions need to be adjusted for H.264 compatibility
    if height % 2 != 0 or int(line_length) % 2 != 0:
        print('Note: Frames will be cropped to ensure even dimensions for H.264 compatibility')

    # Extract and save each frame
    for i in tqdm(range(num_frames)):
        frame_start = i * frame_size
        frame_end = frame_start + frame_size

        if frame_end > len(data_with_offset):
            break

        frame_data = data_with_offset[frame_start:frame_end]
        image = reconstruct_test_image(frame_data, line_length, height)

        # Ensure dimensions are divisible by 2 for H.264 compatibility
        h, w = image.shape
        target_h = h - (h % 2)  # Make height even
        target_w = w - (w % 2)  # Make width even

        # Crop if necessary
        if h != target_h or w != target_w:
            image = image[:target_h, :target_w]

        # Save the frame with sequential numbering (important for ffmpeg)
        output_file = os.path.join(frames_dir, f'frame_{i:04d}.png')
        plt.figure(figsize=(10, 8))
        plt.imshow(image, cmap='gray')
        plt.axis('off')  # No axes for video frames
        plt.tight_layout(pad=0)  # No padding
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
        plt.close()

    print(f'Saved {num_frames} frames to {frames_dir}')
    return frames_dir


def create_video_from_frames(frames_dir: str, output_file: str, framerate: int = 30) -> None:
    """
    Create a video from the extracted frames using ffmpeg.
    Handles frames with dimensions that might not be divisible by 2.

    Args:
        frames_dir: Directory containing the frame images
        output_file: Path to save the output video
        framerate: Frames per second for the output video
    """
    try:
        # Check if ffmpeg is installed
        subprocess.run(  # noqa: S603
            ['ffmpeg', '-version'],  # noqa: S607
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        print(f'Creating video from frames with framerate {framerate} fps...')

        # Build ffmpeg command with options to handle dimensions
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-framerate',
            str(framerate),
            '-i',
            os.path.join(frames_dir, 'frame_%04d.png'),
            '-c:v',
            'libx264',
            '-profile:v',
            'high',
            '-crf',
            '20',  # Quality setting (lower is better quality)
            '-vf',
            'pad=ceil(iw/2)*2:ceil(ih/2)*2',  # Pad to even dimensions if needed
            '-pix_fmt',
            'yuv420p',  # For better compatibility
            output_file,
        ]

        # Run ffmpeg
        subprocess.run(cmd, check=True)  # noqa: S603
        print(f'Video created successfully: {output_file}')

    except subprocess.CalledProcessError as e:
        print('Error: ffmpeg command failed.')
        print(f'Error details: {e}')
        print('Please install ffmpeg to create videos:')
        print('  - Ubuntu/Debian: sudo apt-get install ffmpeg')
        print('  - macOS: brew install ffmpeg')
        print('  - Windows: Download from https://ffmpeg.org/download.html')
        print('\nAlternatively, you can create the video manually with:')
        print(
            f"ffmpeg -framerate {framerate} -i {os.path.join(frames_dir, 'frame_%04d.png')}",
            f"-c:v libx264 -vf 'pad=ceil(iw/2)*2:ceil(ih/2)*2' -pix_fmt yuv420p {output_file}",
        )

    except Exception as e:
        print(f'Error creating video: {e}')


def main() -> None:
    data_file = 'le-calme-avant-la-tempest.bin'
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    print('Loading TEMPEST signal data...')
    data = load_data(data_file)

    print('\nSearching for optimal line length across full range (256-1200)...')
    line_length = find_optimal_line_length(data)

    # Now detect frame height and offset using the entire data
    best_height, best_offset = detect_frame_periodicity(data, line_length)
    print(f'Optimal frame parameters - Height: {best_height}, Offset: {best_offset}')

    # Create the final image with the optimal parameters
    final_image = reconstruct_test_image(data[best_offset:], line_length, best_height)

    save_reconstructed_image(output_dir, line_length, best_height, best_offset, final_image)

    print(f'Reconstruction complete. Final image saved to {output_dir}/final_image.png')
    print(f'Optimal parameters: Line Length={line_length:.2f}, Offset={best_offset}, Height={best_height}')

    # Ask user if they want to create a video
    create_video = (
        str(input('\nDo you want to extract all frames and create a video? (Y/n): ') or 'y').lower().startswith('y')
    )

    if create_video:
        # Ask for video parameters
        try:
            max_frames = int(input('Maximum number of frames to extract (0 = all): ') or '0')
            framerate = int(input('Framerate for video (fps, default = 12): ') or '12')
        except ValueError:
            print('Invalid input, using defaults.')
            max_frames = 0
            framerate = 30

        # Extract all frames
        frames_dir = extract_video_frames(data, line_length, best_offset, best_height, output_dir, max_frames)

        # Create video file
        video_file = os.path.join(output_dir, 'tempest_video.mp4')
        create_video_from_frames(frames_dir, video_file, framerate)

        print('\nVideo reconstruction process complete!')
        print(f'Video saved to: {video_file}')
    else:
        print('\nVideo creation skipped.')

    print('\nThank you for using the TEMPEST video reconstruction tool!')


if __name__ == '__main__':
    main()
