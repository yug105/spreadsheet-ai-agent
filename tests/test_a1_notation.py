"""Unit tests for the A1 notation handler (pure logic, no external services)."""

import pytest

from sheetsai.a1_notation import (
    A1NotationHandler,
    RangeReference,
    ReferenceType,
    RangeAnalyzer,
)


@pytest.mark.parametrize(
    "row,col,expected",
    [
        (0, 0, "A1"),
        (0, 25, "Z1"),
        (0, 26, "AA1"),
        (0, 27, "AB1"),
        (9, 1, "B10"),
        (99, 701, "ZZ100"),
    ],
)
def test_to_a1(row, col, expected):
    assert A1NotationHandler.to_a1(row, col) == expected


@pytest.mark.parametrize(
    "a1,expected",
    [
        ("A1", (0, 0)),
        ("Z1", (0, 25)),
        ("AA1", (0, 26)),
        ("B10", (9, 1)),
        ("$A$1", (0, 0)),
    ],
)
def test_from_a1(a1, expected):
    assert A1NotationHandler.from_a1(a1) == expected


def test_to_a1_rejects_negative():
    with pytest.raises(ValueError):
        A1NotationHandler.to_a1(-1, 0)


def test_from_a1_rejects_garbage():
    with pytest.raises(ValueError):
        A1NotationHandler.from_a1("not-a-cell")


def test_roundtrip():
    handler = A1NotationHandler()
    for row, col in [(0, 0), (5, 12), (99, 3), (1000, 700)]:
        a1 = handler.to_a1(row, col)
        assert handler.from_a1(a1) == (row, col)


def test_parse_cell_reference():
    handler = A1NotationHandler()
    ref = handler.parse_reference("C5")
    assert ref.reference_type == ReferenceType.CELL
    assert (ref.row, ref.col) == (4, 2)


def test_parse_absolute_reference():
    handler = A1NotationHandler()
    ref = handler.parse_reference("$C$5")
    assert ref.is_absolute_col and ref.is_absolute_row
    assert (ref.row, ref.col) == (4, 2)


def test_parse_and_expand_range():
    handler = A1NotationHandler()
    rng = handler.parse_reference("A1:B2")
    assert isinstance(rng, RangeReference)
    cells = rng.get_all_cells()
    assert len(cells) == 4
    assert {c.a1_notation for c in cells} == {"A1", "B1", "A2", "B2"}


def test_range_contains_and_overlaps():
    handler = A1NotationHandler()
    a = handler.parse_reference("A1:C3")
    b = handler.parse_reference("B2:D4")
    inside = handler.parse_reference("B2")
    assert a.contains_cell(inside)
    assert a.overlaps_with(b)


def test_offset_reference():
    handler = A1NotationHandler()
    ref = handler.parse_reference("A1")
    moved = handler.offset_reference(ref, row_offset=2, col_offset=3)
    assert moved.a1_notation == "D3"


def test_offset_clamps_at_origin():
    handler = A1NotationHandler()
    ref = handler.parse_reference("A1")
    moved = handler.offset_reference(ref, row_offset=-5, col_offset=-5)
    assert (moved.row, moved.col) == (0, 0)


def test_is_valid_a1_notation():
    handler = A1NotationHandler()
    assert handler.is_valid_a1_notation("A1")
    assert handler.is_valid_a1_notation("A1:B10")
    assert not handler.is_valid_a1_notation("!!!")


def test_range_analyzer_merges_overlapping():
    handler = A1NotationHandler()
    analyzer = RangeAnalyzer()
    ranges = [handler.parse_reference("A1:B2"), handler.parse_reference("B2:C3")]
    merged = analyzer.merge_ranges(ranges)
    assert len(merged) == 1
