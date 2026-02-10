query: Bộ trộn dùng để điều chỉnh nước nóng lạnh hai đường nước cho bộ vòi sen tắm WE00202, kích thước 147x128x110mm, bằng đồng, nhà sản xuất Carlo Nobili S.p.a, hàng mới 100%

athena-api  | INFO:     172.21.0.1:36496 - "OPTIONS /api/search HTTP/1.1" 200 OK
athena-api  | [Enhance] Cache miss, calling API
athena-api  | [Enhance] Request to model=openai/gpt-5.2
athena-api  | [Enhance] Response status: 200
athena-api  | [Enhance] Content: {
athena-api  |   "enhanced_query": "Bộ trộn/mixer van trộn nước nóng lạnh (2 đường nước) dùng để điều chỉnh nhiệt độ và lưu lượng cho bộ vòi sen tắm mã WE00202; kích thước 147x128x110mm; vật liệu chính bằng đồng (
athena-api  | [Rerank] Cache miss, calling API
athena-api  | [Rerank] Request to model=openai/gpt-5.2
athena-api  | [Rerank] Response status: 200
athena-api  | [Rerank] Response data: {"id": "gen-1770101108-3TeqKHSUzwWQIWcreZhQ", "provider": "OpenAI", "model": "openai/gpt-5.2", "object": "chat.completion", "created": 1770101108, "choices": [{"logprobs": null, "finish_reason": "stop", "native_finish_reason": "completed", "index": 0, "message": {"role": "assistant", "content": "{\n  \"best_code\": \"8481.80.98\",\n  \"reasoning\": \"Theo GRI 1, hàng là “bộ trộn” điều chỉnh/pha trộn nước nóng–lạnh cho vòi sen, có chức năng như vòi/van điều khiển dòng chảy và trộn nước trên đường ống → thuộc nhóm 8481 (vòi, van và các thiết bị tương tự dùng cho đường ống). Không phải van một chiều (8481.30), không phải van an toàn/giảm áp (8481.40) và cũng không phải “bộ phận/thân” rời (8481.90) vì mô tả là bộ trộn hoàn chỉnh. Theo GRI 6, trong phân nhóm 8481.80 (loại khác), mặt hàng bằng đ
athena-api  | [Rerank] Content: {
athena-api  |   "best_code": "8481.80.98",
athena-api  |   "reasoning": "Theo GRI 1, hàng là “bộ trộn” điều chỉnh/pha trộn nước nóng–lạnh cho vòi sen, có chức năng như vòi/van điều khiển dòng chảy và trộn nước trên đường ống →
athena-api  | [LLM] Cache miss, calling API for model=openai/gpt-5.2
athena-api  | [LLM] Request to model=openai/gpt-5.2
athena-api  | [LLM] Response status: 200
athena-api  | [LLM] Response data: {"id": "gen-1770101118-f8VLPtR1LMQHzWYdz76H", "provider": "OpenAI", "model": "openai/gpt-5.2", "object": "chat.completion", "created": 1770101118, "choices": [{"logprobs": null, "finish_reason": "stop", "native_finish_reason": "completed", "index": 0, "message": {"role": "assistant", "content": "{\n  \"material\": \"Sản phẩm làm bằng đồng. Tuy nhiên vì mã HS đã thuộc Chương 84 (nhóm 84.81) là nhóm phân loại theo chức năng của “van, vòi, khóa…” dùng để điều khiển dòng chảy chất lỏng/khí, nên vật
athena-api  | [LLM] Content: {
athena-api  |   "material": "Sản phẩm làm bằng đồng. Tuy nhiên vì mã HS đã thuộc Chương 84 (nhóm 84.81) là nhóm phân loại theo chức năng của “van, vòi, khóa…” dùng để điều khiển dòng chảy chất lỏng/khí, nên vật liệu (đồng/hợp kim đồng) không quyết định việc xếp nhóm mà chủ yếu dùng để xác định phân nhóm/mô tả c
athena-api  | INFO:     172.21.0.1:36496 - "POST /api/search HTTP/1.1" 200 OK

expected: 74182000