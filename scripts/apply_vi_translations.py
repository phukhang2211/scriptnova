#!/usr/bin/env python
"""Apply Vietnamese strings to locale/vi/LC_MESSAGES/django.po (same order as msgids from makemessages)."""
from __future__ import annotations

import sys
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parent.parent
PO_PATH = ROOT / "locale/vi/LC_MESSAGES/django.po"

# Same order as /tmp/msgids.json produced from django.po (98 entries).
VI_TEXT = [
    "English",
    "Tiếng Việt",
    "Tệp âm thanh hoặc video",
    "Tệp quá lớn. Dung tối đa là %(max_mb)s MB.",
    "Định dạng không được hỗ trợ. Cho phép: %(extensions)s",
    "Mã xác nhận",
    "Bắt buộc sau nhiều lần đăng nhập sai.",
    "Thiếu mã xác nhận. Tải lại trang và thử lại.",
    "Trả lời mã xác nhận không đúng.",
    "Email",
    "Tiêu đề",
    "Nội dung",
    "Đang chờ",
    "Đang xử lý",
    "Hoàn thành",
    "Thất bại",
    "Miễn phí",
    "Pro",
    "%(a)s + %(b)s bằng bao nhiêu?",
    "Đã đạt giới hạn tải lên tháng này (%(used)s/%(limit)s). Nâng cấp để tiếp tục.",
    "Quá nhiều lần tải trong thời gian ngắn. Vui lòng chờ một phút.",
    "Vui lòng chọn tệp hợp lệ.",
    "Đã nhận tệp. Đang bắt đầu phiên âm.",
    "Đã xếp lại job #%(id)s để thử lại.",
    "[Liên hệ ScriptNova] %(subject)s",
    "Đã gửi tin nhắn. Chúng tôi sẽ phản hồi sớm.",
    "Khóa API AssemblyAI",
    "Khóa bí mật Stripe",
    "ID giá Stripe",
    "Bí mật webhook Stripe",
    "URL broker Celery",
    "Cấu hình cơ sở dữ liệu",
    "Backend email",
    "Email hỗ trợ",
    "Stripe chưa được cấu hình.",
    "Thanh toán hoàn tất. Gói đăng ký sẽ đồng bộ sau webhook.",
    "Đã hủy thanh toán.",
    "Điều hướng chính",
    "Tình trạng",
    "Điều khoản",
    "Quyền riêng tư",
    "Liên hệ",
    "Bảng điều khiển",
    "Bảng giá",
    "Ngôn ngữ",
    "Đăng xuất",
    "Đăng nhập",
    "ScriptNova — phiên âm nhanh từ audio và video của bạn.",
    "Liên hệ",
    "Bảng điều khiển phiên âm",
    "Tải lên âm thanh hoặc video, sau đó mở từng job để đọc hoặc sao chép bản phiên âm.",
    "Dùng trong tháng này",
    "Đã đạt giới hạn",
    "Nâng cấp Pro",
    "để tải thêm trong tháng này.",
    "Tải lên mới",
    "Tải lên và phiên âm",
    "Job của bạn",
    "Job #%(n)s",
    "Chưa có job nào. Hãy tải tệp phía trên để bắt đầu.",
    "Trạng thái",
    "Lỗi",
    "Thử lại job",
    "Bản phiên âm",
    "← Quay lại bảng điều khiển",
    "Câu hỏi, góp ý hoặc hỗ trợ — chúng tôi đọc mọi tin nhắn.",
    "Ưu tiên email?",
    "Gửi tin nhắn",
    "Tình trạng tích hợp",
    "Kiểm tra nhanh khóa API và cài đặt quan trọng (%(ready)s / %(total)s).",
    "Ổn",
    "Thiếu",
    "Phiên âm rõ ràng, nhanh chóng",
    "Âm thanh & video thành văn bản",
    "Biến bản ghi thành văn bản rõ ràng chỉ trong vài phút.",
    "ScriptNova phục vụ nhà sáng tạo, nhóm và mọi người cần văn bản chính xác từ nội dung nói — không cần quy trình phức tạp.",
    "Bắt đầu",
    "Xem bảng giá",
    "Vì sao chọn ScriptNova",
    "Luồng tải lên đơn giản từ bảng điều khiển",
    "Xử lý tự động, sẵn sàng xuất qua email",
    "Gói miễn phí để thử, Pro khi bạn cần quy mô",
    "Giới hạn đơn giản. Nâng cấp khi vượt gói miễn phí.",
    "Gói của bạn",
    "lượt tải lên mỗi tháng",
    "Stripe chưa được cấu hình. Thêm khóa Stripe vào <code>.env</code> để bật thanh toán.",
    "Cách chúng tôi xử lý tệp và dữ liệu tài khoản của bạn.",
    "Tệp tải lên dùng để tạo bản phiên âm và siêu dữ liệu cần để vận hành dịch vụ. Bản MVP này có chính sách lưu trữ/xóa tối giản và có thể mở rộng sau.",
    "Chúng tôi không bán nội dung của bạn. Liên hệ nếu bạn cần bản sao dữ liệu hoặc thắc mắc về xử lý.",
    "Điều khoản sử dụng",
    "Vui lòng đọc tóm tắt này trước khi dùng dịch vụ.",
    "Đây là dịch vụ MVP dùng nguyên trạng. Không tải lên dữ liệu cá nhân nhạy cảm mà bạn không được phép chia sẻ, hoặc nội dung trái pháp luật. Chúng tôi có thể cập nhật điều khoản khi sản phẩm phát triển.",
    "Khi dùng ScriptNova, bạn đồng ý chịu trách nhiệm về nội dung tải lên và tuân thủ luật pháp cùng quyền của bên thứ ba.",
    "Chào mừng trở lại",
    "Đăng nhập để tải tệp và xem bản phiên âm.",
    "Kiểm tra tên đăng nhập và mật khẩu.",
    "Đăng nhập",
    'Lần đầu? Hỏi quản trị để tạo tài khoản, hoặc dùng <code style="font-size: 0.85em;">createsuperuser</code> trên máy cục bộ.',
]


def main() -> int:
    po = polib.pofile(str(PO_PATH))
    msgids = [e.msgid for e in po if e.msgid]
    if len(msgids) != len(VI_TEXT):
        print(
            f"Mismatch: PO has {len(msgids)} strings, VI_TEXT has {len(VI_TEXT)}.",
            file=sys.stderr,
        )
        return 1
    vi_map = dict(zip(msgids, VI_TEXT))
    for entry in po:
        if entry.msgid and entry.msgid in vi_map:
            entry.msgstr = vi_map[entry.msgid]
    po.metadata["Language"] = "vi"
    po.metadata.setdefault("Content-Type", "text/plain; charset=utf-8")
    po.save(str(PO_PATH))
    print(f"Updated {PO_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
