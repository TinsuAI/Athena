"""Classification analyzer for generating customs classification reasoning."""

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.models.hs_code import HSCode

if TYPE_CHECKING:
    from app.services.llm_reasoning_service import LLMReasoningService

logger = logging.getLogger(__name__)


@dataclass
class ClassificationAnalysis:
    """Analysis result with classification reasoning."""

    material: str
    function: str
    practical_notes: list[str]


# Material keywords mapping (Vietnamese and English)
MATERIAL_KEYWORDS = {
    "đồng": ("copper", "đồng (Chương 74)"),
    "copper": ("copper", "đồng (Chương 74)"),
    "brass": ("copper/brass", "đồng thau - hợp kim đồng (Chương 74)"),
    "đồng thau": ("copper/brass", "đồng thau - hợp kim đồng (Chương 74)"),
    "thép": ("steel", "thép (Chương 72-73)"),
    "steel": ("steel", "thép (Chương 72-73)"),
    "sắt": ("iron", "sắt (Chương 72-73)"),
    "iron": ("iron", "sắt (Chương 72-73)"),
    "nhôm": ("aluminum", "nhôm (Chương 76)"),
    "aluminum": ("aluminum", "nhôm (Chương 76)"),
    "aluminium": ("aluminum", "nhôm (Chương 76)"),
    "nhựa": ("plastic", "nhựa (Chương 39)"),
    "plastic": ("plastic", "nhựa (Chương 39)"),
    "gỗ": ("wood", "gỗ (Chương 44)"),
    "wood": ("wood", "gỗ (Chương 44)"),
    "wooden": ("wood", "gỗ (Chương 44)"),
    "thủy tinh": ("glass", "thủy tinh (Chương 70)"),
    "glass": ("glass", "thủy tinh (Chương 70)"),
    "vải": ("textile", "vải dệt (Phần XI)"),
    "textile": ("textile", "vải dệt (Phần XI)"),
    "fabric": ("textile", "vải dệt (Phần XI)"),
    "da": ("leather", "da (Chương 41-42)"),
    "leather": ("leather", "da (Chương 41-42)"),
    "cao su": ("rubber", "cao su (Chương 40)"),
    "rubber": ("rubber", "cao su (Chương 40)"),
    "gốm": ("ceramic", "gốm sứ (Chương 69)"),
    "ceramic": ("ceramic", "gốm sứ (Chương 69)"),
    "sứ": ("porcelain", "sứ (Chương 69)"),
    "porcelain": ("porcelain", "sứ (Chương 69)"),
    "chrome": ("chrome-plated", "mạ chrome"),
    "mạ chrome": ("chrome-plated", "mạ chrome"),
    "inox": ("stainless steel", "thép không gỉ (Chương 72-73)"),
    "stainless": ("stainless steel", "thép không gỉ (Chương 72-73)"),
}

# Function/purpose keywords mapping
FUNCTION_KEYWORDS = {
    "nhà vệ sinh": ("bathroom", "đồ trang bị trong nhà vệ sinh"),
    "bathroom": ("bathroom", "đồ trang bị trong nhà vệ sinh"),
    "phòng tắm": ("bathroom", "đồ trang bị trong nhà vệ sinh"),
    "nhà bếp": ("kitchen", "đồ nhà bếp"),
    "kitchen": ("kitchen", "đồ nhà bếp"),
    "bếp": ("kitchen", "đồ nhà bếp"),
    "công nghiệp": ("industrial", "dùng trong công nghiệp"),
    "industrial": ("industrial", "dùng trong công nghiệp"),
    "máy": ("machine", "máy móc"),
    "machine": ("machine", "máy móc"),
    "điện": ("electrical", "thiết bị điện"),
    "electrical": ("electrical", "thiết bị điện"),
    "electric": ("electrical", "thiết bị điện"),
    "gia dụng": ("household", "đồ gia dụng"),
    "household": ("household", "đồ gia dụng"),
    "home": ("household", "đồ gia dụng"),
    "treo khăn": ("towel rack", "thanh treo khăn - đồ trang bị nhà vệ sinh"),
    "towel rack": ("towel rack", "thanh treo khăn - đồ trang bị nhà vệ sinh"),
    "towel bar": ("towel rack", "thanh treo khăn - đồ trang bị nhà vệ sinh"),
    "xay": ("blender/grinder", "máy xay"),
    "blender": ("blender/grinder", "máy xay"),
    "mixer": ("blender/grinder", "máy xay"),
    "sinh tố": ("blender", "máy xay sinh tố"),
    "smoothie": ("blender", "máy xay sinh tố"),
}


class ClassificationAnalyzer:
    """Analyzer for generating customs classification reasoning.

    Supports two modes:
    1. LLM-based reasoning (primary): Uses LLM for coherent, accurate explanations
    2. Rule-based reasoning (fallback): Keyword-based extraction when LLM unavailable

    The LLM mode produces better results for complex cases where function
    takes precedence over material (e.g., brass faucets classified in Ch. 84).
    """

    def __init__(self, llm_service: "LLMReasoningService | None" = None):
        """Initialize analyzer.

        Args:
            llm_service: Optional LLM reasoning service. If provided, LLM-based
                reasoning will be used with rule-based fallback on failure.
        """
        self.llm_service = llm_service

    def extract_materials(self, text: str) -> list[tuple[str, str]]:
        """Extract material information from text.

        Args:
            text: Query or description text

        Returns:
            List of (english_name, vietnamese_description) tuples
        """
        text_lower = text.lower()
        found_materials = []

        for keyword, (eng, vn_desc) in MATERIAL_KEYWORDS.items():
            if keyword.lower() in text_lower:
                if (eng, vn_desc) not in found_materials:
                    found_materials.append((eng, vn_desc))

        return found_materials

    def extract_functions(self, text: str) -> list[tuple[str, str]]:
        """Extract function/purpose information from text.

        Args:
            text: Query or description text

        Returns:
            List of (english_name, vietnamese_description) tuples
        """
        text_lower = text.lower()
        found_functions = []

        for keyword, (eng, vn_desc) in FUNCTION_KEYWORDS.items():
            if keyword.lower() in text_lower:
                if (eng, vn_desc) not in found_functions:
                    found_functions.append((eng, vn_desc))

        return found_functions

    def _get_chapter_info(self, hs_code: HSCode) -> str:
        """Get chapter information from HS code hierarchy.

        Args:
            hs_code: The HS code model with relationships

        Returns:
            Chapter description or empty string
        """
        try:
            if hs_code.subheading and hs_code.subheading.heading:
                heading = hs_code.subheading.heading
                if heading.chapter:
                    return f"Chương {heading.chapter.code}: {heading.chapter.name_vn}"
        except Exception:
            pass

        # Fallback: extract chapter from code
        chapter_code = hs_code.code[:2]
        return f"Chương {chapter_code}"

    def _get_heading_info(self, hs_code: HSCode) -> str:
        """Get heading information from HS code hierarchy.

        Args:
            hs_code: The HS code model

        Returns:
            Heading description or empty string
        """
        try:
            if hs_code.subheading and hs_code.subheading.heading:
                heading = hs_code.subheading.heading
                return f"Nhóm {heading.code}: {heading.name_vn}"
        except Exception:
            pass

        # Fallback: extract heading from code
        heading_code = hs_code.code[:4]
        formatted = f"{heading_code[:2]}.{heading_code[2:]}"
        return f"Nhóm {formatted}"

    def generate_material_reasoning(
        self,
        query: str,
        hs_code: HSCode,
    ) -> str:
        """Generate material classification reasoning.

        Args:
            query: The search query
            hs_code: The matched HS code

        Returns:
            Vietnamese reasoning text explaining material classification
        """
        materials = self.extract_materials(query)
        materials_from_desc = self.extract_materials(
            hs_code.description_vn + " " + hs_code.description_en
        )

        all_materials = list(set(materials + materials_from_desc))

        if not all_materials:
            return f"Sản phẩm được phân loại vào {self._get_chapter_info(hs_code)} dựa trên thành phần cấu tạo chính."

        # Build reasoning
        material_desc = ", ".join([m[1] for m in all_materials])
        chapter_info = self._get_chapter_info(hs_code)

        reasoning = f"Sản phẩm được làm từ {material_desc}. "

        # Add chrome plating note if applicable
        if any("chrome" in m[0].lower() for m in all_materials):
            # Find base material
            base_materials = [m for m in all_materials if "chrome" not in m[0].lower()]
            if base_materials:
                reasoning += f"Dù có mạ chrome, sản phẩm vẫn được phân loại theo kim loại cơ bản là {base_materials[0][1]}. "

        reasoning += f"Thuộc {chapter_info}."

        return reasoning

    def generate_function_reasoning(
        self,
        query: str,
        hs_code: HSCode,
    ) -> str:
        """Generate function/purpose classification reasoning.

        Args:
            query: The search query
            hs_code: The matched HS code

        Returns:
            Vietnamese reasoning text explaining functional classification
        """
        functions = self.extract_functions(query)
        functions_from_desc = self.extract_functions(
            hs_code.description_vn + " " + hs_code.description_en
        )

        all_functions = list(set(functions + functions_from_desc))
        heading_info = self._get_heading_info(hs_code)

        if not all_functions:
            return f"Sản phẩm được phân loại vào {heading_info} dựa trên công dụng và đặc điểm kỹ thuật."

        # Build reasoning
        function_desc = ", ".join([f[1] for f in all_functions])

        reasoning = f"Sản phẩm thuộc loại {function_desc}. "
        reasoning += f"Theo Danh mục thuế, {heading_info}."

        # Add specific subheading info
        formatted_code = f"{hs_code.code[:4]}.{hs_code.code[4:6]}.{hs_code.code[6:]}"
        reasoning += f" Mã {formatted_code} được dành cho \"{hs_code.description_vn}\"."

        return reasoning

    def generate_practical_notes(
        self,
        hs_code: HSCode,
        is_new_product: bool = False,
    ) -> list[str]:
        """Generate practical import notes.

        Args:
            hs_code: The matched HS code
            is_new_product: Whether the product is new (100% new)

        Returns:
            List of practical notes in Vietnamese
        """
        notes = []

        # New product note
        if is_new_product:
            notes.append(
                "Hàng mới 100%: Sản phẩm là hàng mới nên đủ điều kiện nhập khẩu "
                "thông thường, không cần giấy phép đặc biệt (trừ khi thuộc danh mục hạn chế)."
            )

        # Duty rate note
        duty_rate = float(hs_code.duty_rate)
        if duty_rate >= 20:
            notes.append(
                f"Chính sách thuế: Mức thuế nhập khẩu MFN cho mã này khá cao ({duty_rate}%). "
                "Nên kiểm tra các hiệp định FTA để hưởng ưu đãi thuế quan."
            )
        elif duty_rate > 0:
            notes.append(
                f"Thuế nhập khẩu MFN: {duty_rate}%. "
                "Có thể áp dụng thuế suất ưu đãi từ các FTA nếu đủ điều kiện."
            )
        else:
            notes.append(
                "Thuế nhập khẩu MFN: 0%. Sản phẩm được miễn thuế nhập khẩu."
            )

        # VAT note
        vat_rate = float(hs_code.vat_rate)
        notes.append(f"Thuế GTGT: {vat_rate}%.")

        # FTA optimization hint
        # Check if fta_rates is loaded and has items
        try:
            if hs_code.fta_rates and len(hs_code.fta_rates) > 0:
                fta_count = len(hs_code.fta_rates)
                # Find the best FTA rate
                best_rate = min(float(r.preferential_rate) for r in hs_code.fta_rates)
                notes.append(
                    f"Ưu đãi FTA: Có {fta_count} hiệp định áp dụng, thuế suất ưu đãi tốt nhất là {best_rate}%. "
                    "Kiểm tra C/O và quy tắc xuất xứ để hưởng ưu đãi."
                )
        except Exception:
            # FTA rates not loaded or error accessing them, skip this note
            pass

        return notes

    def _rule_based_analyze(
        self,
        query: str,
        hs_code: HSCode,
        is_new: bool,
    ) -> ClassificationAnalysis:
        """Generate analysis using rule-based keyword matching.

        This is the fallback method when LLM is unavailable.

        Args:
            query: The search query
            hs_code: The matched HS code
            is_new: Whether the product is new

        Returns:
            ClassificationAnalysis with material, function, and practical notes
        """
        return ClassificationAnalysis(
            material=self.generate_material_reasoning(query, hs_code),
            function=self.generate_function_reasoning(query, hs_code),
            practical_notes=self.generate_practical_notes(hs_code, is_new),
        )

    async def analyze_async(
        self,
        query: str,
        hs_code: HSCode,
    ) -> ClassificationAnalysis:
        """Generate full classification analysis using LLM with fallback.

        This is the primary async method that attempts LLM-based reasoning
        first, falling back to rule-based analysis on failure.

        Args:
            query: The search query
            hs_code: The matched HS code

        Returns:
            ClassificationAnalysis with material, function, and practical notes
        """
        # Check if query mentions "new" or "100%"
        is_new = bool(
            re.search(r"(hàng\s*mới|100\s*%|new|brand\s*new)", query, re.IGNORECASE)
        )

        # Generate practical notes (always rule-based)
        practical_notes = self.generate_practical_notes(hs_code, is_new)

        # Try LLM-based reasoning if service is available
        if self.llm_service:
            try:
                chapter_info = self._get_chapter_info(hs_code)
                heading_info = self._get_heading_info(hs_code)
                formatted_code = f"{hs_code.code[:4]}.{hs_code.code[4:6]}.{hs_code.code[6:]}"

                reasoning = await self.llm_service.generate_reasoning(
                    query=query,
                    hs_code=formatted_code,
                    chapter_info=chapter_info,
                    heading_info=heading_info,
                    description=hs_code.description_vn,
                )

                return ClassificationAnalysis(
                    material=reasoning.material,
                    function=reasoning.function,
                    practical_notes=practical_notes,
                )

            except Exception as e:
                logger.warning(f"LLM reasoning failed, falling back to rule-based: {e}")
                # Fall through to rule-based analysis

        # Fallback to rule-based analysis
        return self._rule_based_analyze(query, hs_code, is_new)

    def analyze(
        self,
        query: str,
        hs_code: HSCode,
    ) -> ClassificationAnalysis:
        """Generate full classification analysis (sync version).

        This is the synchronous method for backward compatibility.
        It only uses rule-based analysis.

        Args:
            query: The search query
            hs_code: The matched HS code

        Returns:
            ClassificationAnalysis with material, function, and practical notes
        """
        # Check if query mentions "new" or "100%"
        is_new = bool(
            re.search(r"(hàng\s*mới|100\s*%|new|brand\s*new)", query, re.IGNORECASE)
        )

        return self._rule_based_analyze(query, hs_code, is_new)
