"""Tests for classification analyzer."""

import pytest
from unittest.mock import MagicMock

from app.services.classification_analyzer import ClassificationAnalyzer


class TestClassificationAnalyzer:
    """Test cases for ClassificationAnalyzer."""

    def test_extract_materials_copper_vietnamese(self):
        """Test extraction of copper material from Vietnamese text."""
        analyzer = ClassificationAnalyzer()
        materials = analyzer.extract_materials("thanh treo khăn bằng đồng mạ chrome")

        material_names = [m[0] for m in materials]
        assert "copper" in material_names
        assert "chrome-plated" in material_names

    def test_extract_materials_copper_english(self):
        """Test extraction of copper material from English text."""
        analyzer = ClassificationAnalyzer()
        materials = analyzer.extract_materials("copper towel rack, chrome plated")

        material_names = [m[0] for m in materials]
        assert "copper" in material_names
        assert "chrome-plated" in material_names

    def test_extract_materials_steel(self):
        """Test extraction of steel material."""
        analyzer = ClassificationAnalyzer()
        materials = analyzer.extract_materials("stainless steel kitchen rack")

        material_names = [m[0] for m in materials]
        assert "stainless steel" in material_names

    def test_extract_materials_plastic(self):
        """Test extraction of plastic material."""
        analyzer = ClassificationAnalyzer()
        materials = analyzer.extract_materials("đồ nhựa gia dụng")

        material_names = [m[0] for m in materials]
        assert "plastic" in material_names

    def test_extract_materials_no_match(self):
        """Test extraction with no recognizable materials."""
        analyzer = ClassificationAnalyzer()
        materials = analyzer.extract_materials("some random text")

        assert len(materials) == 0

    def test_extract_functions_bathroom(self):
        """Test extraction of bathroom function."""
        analyzer = ClassificationAnalyzer()
        functions = analyzer.extract_functions("thanh treo khăn nhà vệ sinh")

        function_names = [f[0] for f in functions]
        assert "bathroom" in function_names
        assert "towel rack" in function_names

    def test_extract_functions_kitchen(self):
        """Test extraction of kitchen function."""
        analyzer = ClassificationAnalyzer()
        functions = analyzer.extract_functions("đồ dùng nhà bếp")

        function_names = [f[0] for f in functions]
        assert "kitchen" in function_names

    def test_extract_functions_blender(self):
        """Test extraction of blender function."""
        analyzer = ClassificationAnalyzer()
        functions = analyzer.extract_functions("máy xay sinh tố")

        function_names = [f[0] for f in functions]
        assert "blender/grinder" in function_names or "blender" in function_names

    def test_generate_material_reasoning_with_chrome(self):
        """Test material reasoning mentions chrome plating correctly."""
        analyzer = ClassificationAnalyzer()

        mock_hs_code = MagicMock()
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_hs_code.description_en = "Sanitary ware"
        mock_hs_code.subheading = None

        query = "thanh treo khăn bằng đồng mạ chrome"
        reasoning = analyzer.generate_material_reasoning(query, mock_hs_code)

        assert "đồng" in reasoning.lower()
        assert "chrome" in reasoning.lower()
        # Should mention classification despite chrome plating
        assert "phân loại" in reasoning.lower()

    def test_generate_function_reasoning(self):
        """Test function reasoning includes heading info."""
        analyzer = ClassificationAnalyzer()

        mock_hs_code = MagicMock()
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_hs_code.description_en = "Sanitary ware"
        mock_hs_code.subheading = None

        query = "thanh treo khăn nhà vệ sinh"
        reasoning = analyzer.generate_function_reasoning(query, mock_hs_code)

        assert "7418.20.00" in reasoning
        assert "Đồ trang bị trong nhà vệ sinh" in reasoning

    def test_generate_practical_notes_high_duty(self):
        """Test practical notes for high duty rate products."""
        analyzer = ClassificationAnalyzer()

        mock_hs_code = MagicMock()
        mock_hs_code.duty_rate = 30.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.fta_rates = []

        notes = analyzer.generate_practical_notes(mock_hs_code, is_new_product=False)

        # Should mention high duty rate
        assert any("30%" in note or "khá cao" in note for note in notes)

    def test_generate_practical_notes_new_product(self):
        """Test practical notes include new product info."""
        analyzer = ClassificationAnalyzer()

        mock_hs_code = MagicMock()
        mock_hs_code.duty_rate = 10.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.fta_rates = []

        notes = analyzer.generate_practical_notes(mock_hs_code, is_new_product=True)

        # Should mention new product
        assert any("hàng mới" in note.lower() or "100%" in note for note in notes)

    def test_generate_practical_notes_with_fta(self):
        """Test practical notes mention FTA rates when available."""
        analyzer = ClassificationAnalyzer()

        mock_fta_rate = MagicMock()
        mock_fta_rate.preferential_rate = 5.0

        mock_hs_code = MagicMock()
        mock_hs_code.duty_rate = 20.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.fta_rates = [mock_fta_rate]

        notes = analyzer.generate_practical_notes(mock_hs_code, is_new_product=False)

        # Should mention FTA
        assert any("fta" in note.lower() for note in notes)

    def test_analyze_returns_complete_analysis(self):
        """Test analyze returns all components."""
        analyzer = ClassificationAnalyzer()

        mock_hs_code = MagicMock()
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Đồ trang bị trong nhà vệ sinh"
        mock_hs_code.description_en = "Sanitary ware"
        mock_hs_code.duty_rate = 30.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.fta_rates = []
        mock_hs_code.subheading = None

        query = "thanh treo khăn bằng đồng mạ chrome, hàng mới 100%"
        analysis = analyzer.analyze(query, mock_hs_code)

        assert analysis.material is not None
        assert analysis.function is not None
        assert isinstance(analysis.practical_notes, list)
        assert len(analysis.practical_notes) > 0

    def test_analyze_detects_new_product(self):
        """Test analyze detects new product from query."""
        analyzer = ClassificationAnalyzer()

        mock_hs_code = MagicMock()
        mock_hs_code.code = "74182000"
        mock_hs_code.description_vn = "Test"
        mock_hs_code.description_en = "Test"
        mock_hs_code.duty_rate = 10.0
        mock_hs_code.vat_rate = 10.0
        mock_hs_code.fta_rates = []
        mock_hs_code.subheading = None

        # Test Vietnamese
        analysis1 = analyzer.analyze("sản phẩm hàng mới", mock_hs_code)
        assert any("hàng mới" in note.lower() for note in analysis1.practical_notes)

        # Test "100%"
        analysis2 = analyzer.analyze("sản phẩm mới 100%", mock_hs_code)
        assert any("hàng mới" in note.lower() or "100%" in note for note in analysis2.practical_notes)
