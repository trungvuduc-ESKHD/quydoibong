import streamlit as st
import streamlit_option_menu as som
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils
from datetime import datetime

# Thiết lập cấu hình trang
st.set_page_config(
    page_title="Quỹ đội bóng Eurofins",
    page_icon="💰",
    layout="wide"
)

# Kiểm tra và khởi tạo session state nếu cần
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# Đảm bảo summary luôn được khởi tạo
utils.initialize_data()

# Tạo header và menu điều hướng
def main():
    # CSS
    st.markdown("""
    <style>
    .main-header {
        display: flex;
        align-items: center;
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .logo-text {
        font-size: 1.5rem;
        font-weight: bold;
        margin-left: 0.5rem;
        color: #1E3A8A;
    }
    .main-container {
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div style="background-color: #1E3A8A; color: white; padding: 8px; border-radius: 8px;">
            <span style="font-size: 1.2rem;">💰</span>
        </div>
        <div class="logo-text">Quỹ đội bóng Eurofins</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu điều hướng
    selected = som.option_menu(
        menu_title=None,
        options=["Tổng quan", "Giao dịch", "Báo cáo"],
        icons=["house", "list-ul", "bar-chart"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "margin": "0!important"},
            "icon": {"color": "#1E3A8A", "font-size": "14px"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#1E3A8A"},
        }
    )
    
    # Hiển thị trang tương ứng
    if selected == "Tổng quan":
        show_home_page()
    elif selected == "Giao dịch":
        show_transactions_page()
    elif selected == "Báo cáo":
        show_reports_page()

def show_home_page():
    # Hiển thị trang chủ trực tiếp trong app.py
    st.markdown("<h2>Tổng quan quỹ</h2>", unsafe_allow_html=True)
    
    # Tạo layout
    col1, col2 = st.columns([3, 2])
    
    # Cập nhật tổng hợp
    utils.update_summary()
    
    # Hiển thị thông tin tổng hợp
    with col1:
        # Thẻ thông tin
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3>Số dư hiện tại</h3>
            <div style="font-size: 2rem; font-weight: bold; color: #1E3A8A; margin: 10px 0;">
                {current_balance}
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                <div>
                    <div style="font-size: 0.9rem; color: #6c757d;">Tổng thu</div>
                    <div style="font-size: 1.2rem; color: #198754; font-weight: 500;">{total_income}</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; color: #6c757d;">Tổng chi</div>
                    <div style="font-size: 1.2rem; color: #dc3545; font-weight: 500;">{total_expense}</div>
                </div>
            </div>
        </div>
        """.format(
            current_balance=utils.format_currency(st.session_state.summary['current_balance']),
            total_income=utils.format_currency(st.session_state.summary['total_income']),
            total_expense=utils.format_currency(st.session_state.summary['total_expense'])
        ), unsafe_allow_html=True)
        
        # Danh sách giao dịch gần đây
        st.markdown("<h3>Giao dịch gần đây</h3>", unsafe_allow_html=True)
        
        # Lấy 5 giao dịch gần nhất
        recent_transactions = st.session_state.transactions[:5]
        
        # Tạo dataframe
        df = utils.get_transaction_df(recent_transactions)
        
        # Hiển thị danh sách giao dịch
        if not df.empty:
            for _, row in df.iterrows():
                cols = st.columns([3, 2, 2, 3])
                
                # Format row
                icon = "⬇️" if row['type'] == 'income' else "⬆️"
                color = "green" if row['type'] == 'income' else "red"
                
                cols[0].markdown(f"<div style='display: flex; align-items: center;'><span>{icon}</span><span style='margin-left: 5px;'>{row['description']}</span></div>", unsafe_allow_html=True)
                cols[1].markdown(f"{row['category']}")
                cols[2].markdown(f"{row['date']}")
                cols[3].markdown(f"<span style='color: {color};'>{row['amount_display']}</span>", unsafe_allow_html=True)
                
                # Đường phân cách
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        else:
            st.info("Chưa có giao dịch nào")

    # Cột phải
    with col2:
        # Form thêm giao dịch mới
        st.markdown("<h3>Thêm giao dịch mới</h3>", unsafe_allow_html=True)
        
        with st.form(key="add_transaction_form"):
            # Loại giao dịch
            transaction_type = st.radio(
                "Loại giao dịch",
                options=["income", "expense"],
                format_func=lambda x: "Thu" if x == "income" else "Chi",
                horizontal=True
            )
            
            # Số tiền
            amount = st.number_input(
                "Số tiền (VNĐ)",
                min_value=1000.0,
                step=10000.0,
                format="%g"
            )
            
            # Mô tả
            description = st.text_input("Mô tả")
            
            # Danh mục
            category = st.selectbox(
                "Danh mục",
                options=utils.CATEGORIES[transaction_type]
            )
            
            # Ngày tháng
            date = st.date_input("Ngày")
            
            # Nút thêm
            button_label = "Thêm khoản thu" if transaction_type == "income" else "Thêm khoản chi"
            
            submitted = st.form_submit_button(
                button_label,
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validate
                if not description or amount <= 0:
                    st.error("Vui lòng điền đầy đủ thông tin và số tiền hợp lệ")
                else:
                    # Thêm giao dịch
                    transaction_data = {
                        'type': transaction_type,
                        'amount': amount,
                        'description': description,
                        'category': category,
                        'date': date.strftime("%Y-%m-%d")
                    }
                    
                    utils.add_transaction(transaction_data)
                    st.success("Đã thêm giao dịch thành công!")
                    st.rerun() # Changed here

def show_transactions_page():
    # Container chính
    st.markdown("<h2>Quản lý giao dịch</h2>", unsafe_allow_html=True)
    
    # Layout: 2 cột (tỉ lệ 2:1)
    col_left, col_right = st.columns([2, 1])
    
    # Cột trái: Danh sách giao dịch với bộ lọc
    with col_left:
        st.markdown("<h3>Lịch sử giao dịch</h3>", unsafe_allow_html=True)
        
        # Bộ lọc
        filter_cols = st.columns([2, 1])
        with filter_cols[0]:
            search = st.text_input("Tìm kiếm giao dịch", placeholder="Nhập từ khóa...")
        with filter_cols[1]:
            transaction_type_filter = st.selectbox(
                "Loại giao dịch",
                options=["all", "income", "expense"],
                format_func=lambda x: "Tất cả" if x == "all" else ("Thu" if x == "income" else "Chi")
            )
        
        # Lọc danh sách giao dịch
        filtered_transactions = st.session_state.transactions
        
        # Lọc theo loại giao dịch
        if transaction_type_filter != "all":
            filtered_transactions = [t for t in filtered_transactions if t['type'] == transaction_type_filter]
        
        # Lọc theo từ khóa
        if search:
            filtered_transactions = [
                t for t in filtered_transactions 
                if search.lower() in t['description'].lower() or search.lower() in t['category'].lower()
            ]
        
        # Tạo dataframe
        df = utils.get_transaction_df(filtered_transactions)
        
        # Hiển thị danh sách giao dịch
        if not df.empty:
            st.markdown("<div style='max-height: 600px; overflow-y: auto;'>", unsafe_allow_html=True)
            
            for _, row in df.iterrows():
                cols = st.columns([3, 2, 2, 2, 1])
                
                # Format row
                icon = "⬇️" if row['type'] == 'income' else "⬆️"
                color = "green" if row['type'] == 'income' else "red"
                
                cols[0].markdown(f"<div style='display: flex; align-items: center;'><span>{icon}</span><span style='margin-left: 5px;'>{row['description']}</span></div>", unsafe_allow_html=True)
                cols[1].markdown(f"{row['category']}")
                cols[2].markdown(f"{row['date']}")
                cols[3].markdown(f"<span style='color: {color};'>{row['amount_display']}</span>", unsafe_allow_html=True)
                
                # Nút xóa
                if cols[4].button("🗑️", key=f"delete_{row['id']}"):
                    # Xác nhận xóa
                    delete_confirm = st.warning(f"Bạn có chắc chắn muốn xóa giao dịch '{row['description']}'?")
                    col1, col2 = st.columns(2)
                    
                    if col1.button("Xác nhận", key=f"confirm_{row['id']}"):
                        utils.delete_transaction(row['id'])
                        st.success("Đã xóa giao dịch!")
                        st.rerun() # Changed here
                    
                    if col2.button("Hủy", key=f"cancel_{row['id']}"):
                        st.rerun() # Changed here
                
                # Đường phân cách
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Không có giao dịch nào")
    
    # Cột phải: Form thêm giao dịch
    with col_right:
        st.markdown("<h3>Thêm giao dịch mới</h3>", unsafe_allow_html=True)
        st.markdown("<div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
        
        with st.form(key="add_transaction_form_page"):
            # Loại giao dịch
            transaction_type = st.radio(
                "Loại giao dịch",
                options=["income", "expense"],
                format_func=lambda x: "Thu" if x == "income" else "Chi",
                horizontal=True
            )
            
            # Số tiền
            amount = st.number_input(
                "Số tiền (VNĐ)",
                min_value=1000.0,
                step=10000.0,
                format="%g"
            )
            
            # Mô tả
            description = st.text_input("Mô tả")
            
            # Danh mục
            category = st.selectbox(
                "Danh mục",
                options=utils.CATEGORIES[transaction_type]
            )
            
            # Ngày tháng
            date = st.date_input("Ngày")
            
            # Nút thêm
            button_label = "Thêm khoản thu" if transaction_type == "income" else "Thêm khoản chi"
            
            submitted = st.form_submit_button(
                button_label,
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validate
                if not description or amount <= 0:
                    st.error("Vui lòng điền đầy đủ thông tin và số tiền hợp lệ")
                else:
                    # Thêm giao dịch
                    transaction_data = {
                        'type': transaction_type,
                        'amount': amount,
                        'description': description,
                        'category': category,
                        'date': date.strftime("%Y-%m-%d")
                    }
                    
                    utils.add_transaction(transaction_data)
                    st.success("Đã thêm giao dịch thành công!")
                    st.rerun() # Changed here
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_reports_page():
    # Container chính
    st.markdown("<h2>Báo cáo tháng</h2>", unsafe_allow_html=True)
    
    # Lấy danh sách các tháng
    months = utils.get_all_months()
    
    # Nếu không có dữ liệu
    if not months:
        st.warning("Chưa có dữ liệu giao dịch để tạo báo cáo")
        return
    
    # Chọn tháng
    selected_month = st.selectbox(
        "Chọn tháng",
        options=months,
        format_func=lambda x: f"{x[5:7]}/{x[:4]}"  # Format MM/YYYY
    )
    
    # Lấy báo cáo tháng đã chọn
    report = utils.get_monthly_report(selected_month)
    
    # Hiển thị tóm tắt và biểu đồ
    col1, col2 = st.columns(2)
    
    # Card tổng quan
    with col1:
        st.markdown("<h3>Tổng quan tháng</h3>", unsafe_allow_html=True)
        
        # Tạo card tổng quan
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #dee2e6;">
                <span style="color: #6c757d;">Tổng thu</span>
                <span style="color: #52c41a; font-weight: 500;">{utils.format_currency(report['total_income'])}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #dee2e6;">
                <span style="color: #6c757d;">Tổng chi</span>
                <span style="color: #f5222d; font-weight: 500;">{utils.format_currency(report['total_expense'])}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 10px 0;">
                <span style="font-weight: 500;">Số dư</span>
                <span style="font-weight: 700; font-size: 18px;">{utils.format_currency(report['balance'])}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Biểu đồ thu chi
        if report['total_income'] > 0 or report['total_expense'] > 0:
            fig = utils.plot_income_expense_bar(report['total_income'], report['total_expense'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Biểu đồ theo danh mục
    with col2:
        st.markdown("<h3>Chi tiêu theo danh mục</h3>", unsafe_allow_html=True)
        
        # Lấy chi tiêu theo danh mục
        expense_by_category = utils.get_expense_by_category(report['transactions'])
        
        if expense_by_category:
            fig = utils.plot_category_pie(expense_by_category)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Không có dữ liệu chi tiêu trong tháng này")
    
    # Danh sách giao dịch trong tháng
    st.markdown("<h3>Giao dịch trong tháng</h3>", unsafe_allow_html=True)
    
    # Tạo dataframe
    df = utils.get_transaction_df(report['transactions'])
    
    # Hiển thị danh sách giao dịch
    if not df.empty:
        st.markdown("<div style='max-height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
        
        for _, row in df.iterrows():
            cols = st.columns([3, 2, 2, 2, 1])
            
            # Format row
            icon = "⬇️" if row['type'] == 'income' else "⬆️"
            color = "green" if row['type'] == 'income' else "red"
            
            cols[0].markdown(f"<div style='display: flex; align-items: center;'><span>{icon}</span><span style='margin-left: 5px;'>{row['description']}</span></div>", unsafe_allow_html=True)
            cols[1].markdown(f"{row['category']}")
            cols[2].markdown(f"{row['date']}")
            cols[3].markdown(f"<span style='color: {color};'>{row['amount_display']}</span>", unsafe_allow_html=True)
            
            # Nút xóa
            if cols[4].button("🗑️", key=f"delete_report_{row['id']}"):
                utils.delete_transaction(row['id'])
                st.rerun() # Changed here
            
            # Đường phân cách
            st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Không có giao dịch nào trong tháng này")

# Main
if __name__ == "__main__":
    main()