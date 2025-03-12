
## Cài đặt và chạy

1. Clone repository này về máy:
```
git clone <url-repository>
cd <ten-thu-muc>
```

2. Cài đặt các thư viện cần thiết:
```
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```
streamlit run app.py
```

## Cấu trúc dự án

- `app.py`: File chính để chạy ứng dụng
- `utils.py`: Chứa các hàm tiện ích và xử lý dữ liệu
- `pages/`: Thư mục chứa các trang của ứng dụng
  - `trang_chu.py`: Trang tổng quan
  - `giao_dich.py`: Trang quản lý giao dịch
  - `bao_cao.py`: Trang báo cáo tháng

## Ghi chú

- Ứng dụng sử dụng session_state của Streamlit để lưu trữ dữ liệu tạm thời
- Để lưu trữ dữ liệu vĩnh viễn, bạn có thể thêm tích hợp với cơ sở dữ liệu như SQLite, MySQL hoặc Google Sheets

## Yêu cầu hệ thống

- Python 3.7+
- Streamlit 1.33.0+
- Pandas 2.2.0+
- Plotly 5.18.0+