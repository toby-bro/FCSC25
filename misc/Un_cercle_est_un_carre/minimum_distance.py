import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


class point:
    def __init__(self, P: list[int]) -> None:
        self.coordinates = P

    def distance(self, P: 'point') -> int:
        assert len(P.coordinates) == len(self.coordinates), 'Dimension mismatch'
        dist: int = 0
        for i, j in zip(self.coordinates, P.coordinates, strict=False):
            dist += (i - j) ** 2
        return dist

    def __str__(self) -> str:
        return f'[{", ".join(str(x) for x in self.coordinates)}]'

    def __repr__(self) -> str:
        return f'point({", ".join(str(x) for x in self.coordinates)})'


def get_rotation_matrix(edge_start: point, edge_end: point, angle: float) -> np.ndarray:
    """
    Returns a rotation matrix for rotating around an edge of the cube.

    Args:
        edge_start: The starting point of the edge
        edge_end: The ending point of the edge
        angle: The rotation angle in radians

    Returns:
        A 3x3 numpy array representing the rotation matrix
    """
    # Convert edge points to numpy arrays
    p1 = np.array(edge_start.coordinates)
    p2 = np.array(edge_end.coordinates)

    # Calculate the vector representing the rotation axis (the edge)
    axis = p2 - p1
    axis = axis / np.linalg.norm(axis)  # Normalize to unit vector

    # Create the rotation matrix around an arbitrary axis
    # Using Rodrigues' rotation formula
    a = axis[0]
    b = axis[1]
    c = axis[2]

    # Projection matrix
    P = np.array(
        [
            [a * a, a * b, a * c],
            [a * b, b * b, b * c],
            [a * c, b * c, c * c],
        ],
    )

    # Cross product matrix
    K = np.array(
        [
            [0, -c, b],
            [c, 0, -a],
            [-b, a, 0],
        ],
    )

    # Rodrigues' rotation formula
    R = P + (np.eye(3) - P) * np.cos(angle) + K * np.sin(angle)

    return R  # noqa: RET504


def get_face(p: point, length: int) -> int:
    """
    Determine which face of the cube the point is on.

    Returns:
        0: x = 0 (left)
        1: x = length (right)
        2: y = 0 (bottom)
        3: y = length (top)
        4: z = 0 (back)
        5: z = length (front)
    """
    x, y, z = p.coordinates

    if x == 0:
        return 0
    if x == length:
        return 1
    if y == 0:
        return 2
    if y == length:
        return 3
    if z == 0:
        return 4
    if z == length:
        return 5

    raise ValueError(f'Point {p} is not on the surface of the cube')


def is_on_face(face: int, ptc: np.ndarray, length: int) -> bool:
    epsilon = 1e-5  # Small tolerance for floating point precision

    if face == 0:
        return abs(ptc[0]) < epsilon
    if face == 1:
        return abs(ptc[0] - length) < epsilon
    if face == 2:
        return abs(ptc[1]) < epsilon
    if face == 3:
        return abs(ptc[1] - length) < epsilon
    if face == 4:
        return abs(ptc[2]) < epsilon
    if face == 5:
        return abs(ptc[2] - length) < epsilon

    raise ValueError(f'Invalid face {face} for point {ptc}')


def get_edges_for_faces(face_p: int, face_q: int, length: int) -> tuple[point, point]:
    """
    Get the edges that belong to the faces p and q.

    Args:
        face_p (int): first face
        face_q (int): second face

    Returns:
        tuple[point, point]: the points of the edge between both faces
    """
    assert face_p != face_q, 'Faces must be different'
    assert (face_p, face_q) not in [(0, 1), (2, 3), (4, 5)], 'Faces must be adjacent'
    x, y, z = None, None, None
    if face_p == 0 or face_q == 0:
        x = 0
    if face_p == 1 or face_q == 1:
        x = length
    if face_p == 2 or face_q == 2:
        y = 0
    if face_p == 3 or face_q == 3:
        y = length
    if face_p == 4 or face_q == 4:
        z = 0
    if face_p == 5 or face_q == 5:
        z = length
    if x is None and y is not None and z is not None:
        return point([0, y, z]), point([length, y, z])
    if y is None and x is not None and z is not None:
        return point([x, 0, z]), point([x, length, z])
    if z is None and x is not None and y is not None:
        return point([x, y, 0]), point([x, y, length])
    raise ValueError('Invalid faces or coordinates')


def get_adjacent_faces(face: int, length: int) -> list[tuple[int, tuple[point, point]]]:
    """
    Get adjacent faces and the edges they share with the current face.

    Returns:
        List of tuples (adjacent_face, (edge_start, edge_end))
    """
    adj_faces = []

    # Define corners of the cube

    corners = [
        point([0, 0, 0]),
        point([length, 0, 0]),
        point([0, length, 0]),
        point([length, length, 0]),
        point([0, 0, length]),
        point([length, 0, length]),
        point([0, length, length]),
        point([length, length, length]),
    ]
    # Define edges for each face and its adjacent faces
    if face == 0:  # x = 0 (left)
        adj_faces.extend(
            [
                (2, (corners[0], corners[4])),  # Left->Bottom
                (3, (corners[2], corners[6])),  # Left->Top
                (4, (corners[0], corners[2])),  # Left->Back
                (5, (corners[4], corners[6])),  # Left->Front
            ],
        )
    elif face == 1:  # x = length (right)
        adj_faces.extend(
            [
                (2, (corners[1], corners[5])),  # Right->Bottom
                (3, (corners[3], corners[7])),  # Right->Top
                (4, (corners[1], corners[3])),  # Right->Back
                (5, (corners[5], corners[7])),  # Right->Front
            ],
        )
    elif face == 2:  # y = 0 (bottom)
        adj_faces.extend(
            [
                (0, (corners[0], corners[4])),  # Bottom->Left
                (1, (corners[1], corners[5])),  # Bottom->Right
                (4, (corners[0], corners[1])),  # Bottom->Back
                (5, (corners[4], corners[5])),  # Bottom->Front
            ],
        )
    elif face == 3:  # y = length (top)
        adj_faces.extend(
            [
                (0, (corners[2], corners[6])),  # Top->Left
                (1, (corners[3], corners[7])),  # Top->Right
                (4, (corners[2], corners[3])),  # Top->Back
                (5, (corners[6], corners[7])),  # Top->Front
            ],
        )
    elif face == 4:  # z = 0 (back)
        adj_faces.extend(
            [
                (0, (corners[0], corners[2])),  # Back->Left
                (1, (corners[1], corners[3])),  # Back->Right
                (2, (corners[0], corners[1])),  # Back->Bottom
                (3, (corners[2], corners[3])),  # Back->Top
            ],
        )
    elif face == 5:  # z = length (front)
        adj_faces.extend(
            [
                (0, (corners[4], corners[6])),  # Front->Left
                (1, (corners[5], corners[7])),  # Front->Right
                (2, (corners[4], corners[5])),  # Front->Bottom
                (3, (corners[6], corners[7])),  # Front->Top
            ],
        )

    return adj_faces


def calculate_unfolding_transformation(
    current_face: int,
    adjacent_face: int,
    edge: tuple[point, point],
    length: int,
    cumulative_transform: np.ndarray = np.eye(4),
) -> np.ndarray:
    """
    Calculate the transformation matrix for unfolding from current_face to adjacent_face
    taking into account previous unfolding transformations.

    Args:
        current_face: The index of the current face
        adjacent_face: The index of the adjacent face to unfold
        edge: The edge shared between the two faces (edge_start, edge_end)
        length: The length of the cube
        cumulative_transform: The accumulated transformations from previous unfolding steps

    Returns:
        A 4x4 transformation matrix that combines rotation and translation
    """
    edge_start, edge_end = edge
    edge_start_coords = np.array(edge_start.coordinates)
    edge_end_coords = np.array(edge_end.coordinates)

    # Calculate the edge vector in the current transformed space
    edge_start_homo = np.append(edge_start_coords, 1)
    edge_end_homo = np.append(edge_end_coords, 1)

    # Apply existing transforms to calculate current edge position
    transformed_start = cumulative_transform @ edge_start_homo
    transformed_end = cumulative_transform @ edge_end_homo

    # Calculate the edge vector in transformed space
    edge_vector = transformed_end[:3] - transformed_start[:3]
    edge_length = np.linalg.norm(edge_vector)
    axis = edge_vector / edge_length  # Normalize to unit vector

    # Original face normals in global coordinate system
    original_face_normals = {
        0: np.array([-1.0, 0.0, 0.0]),  # Left face normal (-x direction)
        1: np.array([1.0, 0.0, 0.0]),  # Right face normal (+x direction)
        2: np.array([0.0, -1.0, 0.0]),  # Bottom face normal (-y direction)
        3: np.array([0.0, 1.0, 0.0]),  # Top face normal (+y direction)
        4: np.array([0.0, 0.0, -1.0]),  # Back face normal (-z direction)
        5: np.array([0.0, 0.0, 1.0]),  # Front face normal (+z direction)
    }

    # Transform the face normals according to the cumulative transformation
    # We need to use the rotation part of the cumulative transform (3x3 upper-left matrix)
    rotation_part = cumulative_transform[:3, :3]

    # Transform both face normals
    normal1 = np.dot(rotation_part, original_face_normals[current_face])
    normal2 = np.dot(rotation_part, original_face_normals[adjacent_face])

    # Normalize the transformed normals
    normal1 = normal1 / np.linalg.norm(normal1)
    normal2 = normal2 / np.linalg.norm(normal2)

    # Calculate cross product of the transformed normals
    cross_prod = np.cross(normal1, normal2)
    cross_norm = np.linalg.norm(cross_prod)

    # If cross product is zero, the faces are parallel, which shouldn't happen for adjacent faces
    if cross_norm < 1e-10:
        raise ValueError(f'Faces {current_face} and {adjacent_face} appear to be parallel after transformation')

    # Normalize the cross product
    cross_unit = cross_prod / cross_norm

    # The rotation angle is always 90 degrees for cube unfolding
    rotation_angle = np.pi / 2

    # Check if the cross product and edge directions are aligned
    alignment = np.dot(cross_unit, axis)

    # If they're not aligned, flip the rotation direction
    if alignment < 0:
        rotation_angle = -rotation_angle

    # Build the rotation matrix relative to the transformed edge start
    translation_to_edge = np.eye(4)
    translation_to_edge[0:3, 3] = -transformed_start[:3]

    # Calculate the 3x3 rotation matrix using Rodrigues' formula
    a, b, c = axis
    K = np.array(
        [
            [0, -c, b],
            [c, 0, -a],
            [-b, a, 0],
        ],
    )
    P = np.outer(axis, axis)
    R = np.eye(3) * np.cos(rotation_angle) + K * np.sin(rotation_angle) + P * (1 - np.cos(rotation_angle))

    # Ensure orthogonality
    u = R[:, 0]
    v = R[:, 1] - np.dot(R[:, 1], u) * u / np.dot(u, u)
    w = np.cross(u, v)

    # Normalize
    u /= np.linalg.norm(u)
    v /= np.linalg.norm(v)
    w /= np.linalg.norm(w)

    R_ortho = np.column_stack((u, v, w))

    # Ensure it's a proper rotation (det = 1)
    if np.linalg.det(R_ortho) < 0:
        R_ortho[:, 2] = -R_ortho[:, 2]

    # Create 4x4 rotation matrix
    rotation_matrix = np.eye(4)
    rotation_matrix[0:3, 0:3] = R_ortho

    # Translation back
    translation_back = np.eye(4)
    translation_back[0:3, 3] = transformed_start[:3]

    # Combine transformations for this step
    transform_step = translation_back @ rotation_matrix @ translation_to_edge

    return transform_step


def unfold_cube(P: point, Q: point, length: int) -> list[np.ndarray]:
    """
    Find all possible positions of Q when unfolding the cube from P's face.

    Args:
        P: The starting point
        Q: The target point
        length: The length of the cube

    Returns:
        List of different positions of Q after unfolding the cube
    """
    face_P = get_face(P, length)
    face_Q = get_face(Q, length)

    # Track all positions of Q after different unfoldings
    all_Q_positions: list[np.ndarray] = []

    # Start the recursive unfolding
    unfold_recursive(P, Q, length, face_P, face_Q, {face_P}, np.eye(4), all_Q_positions)

    return all_Q_positions


def unfold_recursive(
    P: point,
    Q: point,
    length: int,
    current_face: int,
    target_face: int,
    visited_faces: set,
    cumulative_transform: np.ndarray,
    result: list,
) -> None:
    """
    Recursively unfold the cube to find all possible positions of Q.

    Args:
        P: The starting point
        Q: The target point
        length: The length of the cube
        current_face: The face currently being processed
        target_face: The face containing Q
        visited_faces: Set of faces already visited in this unfolding path
        cumulative_transform: Cumulative transformation matrix applied so far
        result: List to store all positions of Q after unfolding
    """
    # If we've reached the face with Q, calculate its unfolded position
    if current_face == target_face:
        # Convert Q coordinates to homogeneous coordinates (add 1 at the end)
        q_homogeneous = np.append(np.array(Q.coordinates, dtype=np.int64), 1)

        # Apply transformation
        unfolded_q_homogeneous = cumulative_transform @ q_homogeneous

        # Convert back to 3D coordinates and ensure result is integer
        unfolded_q = np.round(unfolded_q_homogeneous[0:3]).astype(np.int64)
        result.append(unfolded_q)
        return

    # Try unfolding each adjacent face
    for adj_face, edge in get_adjacent_faces(current_face, length):
        if adj_face not in visited_faces:
            # Calculate the transformation matrix for this unfolding step
            transform = calculate_unfolding_transformation(
                adj_face,
                current_face,
                edge,
                length,
                cumulative_transform,
            )

            # Update the cumulative transformation
            updated_transform = transform @ cumulative_transform

            # Mark this face as visited in this path
            new_visited = visited_faces.copy()
            new_visited.add(adj_face)

            # Recursively unfold from this new face
            unfold_recursive(
                P,
                Q,
                length,
                adj_face,
                target_face,
                new_visited,
                updated_transform,
                result,
            )


def plot_unfolded_cube(P: point, Q: point, length: int, save_path: str | None = None) -> None:
    """
    Plot all possible positions of Q when the cube is unfolded onto P's face.

    Args:
        P: The reference point
        Q: The target point
        length: The length of the cube
        save_path: Path to save the figure, if None, the figure is displayed
    """
    face_P = get_face(P, length)
    P_coords = np.array(P.coordinates)
    face_Q = get_face(Q, length)

    unfolded_positions = unfold_cube(P, Q, length)

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111)

    # Determine axis mapping based on P's face
    if face_P == 0:  # x = 0
        x_idx, y_idx = 1, 2  # y, z axes
        ax_labels = ['y', 'z']
        face_label = 'x=0 (Left)'
    elif face_P == 1:  # x = length
        x_idx, y_idx = 1, 2  # y, z axes
        ax_labels = ['y', 'z']
        face_label = f'x={length} (Right)'
    elif face_P == 2:  # y = 0
        x_idx, y_idx = 0, 2  # x, z axes
        ax_labels = ['x', 'z']
        face_label = 'y=0 (Bottom)'
    elif face_P == 3:  # y = length
        x_idx, y_idx = 0, 2  # x, z axes
        ax_labels = ['x', 'z']
        face_label = f'y={length} (Top)'
    elif face_P == 4:  # z = 0
        x_idx, y_idx = 0, 1  # x, y axes
        ax_labels = ['x', 'y']
        face_label = 'z=0 (Back)'
    else:  # z = length
        x_idx, y_idx = 0, 1  # x, y axes
        ax_labels = ['x', 'y']
        face_label = f'z={length} (Front)'

    ax.add_patch(Rectangle((0, 0), length, length, fill=False, edgecolor='black', linewidth=2))

    p_x, p_y = P_coords[x_idx], P_coords[y_idx]
    ax.scatter(p_x, p_y, color='red', s=100, label=f'P{P.coordinates}')

    min_dist = float('inf')
    closest_q = None

    for i, unfolded_Q in enumerate(unfolded_positions):
        q_x, q_y = unfolded_Q[x_idx], unfolded_Q[y_idx]

        dist = np.sum((P_coords - unfolded_Q) ** 2)

        q_label = f'Q{i}({dist:.0f})'

        if dist < min_dist:
            min_dist = dist
            closest_q = (q_x, q_y, dist, i)

        ax.scatter(q_x, q_y, color='blue', alpha=0.6, s=50)
        ax.text(q_x + 1, q_y + 1, q_label, fontsize=8)

    if closest_q:
        q_x, q_y, dist, idx = closest_q
        ax.scatter(q_x, q_y, color='green', s=100, label=f'Closest Q{idx}(dist={dist:.0f})')
        ax.plot([p_x, q_x], [p_y, q_y], 'g--', linewidth=2)

    min_x, max_x = 0, length
    min_y, max_y = 0, length

    for unfolded_Q in unfolded_positions:
        q_x, q_y = unfolded_Q[x_idx], unfolded_Q[y_idx]
        min_x = min(min_x, q_x - 5)
        max_x = max(max_x, q_x + 5)
        min_y = min(min_y, q_y - 5)
        max_y = max(max_y, q_y + 5)

    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_xlabel(ax_labels[0])
    ax.set_ylabel(ax_labels[1])
    ax.set_aspect('equal')

    ax.set_title(f'Unfolded Cube: P on {face_label}, Q on face {face_Q}\nMinimum distance = {min_dist:.0f}')

    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper right')

    if save_path:
        plt.savefig(save_path)
    else:
        plt.tight_layout()
        plt.show()


def minimumDistanceOnCube(length: int, P: point, Q: point) -> int:
    """
    Calculate the minimum distance between two points on a cube.

    Args:
        length: The length of the cube's edge
        P: The first point
        Q: The second point

    Returns:
        The minimum distance squared between the two points
    """
    face_P = get_face(P, length)
    face_Q = get_face(Q, length)

    if face_P == face_Q:
        return P.distance(Q)

    unfolded_positions = unfold_cube(P, Q, length)

    min_dist = float('inf')
    P_coords = np.array(P.coordinates, dtype=np.int64)

    for unfolded_Q in unfolded_positions:
        # Calculate squared distance ensuring integer math
        dist = np.sum((P_coords - unfolded_Q) ** 2)
        min_dist = min(min_dist, dist)

    return int(min_dist)  # Ensure the final result is an integer


if __name__ == '__main__':

    from random import randint

    def get_pt() -> point:
        return get_random_point_on_face(32)

    def get_random_point_on_face(length: int) -> point:
        face_p = randint(0, 5)
        r1 = randint(1, length - 1)
        r2 = randint(1, length - 1)

        if face_p // 2 == 0:  # x=0
            p = point([face_p * length, r1, r2])
        elif face_p // 2 == 1:  # y=0
            p = point([r1, (face_p % 2) * length, r2])
        elif face_p // 2 == 2:  # y=length
            p = point([r1, r2, (face_p % 2) * length])
        else:
            raise ValueError(f'Invalid face index: {face_p}')
        return p

    for _ in range(1000):
        pta = get_pt()
        ptb = get_pt()
        minimumDistanceOnCube(32, pta, ptb)
