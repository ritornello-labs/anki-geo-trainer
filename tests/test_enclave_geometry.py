"""Map topology regressions: preserve enclave holes through projection/export."""
import importlib.util
from pathlib import Path

from shapely.geometry import Point, Polygon

spec = importlib.util.spec_from_file_location('build_bundle', Path(__file__).parents[1] / 'scripts/build_bundle.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_projection_and_export_preserve_holes():
    source = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                     [[(3, 3), (7, 3), (7, 7), (3, 7)]])
    projected = builder.project_geom(source, lambda x, y: (x * 2, 20 - y * 2))
    assert len(projected.interiors) == 1
    assert not projected.contains(Point(10, 10))
    rings = builder.rings_of(projected)
    restored = Polygon(rings[0], rings[1:])
    assert restored.equals(projected)
    assert all(restored.contains(Point(p)) for p in builder.sample_points(projected, 'host'))


def test_antimeridian_unwrap_preserves_holes():
    source = Polygon([(-170, 0), (-160, 0), (-160, 10), (-170, 10)],
                     [[(-167, 3), (-163, 3), (-163, 7), (-167, 7)]])
    unwrapped = builder._unwrap_antimeridian(source)
    assert len(unwrapped.interiors) == 1
    assert not unwrapped.contains(Point(195, 5))
