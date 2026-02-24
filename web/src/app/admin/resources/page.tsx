"use client";

import { ExternalLink, FileText, Globe, Sparkles, FileArchive } from "lucide-react";

const NOTEBOOK_URL =
  "https://notebooklm.google.com/notebook/5d982e32-e9a6-43a2-a469-090dd46c140c";

type SourceType = "web_page" | "pdf" | "word_doc" | "generated_text";

interface Source {
  id: string;
  title: string;
  type: SourceType;
  url?: string;
}

const SOURCES: Source[] = [
  {
    id: "e0b6257b-4669-4115-b8ed-c67151f0338e",
    title: "1810 TCHQ-TXNK 608858 | PDF - Scribd",
    type: "web_page",
    url: "https://www.scribd.com/document/608858/1810-TCHQ-TXNK",
  },
  {
    id: "2ae81d55-24b0-48b9-8375-fbbdb574607f",
    title:
      "BIỂU THUẾ XUẤT NHẬP KHẨU ƯU ĐÃI THỰC THI CÁC FTA NĂM 2022-2023-2024-2025-2026-2027-2028",
    type: "web_page",
  },
  {
    id: "2df6213e-5e00-47f4-a362-b003981e2849",
    title:
      "Ban hành Nghị định về Biểu thuế nhập khẩu ưu đãi đặc biệt Việt Nam - Campuchia giai đoạn 2025 – 2026",
    type: "web_page",
  },
  {
    id: "f68992e7-3e87-4b96-85a5-c7ceb2b1d9bc",
    title: "Bieu thue XNK 2026 (PDF - A3).pdf",
    type: "word_doc",
  },
  {
    id: "c6e7c110-779f-459c-aa4d-b302e1120585",
    title: "Biểu Thuế Xuất Nhập Khẩu 2026 - Cập Nhật Mới Nhất",
    type: "web_page",
  },
  {
    id: "025eb0aa-87f6-41ba-a4fa-44c67b6ad712",
    title: "Biểu thuế nhập khẩu ưu đãi đặc biệt Việt Nam - Campuchia giai đoạn 2025-2026",
    type: "web_page",
  },
  {
    id: "15b36e85-766f-464f-8864-0654c463472e",
    title: "Biểu thuế nhập khẩu ưu đãi đặc biệt giữa Việt Nam với quốc tế mới ...",
    type: "web_page",
  },
  {
    id: "bd2a08e2-395e-4e92-9dc0-2ce000bb35dd",
    title: "Biểu thuế xuất nhập khẩu mới nhất 2026",
    type: "web_page",
  },
  {
    id: "7b8d2da7-2438-4af4-bcfa-20523870ff67",
    title: "CHÚ GIẢI BỔ SUNG SEN 2022 THEO CÔNG VĂN 3866/TCHQ-TXNK - Rồng Biển Logistics",
    type: "web_page",
  },
  {
    id: "d8f84684-a988-4633-bc00-27670a5a74a0",
    title: "Chú Giải Bổ Sung (SEN): Chìa Khóa Phân Loại HS Code 8 Số",
    type: "web_page",
  },
  {
    id: "3256db08-760f-4410-a846-904c232e7199",
    title: "Chú giải HS2022 - CHUYÊN HS CODE",
    type: "web_page",
  },
  {
    id: "3b328b8d-f61e-4656-b00a-bfd8e5ca656e",
    title: "Chú giải SEN - CHUYÊN HS CODE",
    type: "web_page",
  },
  {
    id: "7fbe9ba1-71aa-4117-a329-71c3079b8d25",
    title: "Chú giải bổ sung SEN: Hướng dẫn phân loại HS code 8 số chính xác",
    type: "web_page",
  },
  {
    id: "73766754-29b6-4228-84d2-03fd79e9e4bd",
    title:
      "Công văn 1810/TCHQ-TXNK 2024 về bản dịch Chú giải chi tiết Danh mục HS 2022",
    type: "web_page",
  },
  {
    id: "63c7575e-91d7-428b-ab7f-1e7b9db23e42",
    title:
      "Công văn 1810/TCHQ-TXNK ngày 26/04/2024 Bản dịch Chú giải chi tiết Danh mục HS 2022",
    type: "web_page",
  },
  {
    id: "398523cf-78ec-4b4e-a689-9bece551d95f",
    title:
      "Công văn 4891/TCHQ-TXNK năm 2022 V/v thực hiện Thông tư số 31/2022/TT-BTC ngày 08/06/2022 - thư viện xuất nhập khẩu",
    type: "web_page",
  },
  {
    id: "dcb6cd45-d303-4283-8e89-d80edef7c4f7",
    title: "Cập nhật biểu thuế xuất nhập khẩu mới nhất 2026 - Finlogistics",
    type: "web_page",
  },
  {
    id: "2c8b6501-8ae3-4eb2-883e-01452bd423ea",
    title: "DANH MỤC HÀNG HOÁ XUẤT NHẬP KHẨU VIỆT NAM PHIÊN BẢN 2022",
    type: "web_page",
  },
  {
    id: "0a5d2845-a50f-4e6d-b6e7-88e714600476",
    title: "HS Code là gì? Cách tra cứu mã HS Code [mới nhất 2026] - LuatVietnam",
    type: "web_page",
    url: "https://luatvietnam.vn/linh-vuc-khac/hs-code-la-gi-883-95133-article.html",
  },
  {
    id: "3bc10dff-6fd0-40cc-a95b-f8d39542ea8f",
    title: "HS code trong xuất nhập khẩu là gì? Cách tra cứu mã code - ECUS",
    type: "web_page",
  },
  {
    id: "ea21ae27-8abb-46b2-b215-14364170593b",
    title: "Hiểu về HS Code #2: 6 qui tắc phân loại mã HS (GIRs) - THT Cargo Logistics",
    type: "web_page",
  },
  {
    id: "136136c3-7f33-4e05-9bc4-453337c4ebad",
    title:
      "HƯỚNG DẪN TRA CỨU ĐỘ UY TÍN CỦA DN KHAI BÁO HẢI QUAN ẢNH HƯỞNG ĐẾN PHÂN LUỒNG TKHQ - CỔNG THÔNG TIN ITS LOGISTICS",
    type: "web_page",
  },
  {
    id: "a90c4bbf-3692-4bd5-9fbe-e91493168697",
    title:
      "Hướng dẫn cách phân loại hàng hoá theo Danh mục Biểu thuế - Cơ sở dữ liệu Quốc gia về Văn bản Pháp luật",
    type: "web_page",
  },
  {
    id: "37ce7235-05a8-47de-b3fb-e8a4e0ca5324",
    title:
      "Hướng dẫn làm thủ tục xác định trước mã số hs code, 3134/TCHQ-TXNK, 5652/TCHQ-TXNK - Cẩm nang XNK",
    type: "web_page",
  },
  {
    id: "2a365076-f1ee-406a-a944-06c450c8ca30",
    title: "Hướng dẫn thủ tục xác định trước mã số hàng hóa - Công ty luật Việt An",
    type: "web_page",
  },
  {
    id: "1ef26fee-8523-460d-8891-0f623e594c7f",
    title:
      "Hướng dẫn thực hiện việc phân loại hàng hoá theo Danh mục hàng hoá xuất khẩu, nhập khẩu và Biểu thuế nhập khẩu ưu đãi, Biểu thuế xuất khẩu",
    type: "web_page",
  },
  {
    id: "b9ffaeab-2456-487c-ad8c-17459184776a",
    title:
      "Hệ thống hóa toàn diện văn bản quy phạm pháp luật và cơ chế vận hành phân loại hàng hóa theo mã HS tại Việt Nam giai đoạn 2025-2026",
    type: "generated_text",
  },
  {
    id: "f9322829-c95f-45c5-aade-b1da34c15a3a",
    title: "I. PHÂN LOẠI HÀNG HÓA - Cẩm nang XNK",
    type: "pdf",
  },
  {
    id: "dd2de3ab-824b-4806-b6e0-a4a6434e65d9",
    title: "Nghị định 111/2020/NĐ-CP biểu thuế xuất khẩu ưu đãi của Việt Nam - Luật Việt Nam",
    type: "web_page",
  },
  {
    id: "296f68e8-3ead-41f2-a31a-c9889be9fc0b",
    title:
      "Nghị định 126/2022/NĐ-CP Biểu thuế nhập khẩu ưu đãi đặc biệt của Việt Nam để thực hiện Hiệp định Thương mại Hàng hóa ASEAN giai đoạn 2022-2027",
    type: "web_page",
  },
  {
    id: "03526b9c-d19c-4a9d-9d3e-5c438df09211",
    title: "Nghị định 199/2025/NĐ-CP: Sửa đổi Biểu thuế xuất nhập khẩu ưu đãi 2023 - LuatVietnam",
    type: "web_page",
  },
  {
    id: "eb30d380-7dea-48e2-b3c4-57cf7b05042b",
    title:
      "Nghị định 260/2025/NĐ-CP sửa đổi mức thuế suất thuế xuất khẩu đối với mặt hàng thuộc nhóm 71.13, 71.14 và 71.15 tại Biểu thuế xuất khẩu theo Danh mục mặt hàng chịu thuế kèm theo Nghị định 26/2023/NĐ-CP - thư viện xuất nhập khẩu",
    type: "web_page",
  },
  {
    id: "049a2113-24c1-4265-baf8-d2c4d8c227ee",
    title: "Nghị định 56/2026/NĐ-CP: Biểu thuế nhập khẩu ưu đãi Việt Nam - LuatVietnam.vn",
    type: "web_page",
  },
  {
    id: "873e43a9-72f0-4571-b558-fbda374d5482",
    title: "Nghị định số 56/2026/NĐ-CP của Chính phủ: Biểu thuế nhập khẩu ...",
    type: "web_page",
  },
  {
    id: "8fdc4354-267e-4c46-a788-7e31caebdc21",
    title: "Thông tư 31/2022/TT-BTC - Thutucxuatnhapkhau.vn",
    type: "web_page",
  },
  {
    id: "d164115a-dd0d-4203-9757-23ca016daa9d",
    title: "Thông tư 31/2022/TT-BTC Danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam",
    type: "web_page",
  },
  {
    id: "411ab355-6ccc-4408-b70b-b768f406bf8a",
    title:
      "Thông tư 31/2022/TT-BTC Ngày 08/06/2022 Ban Hành Danh Mục Hàng Hóa Xuất Khẩu, Nhập Khẩu Việt Nam",
    type: "web_page",
  },
  {
    id: "6289758d-8183-49a8-b12d-ad4d09e63f56",
    title: "Thông tư số 31/2022/TT-BTC về việc danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam",
    type: "web_page",
  },
  {
    id: "50d916e6-1ad6-4bfd-8865-85dc5e5118f8",
    title: "Thủ tục hải quan xuất khẩu hàng hóa 2026 và quy trình mới nhất - InterLOG",
    type: "web_page",
  },
  {
    id: "9f8dd1a5-b10f-472f-b27e-e9643856c5b3",
    title: "Thủ tục xác định trước mã HS code hàng hóa xuất nhập khẩu",
    type: "web_page",
  },
  {
    id: "fbf7c03c-ad9c-4ab1-a0a9-dab635cfc875",
    title: "Thủ tục xác định trước mã số hàng hóa của Công ty cổ phần - LuatVietnam",
    type: "web_page",
  },
  {
    id: "fb258b09-59a2-460c-8343-caf9e8fbeb56",
    title: "Top 5 Website Tra Cứu Mã HS Chính Xác, Cách Dùng Nhanh",
    type: "web_page",
  },
  {
    id: "4693dbaa-1cff-4bf3-a6c5-c0803ff9fde7",
    title: "Tìm hiểu về HS Code",
    type: "web_page",
  },
];

const TYPE_CONFIG: Record<
  SourceType,
  { label: string; icon: React.ReactNode; className: string }
> = {
  web_page: {
    label: "Trang web",
    icon: <Globe className="w-3 h-3" />,
    className: "bg-blue-50 text-blue-700 border-blue-200",
  },
  pdf: {
    label: "PDF",
    icon: <FileText className="w-3 h-3" />,
    className: "bg-red-50 text-red-700 border-red-200",
  },
  word_doc: {
    label: "Tài liệu",
    icon: <FileArchive className="w-3 h-3" />,
    className: "bg-indigo-50 text-indigo-700 border-indigo-200",
  },
  generated_text: {
    label: "Tổng hợp AI",
    icon: <Sparkles className="w-3 h-3" />,
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
};

function searchUrl(title: string) {
  return `https://www.google.com/search?q=${encodeURIComponent(title)}`;
}

export default function ResourcesPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Tài liệu tham khảo
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {SOURCES.length} nguồn từ kho kiến thức NotebookLM về biểu thuế xuất nhập khẩu Việt Nam 2026
          </p>
        </div>
        <a
          href={NOTEBOOK_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm text-emerald-700 border border-emerald-200 bg-emerald-50 rounded-lg px-3 py-2 hover:bg-emerald-100 transition-colors shrink-0"
        >
          <ExternalLink className="w-4 h-4" />
          Mở NotebookLM
        </a>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left py-3 px-4 font-medium text-slate-600 w-10">#</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Tên tài liệu</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600 w-36">Loại</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600 w-28">Liên kết</th>
            </tr>
          </thead>
          <tbody>
            {SOURCES.map((source, index) => {
              const typeConfig = TYPE_CONFIG[source.type];
              const link = source.url ?? searchUrl(source.title);
              const isSearch = !source.url;

              return (
                <tr
                  key={source.id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
                >
                  <td className="py-3 px-4 text-slate-400 text-xs">{index + 1}</td>
                  <td className="py-3 px-4 text-slate-800 leading-snug">
                    {source.title}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border font-medium ${typeConfig.className}`}
                    >
                      {typeConfig.icon}
                      {typeConfig.label}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <a
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={isSearch ? "Tìm kiếm tài liệu này trên Google" : "Mở liên kết gốc"}
                      className="inline-flex items-center gap-1 text-xs text-emerald-700 hover:text-emerald-800 hover:underline"
                    >
                      <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      {isSearch ? "Tìm kiếm" : "Xem nguồn"}
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
