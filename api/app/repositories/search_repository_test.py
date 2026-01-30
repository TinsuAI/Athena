"""Tests for search repository."""

import pytest

from app.repositories.search_repository import SearchRepository


class TestSearchRepository:
    """Test cases for SearchRepository."""

    def test_is_hs_code_pattern_8_digits(self):
        """Test detection of 8-digit HS code."""
        assert SearchRepository.is_hs_code_pattern("74182000") is True

    def test_is_hs_code_pattern_with_periods(self):
        """Test detection of HS code with periods."""
        assert SearchRepository.is_hs_code_pattern("7418.20.00") is True

    def test_is_hs_code_pattern_with_spaces(self):
        """Test detection of HS code with spaces."""
        assert SearchRepository.is_hs_code_pattern("7418 20 00") is True

    def test_is_hs_code_pattern_short_code(self):
        """Test rejection of short code."""
        assert SearchRepository.is_hs_code_pattern("741820") is False

    def test_is_hs_code_pattern_long_code(self):
        """Test rejection of long code."""
        assert SearchRepository.is_hs_code_pattern("7418200000") is False

    def test_is_hs_code_pattern_with_letters(self):
        """Test rejection of code with letters."""
        assert SearchRepository.is_hs_code_pattern("7418A000") is False

    def test_is_hs_code_pattern_text_query(self):
        """Test rejection of text query."""
        assert SearchRepository.is_hs_code_pattern("máy xay sinh tố") is False

    def test_normalize_hs_code_removes_periods(self):
        """Test normalization removes periods."""
        assert SearchRepository.normalize_hs_code("7418.20.00") == "74182000"

    def test_normalize_hs_code_removes_spaces(self):
        """Test normalization removes spaces."""
        assert SearchRepository.normalize_hs_code("7418 20 00") == "74182000"

    def test_normalize_hs_code_already_normalized(self):
        """Test normalization of already normalized code."""
        assert SearchRepository.normalize_hs_code("74182000") == "74182000"

    def test_normalize_hs_code_mixed_separators(self):
        """Test normalization with mixed separators."""
        assert SearchRepository.normalize_hs_code("74 18.20.00") == "74182000"
