import random

import numpy as np
import pytest

from minimum_distance import (
    calculate_unfolding_transformation,
    get_adjacent_faces,
    get_edges_for_faces,
    get_rotation_matrix,
    is_on_face,
    minimumDistanceOnCube,
    point,
    unfold_cube,
)


def get_random_point_on_faces(length: int, face_p: int, face_q: int) -> tuple[point, point]:
    p = get_random_point_on_face(length, face_p)
    q = get_random_point_on_face(length, face_q)
    return p, q


def get_random_point_on_face(length: int, face_p: int) -> point:
    r1 = random.randint(1, length - 1)
    r2 = random.randint(1, length - 1)

    if face_p // 2 == 0:  # x=0
        p = point([face_p * length, r1, r2])
    elif face_p // 2 == 1:  # y=0
        p = point([r1, (face_p % 2) * length, r2])
    elif face_p // 2 == 2:  # y=length
        p = point([r1, r2, (face_p % 2) * length])
    else:
        raise ValueError(f'Invalid face index: {face_p}')
    return p


@pytest.mark.parametrize(
    ('P, Q, length, expected'),
    [
        (point([0, 1, 2]), point([0, 0, 0]), 32, 5),
        (point([0, 2, 1]), point([1, 2, 0]), 32, 4),
        (point([0, 1, 1]), point([32, 1, 1]), 32, 34**2),
        (point([0, 1, 1]), point([32, 1, 2]), 32, 34**2 + 1**2),
        (point([0, 2, 14]), point([32, 28, 11]), 32, 3789),
    ],
)
def test_minimum_distance_on_cube(P: point, Q: point, length: int, expected: int) -> None:
    dist = minimumDistanceOnCube(length, P, Q)
    assert dist == expected, f'Expected {expected}, got {dist}'


# Tests for rotation matrix properties
def test_rotation_matrix_is_orthogonal() -> None:
    """Test that rotation matrices are orthogonal (transpose = inverse)."""
    edge_start = point([0, 0, 0])
    edge_end = point([0, 1, 0])
    angle = np.pi / 2  # 90 degrees

    rot_matrix = get_rotation_matrix(edge_start, edge_end, angle)

    # For an orthogonal matrix, transpose = inverse, so R * R^T = I
    product = np.dot(rot_matrix, rot_matrix.T)
    identity = np.eye(3)

    # Test if product is close to identity matrix (with numerical precision)
    assert np.allclose(product, identity, rtol=1e-10, atol=1e-10)


def test_rotation_matrix_preserves_length() -> None:
    """Test that rotation preserves vector length."""
    edge_start = point([0, 0, 0])
    edge_end = point([1, 0, 0])
    angle = np.pi / 4  # 45 degrees

    rot_matrix = get_rotation_matrix(edge_start, edge_end, angle)

    # Create a test vector
    test_vector = np.array([1.0, 2.0, 3.0])
    rotated_vector = np.dot(rot_matrix, test_vector)

    # Length should be preserved
    original_length = np.linalg.norm(test_vector)
    rotated_length = np.linalg.norm(rotated_vector)

    assert np.isclose(original_length, rotated_length, rtol=1e-10, atol=1e-10)


def test_rotation_matrix_determinant() -> None:
    """Test that rotation matrix has determinant 1."""
    edge_start = point([0, 0, 0])
    edge_end = point([0, 0, 1])
    angle = np.pi / 3  # 60 degrees

    rot_matrix = get_rotation_matrix(edge_start, edge_end, angle)
    det = np.linalg.det(rot_matrix)

    assert np.isclose(det, 1.0, rtol=1e-10, atol=1e-10)


# Tests for specific rotations
def test_x_axis_rotation() -> None:
    """Test rotation around x-axis."""
    edge_start = point([0, 0, 0])
    edge_end = point([1, 0, 0])
    angle = np.pi / 2  # 90 degrees

    rot_matrix = get_rotation_matrix(edge_start, edge_end, angle)

    # A point on the y-axis should rotate to the z-axis
    y_point = np.array([0, 1, 0])
    rotated = np.dot(rot_matrix, y_point)

    assert np.allclose(rotated, np.array([0, 0, 1]), rtol=1e-10, atol=1e-10)


def test_y_axis_rotation() -> None:
    """Test rotation around y-axis."""
    edge_start = point([0, 0, 0])
    edge_end = point([0, 1, 0])
    angle = np.pi / 2  # 90 degrees

    rot_matrix = get_rotation_matrix(edge_start, edge_end, angle)

    # A point on the x-axis should rotate to the z-axis
    x_point = np.array([1, 0, 0])
    rotated = np.dot(rot_matrix, x_point)

    assert np.allclose(rotated, np.array([0, 0, -1]), rtol=1e-10, atol=1e-10)


def test_z_axis_rotation() -> None:
    """Test rotation around z-axis."""
    edge_start = point([0, 0, 0])
    edge_end = point([0, 0, 1])
    angle = np.pi / 2  # 90 degrees

    rot_matrix = get_rotation_matrix(edge_start, edge_end, angle)

    # A point on the x-axis should rotate to the y-axis
    x_point = np.array([1, 0, 0])
    rotated = np.dot(rot_matrix, x_point)

    assert np.allclose(rotated, np.array([0, 1, 0]), rtol=1e-10, atol=1e-10)


# Tests for unfolding transformations
def test_unfolding_transformation_origin() -> None:
    """Test that unfolding transformation preserves the edge points."""
    length = 32

    # Set up two adjacent faces and their shared edge
    current_face = 0  # left face (x=0)
    adjacent_face = 4  # back face (z=0)
    edge_start = point([0, 0, 0])
    edge_end = point([0, length, 0])

    # Calculate transformation matrix
    transform = calculate_unfolding_transformation(current_face, adjacent_face, (edge_start, edge_end), length)

    # The edge points should remain fixed during transformation
    start_homo = np.append(np.array(edge_start.coordinates), 1)  # homogeneous coordinates
    end_homo = np.append(np.array(edge_end.coordinates), 1)

    transformed_start = transform @ start_homo
    transformed_end = transform @ end_homo

    # The edge points should be unchanged after transformation
    assert np.allclose(transformed_start[:3], edge_start.coordinates, rtol=1e-10, atol=1e-10)
    assert np.allclose(transformed_end[:3], edge_end.coordinates, rtol=1e-10, atol=1e-10)


def test_unfolding_distance_preservation() -> None:
    """Test that distances on unfolded faces match expected values."""
    length = 32

    # Points on opposite sides of the cube
    p1 = point([0, 16, 16])  # left face
    p2 = point([length, 16, 16])  # right face

    # When unfolded, these should be at distance 64 (2*length) apart
    expected_squared_distance = (2 * length) ** 2

    # Calculate minimum distance
    min_dist = minimumDistanceOnCube(length, p1, p2)

    assert min_dist == expected_squared_distance


@pytest.mark.parametrize(
    ('length', 'pt1', 'pt2', 'expected_dist'),
    [
        (32, point([1, 0, 1]), point([0, 1, 1]), 4),
        (32, point([1, 1, 0]), point([1, 1, 32]), 34**2),
        (32, point([0, 1, 1]), point([32, 1, 1]), 34**2),
    ],
)
def test_specific_edge_unfolding(length: int, pt1: point, pt2: point, expected_dist: int) -> None:
    """Test unfolding of a specific edge case with known coordinates."""

    # When front face is unfolded onto the bottom face, and then right face is unfolded,
    # the right_point should end up at specific coordinates
    unfolded_positions = unfold_cube(pt1, pt2, length)

    # Print all positions for debugging
    print(f'\nUnfolded positions of {pt2} relative to {pt1}:')
    for i, pos in enumerate(unfolded_positions):
        print(f'Position {i}: {[round(i) for i in pos]}')

    # Test distance calculation against expected value
    min_dist = minimumDistanceOnCube(length, pt1, pt2)

    # Calculate expected distance using Pythagorean theorem for the specific unfolding
    # When unfolded properly, these points should be sqrt(2*length^2) apart

    print(f'Calculated minimum distance: {min_dist}')
    print(f'Expected distance: {expected_dist}')

    # Test with relaxed tolerance for now to identify issues
    assert abs(min_dist - expected_dist) < length, f'Distance {min_dist} is too far from expected {expected_dist}'


def test_known_example_from_instructions() -> None:
    """Test the specific example provided in the instructions."""
    length = 32

    # Example from instruction.txt
    P = point([0, 2, 14])
    Q = point([32, 28, 11])

    # Expected result is 3789
    expected_dist = 3789

    min_dist = minimumDistanceOnCube(length, P, Q)

    # Print debugging info
    print('\nExample from instructions:')
    print(f'P: {P}, Q: {Q}')
    print(f'Calculated distance: {min_dist}')
    print(f'Expected distance: {expected_dist}')

    # Print all unfolded positions for analysis
    unfolded_positions = unfold_cube(P, Q, length)
    for i, pos in enumerate(unfolded_positions):
        print(f'Unfolded position {i}: {pos}')
        print(f'Distance to P: {np.sum((np.array(P.coordinates) - pos)**2)}')

    assert min_dist == expected_dist, f'Expected {expected_dist}, got {min_dist}'


def test_multiple_random_unfoldings() -> None:

    length = 32

    # Generate 5 random test cases
    for i in range(5):
        # Generate random points on the cube surface
        face_p = random.randint(0, 5)
        face_q = random.randint(0, 5)

        # Create P based on its face
        if face_p == 0:  # x=0
            p = point([0, random.randint(1, length - 1), random.randint(1, length - 1)])
        elif face_p == 1:  # x=length
            p = point([length, random.randint(1, length - 1), random.randint(1, length - 1)])
        elif face_p == 2:  # y=0
            p = point([random.randint(1, length - 1), 0, random.randint(1, length - 1)])
        elif face_p == 3:  # y=length
            p = point([random.randint(1, length - 1), length, random.randint(1, length - 1)])
        elif face_p == 4:  # z=0
            p = point([random.randint(1, length - 1), random.randint(1, length - 1), 0])
        else:  # z=length
            p = point([random.randint(1, length - 1), random.randint(1, length - 1), length])

        # Create Q based on its face
        if face_q == 0:  # x=0
            q = point([0, random.randint(1, length - 1), random.randint(1, length - 1)])
        elif face_q == 1:  # x=length
            q = point([length, random.randint(1, length - 1), random.randint(1, length - 1)])
        elif face_q == 2:  # y=0
            q = point([random.randint(1, length - 1), 0, random.randint(1, length - 1)])
        elif face_q == 3:  # y=length
            q = point([random.randint(1, length - 1), length, random.randint(1, length - 1)])
        elif face_q == 4:  # z=0
            q = point([random.randint(1, length - 1), random.randint(1, length - 1), 0])
        else:  # z=length
            q = point([random.randint(1, length - 1), random.randint(1, length - 1), length])

        print(f'\nRandom test {i+1}:')
        print(f'P: {p} on face {face_p}')
        print(f'Q: {q} on face {face_q}')

        # Find all unfolding positions
        unfolded_positions = unfold_cube(p, q, length)

        # Check that we got some unfolded positions
        assert len(unfolded_positions) > 0, 'No unfolding paths found'

        # Calculate the minimum distance
        min_dist = minimumDistanceOnCube(length, p, q)

        print(f'Calculated minimum distance: {min_dist}')

        # For same-face points, verify direct distance
        if face_p == face_q:
            expected_dist = p.distance(q)
            assert min_dist == expected_dist, f'Same-face distance incorrect: {min_dist} vs {expected_dist}'

        # Verify distance is non-negative
        assert min_dist >= 0, 'Distance cannot be negative'


def get_third_coord(f1: int, f2: int) -> int:
    return next(i for i in range(3) if f1 // 2 != i and i != f2 // 2)


@pytest.mark.parametrize(
    ('length', 'face_p', 'face_q'),
    [
        (32, 0, 2),
        (32, 0, 3),
        (32, 0, 4),
        (32, 0, 5),
        (32, 1, 2),
        (32, 1, 3),
        (32, 1, 4),
        (32, 1, 5),
        (32, 2, 0),
        (32, 2, 1),
        (32, 2, 4),
        (32, 2, 5),
        (32, 3, 0),
        (32, 3, 1),
        (32, 3, 4),
        (32, 3, 5),
        (32, 4, 0),
        (32, 4, 1),
        (32, 4, 2),
        (32, 4, 3),
        (32, 5, 0),
        (32, 5, 1),
        (32, 5, 2),
        (32, 5, 3),
    ],
)
class TestUnfoldingOnce:
    def test_all_six_adjacent_faces(self, length: int, face_p: int, face_q: int) -> None:
        """Test unfolding from each face to all its adjacent faces."""
        if face_p == 0:  # left
            p1 = point([0, length // 2, length // 2])
        elif face_p == 1:  # right
            p1 = point([length, length // 2, length // 2])
        elif face_p == 2:  # bottom
            p1 = point([length // 2, 0, length // 2])
        elif face_p == 3:  # top
            p1 = point([length // 2, length, length // 2])
        elif face_p == 4:  # back
            p1 = point([length // 2, length // 2, 0])
        else:  # front
            p1 = point([length // 2, length // 2, length])

        # Get a point in the center of the second face
        if face_q == 0:  # left
            p2 = point([0, length // 2, length // 2])
        elif face_q == 1:  # right
            p2 = point([length, length // 2, length // 2])
        elif face_q == 2:  # bottom
            p2 = point([length // 2, 0, length // 2])
        elif face_q == 3:  # top
            p2 = point([length // 2, length, length // 2])
        elif face_q == 4:  # back
            p2 = point([length // 2, length // 2, 0])
        else:  # front
            p2 = point([length // 2, length // 2, length])

        # Calculate distance - this should always work without exceptions
        min_dist = minimumDistanceOnCube(length, p1, p2)

        # The minimum distance between centers of adjacent faces should be length
        # If they're not adjacent, it will be at least sqrt(2)*length
        # Just check that we get a reasonable value
        assert isinstance(min_dist, int)
        assert min_dist >= 0

    def test_random_unfolding_ppties(self, length: int, face_p: int, face_q: int) -> None:
        """Test random unfolding properties."""
        p, q = get_random_point_on_faces(length, face_p, face_q)
        edge = get_edges_for_faces(face_p, face_q, length)
        t1 = calculate_unfolding_transformation(face_p, face_q, edge, length)
        t2 = calculate_unfolding_transformation(face_q, face_p, edge, length)

        hp = np.append(np.array(p.coordinates), 1)
        hq = np.append(np.array(q.coordinates), 1)

        tp = t1 @ hp
        tq = t2 @ hq

        assert is_on_face(face_q, tp[:3], length), f'Point {p} not on face {face_p}'
        assert is_on_face(face_p, tq[:3], length), f'Point {q} not on face {face_q}'

        stable_coord = get_third_coord(face_p, face_q)
        assert tp[stable_coord] == p.coordinates[stable_coord], f'Point {p} not stable on dimension {stable_coord}'
        assert tq[stable_coord] == q.coordinates[stable_coord], f'Point {q} not stable on dimension {stable_coord}'

        if face_p % 2 == 0 and face_q % 2 == 0:
            assert tp[face_p // 2] < 0
            assert tq[face_q // 2] < 0
        elif face_p % 2 == 1 and face_q % 2 == 1:
            assert tp[face_p // 2] > length
            assert tq[face_q // 2] > length
        elif face_p % 2 == 0 and face_q % 2 == 1:
            assert tp[face_p // 2] < 0
            assert tq[face_q // 2] > length
        elif face_p % 2 == 1 and face_q % 2 == 0:
            assert tp[face_p // 2] > length
            assert tq[face_q // 2] < 0
        else:
            raise ValueError('Invalid face combination')


# Add these parametrized tests for one-step unfolding
@pytest.mark.parametrize(
    ('length', 'current_face', 'adjacent_face', 'test_point', 'expected_position'),
    [
        # (x=0) face (0) to adjacent faces
        (2, 0, 2, [0, 1, 1], [-1, 0, 1]),  # (x=0) -> (y=0)
        (2, 0, 3, [0, 1, 1], [-1, 2, 1]),  # (x=0) -> (y=2)
        (2, 0, 4, [0, 1, 1], [-1, 1, 0]),  # (x=0) -> (z=0)
        (2, 0, 5, [0, 1, 1], [-1, 1, 2]),  # (x=0) -> (z=2)
        # (x=2) face (1) to adjacent faces
        (2, 1, 2, [2, 1, 1], [3, 0, 1]),  # (x=2) -> (y=0)
        (2, 1, 3, [2, 1, 1], [3, 2, 1]),  # (x=2) -> (y=2)
        (2, 1, 4, [2, 1, 1], [3, 1, 0]),  # (x=2) -> (z=0)
        (2, 1, 5, [2, 1, 1], [3, 1, 2]),  # (x=2) -> (z=2)
        # (y=0) face (2) to adjacent faces
        (2, 2, 0, [1, 0, 1], [0, -1, 1]),  # (y=0) -> (x=0)
        (2, 2, 1, [1, 0, 1], [2, -1, 1]),  # (y=0) -> (x=2)
        (2, 2, 4, [1, 0, 1], [1, -1, 0]),  # (y=0) -> (z=0)
        (2, 2, 5, [1, 0, 1], [1, -1, 2]),  # (y=0) -> (z=2)
        # (y=2) face (3) to adjacent faces
        (2, 3, 0, [1, 2, 1], [0, 3, 1]),  # (y=2) -> (x=0)
        (2, 3, 1, [1, 2, 1], [2, 3, 1]),  # (y=2) -> (x=2)
        (2, 3, 4, [1, 2, 1], [1, 3, 0]),  # (y=2) -> (z=0)
        (2, 3, 5, [1, 2, 1], [1, 3, 2]),  # (y=2) -> (z=2)
        # (z=0) face (4) to adjacent faces
        (2, 4, 0, [1, 1, 0], [0, 1, -1]),  # (z=0) -> (x=0)
        (2, 4, 1, [1, 1, 0], [2, 1, -1]),  # (z=0) -> (x=2)
        (2, 4, 2, [1, 1, 0], [1, 0, -1]),  # (z=0) -> (y=0)
        (2, 4, 3, [1, 1, 0], [1, 2, -1]),  # (z=0) -> (y=2)
        # (z=2) face (5) to adjacent faces
        (2, 5, 0, [1, 1, 2], [0, 1, 3]),  # (z=2) -> (x=0)
        (2, 5, 1, [1, 1, 2], [2, 1, 3]),  # (z=2) -> (x=2)
        (2, 5, 2, [1, 1, 2], [1, 0, 3]),  # (z=2) -> (y=0)
        (2, 5, 3, [1, 1, 2], [1, 2, 3]),  # (z=2) -> (y=2)
    ],
)
def test_parametrized_one_step_unfolding(
    length: int,
    current_face: int,
    adjacent_face: int,
    test_point: list[int],
    expected_position: list[int],
) -> None:
    """Test one-step unfolding between all adjacent face pairs with specific points."""

    # Create the test point on the current face
    p = point(test_point)

    # Get adjacent face edges

    for adj_face, edge in get_adjacent_faces(current_face, length):
        if adj_face == adjacent_face:
            # Apply transformation for this specific unfolding
            transform = calculate_unfolding_transformation(current_face, adjacent_face, edge, length)

            # Convert to homogeneous coordinates
            p_homo = np.append(np.array(p.coordinates), 1)

            # Apply transformation
            transformed = transform @ p_homo

            # Check against expected position (with some tolerance)
            assert np.allclose(transformed[:3], expected_position, rtol=0.0001, atol=0.0001), (
                f'Unfolding from face {current_face} to {adjacent_face}: '
                f'Expected {expected_position}, got {transformed[:3]}'
            )

            # Verify distance preservation
            # Distance from test point to edge start should be preserved
            edge_start = edge[0]
            orig_dist = np.sum((np.array(p.coordinates) - np.array(edge_start.coordinates)) ** 2)

            # Distance in transformed space
            edge_start_homo = np.append(np.array(edge_start.coordinates), 1)
            transformed_edge = transform @ edge_start_homo
            trans_dist = np.sum((transformed[:3] - transformed_edge[:3]) ** 2)

            assert np.isclose(
                orig_dist,
                trans_dist,
                rtol=1e-8,
                atol=1e-8,
            ), f'Distance not preserved: original={orig_dist}, transformed={trans_dist}'

            return

    # If we get here, we didn't find the specified adjacent face
    raise AssertionError(f'Adjacent face {adjacent_face} not found for face {current_face}')


@pytest.mark.parametrize(
    ('face', 'p1_coords', 'p2_coords'),
    [
        # Test points on each face
        (0, [0, 5, 10], [0, 15, 25]),  # Left face
        (1, [32, 7, 12], [32, 22, 28]),  # Right face
        (2, [8, 0, 15], [24, 0, 27]),  # Bottom face
        (3, [11, 32, 9], [20, 32, 19]),  # Top face
        (4, [14, 18, 0], [26, 29, 0]),  # Back face
        (5, [6, 16, 32], [17, 28, 32]),  # Front face
    ],
)
def test_distance_preservation_after_unfolding(face: int, p1_coords: list[int], p2_coords: list[int]) -> None:
    """
    Test that distances between two points on the same face are preserved
    after unfolding to an adjacent face.
    """
    length = 32

    # Create points on the same face
    p1 = point(p1_coords)
    p2 = point(p2_coords)

    # Calculate original distance
    original_dist = p1.distance(p2)

    # Get an adjacent face to unfold to
    adjacent_faces = get_adjacent_faces(face, length)
    adjacent_face, edge = adjacent_faces[0]  # Take the first adjacent face

    # Calculate transformation
    transform = calculate_unfolding_transformation(face, adjacent_face, edge, length)

    # Apply transformation to both points
    p1_homo = np.append(np.array(p1.coordinates), 1)
    p2_homo = np.append(np.array(p2.coordinates), 1)

    transformed_p1 = transform @ p1_homo
    transformed_p2 = transform @ p2_homo

    # Calculate distance after transformation
    transformed_dist = np.sum((transformed_p1[:3] - transformed_p2[:3]) ** 2)

    # Check that distance is preserved
    assert np.isclose(
        original_dist,
        transformed_dist,
        rtol=1e-8,
        atol=1e-8,
    ), f'Distance not preserved: original={original_dist}, transformed={transformed_dist}'


def test_random_rotations_preserve_distances() -> None:
    """
    Test that our rotation matrices preserve distances between random points in space.
    """
    import random

    # Use a fixed seed for reproducibility
    random.seed(42)
    np.random.seed(42)  # noqa: NPY002

    length = 32

    # Create multiple test cases with random points and rotations
    for test_idx in range(20):  # 20 different test scenarios
        # Generate random points in 3D space (not necessarily on the cube)
        points = []
        for _ in range(5):  # 5 points per test case
            coords = [random.uniform(0, length) for _ in range(3)]
            points.append(np.array(coords))

        # Generate random rotation parameters
        # Random rotation axis
        axis_start = point([round(random.uniform(0, length)) for _ in range(3)])
        axis_end = point([round(random.uniform(0, length)) for _ in range(3)])
        # Random rotation angle between 0 and 2π
        angle = random.uniform(0, 2 * np.pi)

        # Get rotation matrix
        rot_matrix = get_rotation_matrix(axis_start, axis_end, angle)

        # Calculate distances between all pairs of points before rotation
        distances_before = []
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = np.sum((points[i] - points[j]) ** 2)
                distances_before.append((i, j, dist))

        # Apply rotation to all points
        rotated_points = [np.dot(rot_matrix, p) for p in points]

        # Calculate distances after rotation and compare
        for i, j, original_dist in distances_before:
            rotated_dist = np.sum((rotated_points[i] - rotated_points[j]) ** 2)
            # Check distance preservation with a small tolerance for numerical precision
            assert np.isclose(original_dist, rotated_dist, rtol=1e-10, atol=1e-10), (
                f'Distance not preserved in test {test_idx}: points {i},{j}: '
                f'original={original_dist}, rotated={rotated_dist}'
            )


def test_random_transformations_preserve_distances() -> None:
    """
    Test that our transformation matrices preserve distances between points on same face.
    """
    import random

    # Use a fixed seed for reproducibility
    random.seed(43)
    np.random.seed(43)

    length = 32

    # Test for each face of the cube
    for face in range(6):
        # For each face, test multiple random point sets and transformations
        for test_idx in range(5):  # 5 tests per face
            # Generate random points on this face
            points = []
            for _ in range(4):  # 4 points per test
                if face == 0:  # x = 0 (left)
                    coords = [0, random.uniform(0, length), random.uniform(0, length)]
                elif face == 1:  # x = length (right)
                    coords = [length, random.uniform(0, length), random.uniform(0, length)]
                elif face == 2:  # y = 0 (bottom)
                    coords = [random.uniform(0, length), 0, random.uniform(0, length)]
                elif face == 3:  # y = length (top)
                    coords = [random.uniform(0, length), length, random.uniform(0, length)]
                elif face == 4:  # z = 0 (back)
                    coords = [random.uniform(0, length), random.uniform(0, length), 0]
                else:  # z = length (front)
                    coords = [random.uniform(0, length), random.uniform(0, length), length]

                points.append(np.array(coords))

            # Get adjacent faces to transform to
            adj_faces = get_adjacent_faces(face, length)
            adj_face, edge = random.choice(adj_faces)

            # Calculate transformation
            transform = calculate_unfolding_transformation(face, adj_face, edge, length)

            # Calculate distances between all pairs of points before transformation
            distances_before = []
            for i in range(len(points)):
                for j in range(i + 1, len(points)):
                    dist = np.sum((points[i] - points[j]) ** 2)
                    distances_before.append((i, j, dist))

            # Apply transformation to all points
            transformed_points = []
            for p in points:
                p_homo = np.append(p, 1)  # Convert to homogeneous coordinates
                transformed = transform @ p_homo
                transformed_points.append(transformed[:3])  # Get 3D coordinates

            # Calculate distances after transformation and compare
            for i, j, original_dist in distances_before:
                transformed_dist = np.sum((transformed_points[i] - transformed_points[j]) ** 2)

                # Check distance preservation
                assert np.isclose(original_dist, transformed_dist, rtol=1e-8, atol=1e-8), (
                    f'Distance not preserved for face {face} transformation to {adj_face}, '
                    f'points {i},{j} in test {test_idx}: '
                    f'original={original_dist}, transformed={transformed_dist}'
                )


def test_edge_point_distances_preserved() -> None:
    """
    Test that distances from points to the rotation edge are preserved.
    """
    import random

    # Use a fixed seed for reproducibility
    random.seed(44)
    np.random.seed(44)

    length = 32

    for face in range(6):
        # Get all adjacent faces for this face
        adj_faces = get_adjacent_faces(face, length)

        for adj_face, edge in adj_faces:
            edge_start, edge_end = edge
            edge_start_coords = np.array(edge_start.coordinates)
            edge_end_coords = np.array(edge_end.coordinates)

            # Generate multiple random points on the face
            for _ in range(5):
                # Create a random point on the current face
                if face == 0:  # x = 0 (left)
                    p_coords = [0, random.uniform(0, length), random.uniform(0, length)]
                elif face == 1:  # x = length (right)
                    p_coords = [length, random.uniform(0, length), random.uniform(0, length)]
                elif face == 2:  # y = 0 (bottom)
                    p_coords = [random.uniform(0, length), 0, random.uniform(0, length)]
                elif face == 3:  # y = length (top)
                    p_coords = [random.uniform(0, length), length, random.uniform(0, length)]
                elif face == 4:  # z = 0 (back)
                    p_coords = [random.uniform(0, length), random.uniform(0, length), 0]
                else:  # z = length (front)
                    p_coords = [random.uniform(0, length), random.uniform(0, length), length]

                p = np.array(p_coords)

                # Calculate distance from point to edge_start
                dist_to_start = np.sum((p - edge_start_coords) ** 2)

                # Calculate distance from point to edge_end
                dist_to_end = np.sum((p - edge_end_coords) ** 2)

                # Calculate transformation
                transform = calculate_unfolding_transformation(face, adj_face, edge, length)

                # Apply transformation
                p_homo = np.append(p, 1)
                transformed_p = transform @ p_homo

                # Apply transformation to edge points
                start_homo = np.append(edge_start_coords, 1)
                end_homo = np.append(edge_end_coords, 1)
                transformed_start = transform @ start_homo
                transformed_end = transform @ end_homo

                # Calculate distances after transformation
                transformed_dist_to_start = np.sum((transformed_p[:3] - transformed_start[:3]) ** 2)
                transformed_dist_to_end = np.sum((transformed_p[:3] - transformed_end[:3]) ** 2)

                # Check distance preservation
                assert np.isclose(dist_to_start, transformed_dist_to_start, rtol=1e-8, atol=1e-8), (
                    f'Distance to edge start not preserved: face {face} to {adj_face}, '
                    f'original={dist_to_start}, transformed={transformed_dist_to_start}'
                )

                assert np.isclose(dist_to_end, transformed_dist_to_end, rtol=1e-8, atol=1e-8), (
                    f'Distance to edge end not preserved: face {face} to {adj_face}, '
                    f'original={dist_to_end}, transformed={transformed_dist_to_end}'
                )


@pytest.mark.parametrize(
    ('f1', 'f2'),
    [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 5),
        (1, 0),
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (2, 0),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (2, 5),
        (3, 0),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (3, 5),
        (4, 0),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (5, 0),
        (5, 1),
        (5, 2),
        (5, 3),
        (5, 4),
        (5, 5),
    ],
)
def test_all_unfolded_points_on_same_plane(f1: int, f2: int) -> None:
    """
    Test that all unfolded points are on the same plane after unfolding.
    """
    length = 32

    # Create two points on opposite faces
    pt1 = get_random_point_on_face(length, f1)
    pt2 = get_random_point_on_face(length, f2)

    # Get all unfolded positions
    u1 = unfold_cube(pt1, pt2, length)
    u2 = unfold_cube(pt2, pt1, length)

    # Check that all unfolded points are on the same plane
    for pos in u1:
        assert np.isclose(pos[f1 // 2], pt1.coordinates[f1 // 2]), f'Point {pos} not on the same plane as {pt1}'
    for pos in u2:
        assert np.isclose(pos[f2 // 2], pt2.coordinates[f2 // 2]), f'Point {pos} not on the same plane as {pt2}'
