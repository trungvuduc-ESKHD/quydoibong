import streamlit as st
import pandas as pd
import plotly.express as px
import utils
from datetime import datetime
import uuid

def show():
    # Cập nhật session state
    utils.update_summary()

    # Container chính
    st.markdown("<h2>Tổng quan quỹ</h2>", unsafe_allow_html=True)
    
    # Hiển thị tóm tắt
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #6c757d; font-size: 14px;">Số dư hiện tại</span>
                <div style="background-color: #e6f7ff; padding: 8px; border-radius: 50%;">
                    <span style="color: #1890ff; font-size: 16px;">💰</span>
                </div>
            </div>
            <p style="font-size: 24px; font-weight: bold; margin-top: 10px;">{}</p>
        </div>
        """.format(utils.format_currency(st.session_state.summary['current_balance'])), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #6c757d; font-size: 14px;">Tổng thu</span>
                <div style="background-color: #e6ffe6; padding: 8px; border-radius: 50%;">
                    <span style="color: #52c41a; font-size: 16px;">⬇️</span>
                </div>
            </div>
            <p style="font-size: 24px; font-weight: bold; margin-top: 10px; color: #52c41a;">{}</p>
        </div>
        """.format(utils.format_currency(st.session_state.summary['total_income'])), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #6c757d; font-size: 14px;">Tổng chi</span>
                <div style="background-color: #ffe6e6; padding: 8px; border-radius: 50%;">
                    <span style="color: #f5222d; font-size: 16px;">⬆️</span>
                </div>
            </div>
            <p style="font-size: 24px; font-weight: bold; margin-top: 10px; color: #f5222d;">{}</p>
        </div>
        """.format(utils.format_currency(st.session_state.summary['total_expense'])), unsafe_allow_html=True)
    
    # Layout chính: 2 cột
    col_left, col_right = st.columns([2, 1])
    
    # Cột trái: Danh sách giao dịch
    with col_left:
        st.markdown("<h3>Lịch sử giao dịch</h3>", unsafe_allow_html=True)
        
        # Tìm kiếm
        search = st.text_input("Tìm kiếm giao dịch", placeholder="Nhập từ khóa...")
        
        # Lọc danh sách giao dịch
        filtered_transactions = st.session_state.transactions
        if search:
            filtered_transactions = [
                t for t in filtered_transactions 
                if search.lower() in t['description'].lower() or search.lower() in t['category'].lower()
            ]
        
        # Tạo dataframe
        df = utils.get_transaction_df(filtered_transactions)
        
        if not df.empty:
            # Custom định dạng
            def format_row(row):
                icon = "⬇️" if row['type'] == 'income' else "⬆️"
                color = "color: green" if row['type'] == 'income' else "color: red"
                return [
                    f"<div style='display: flex; align-items: center;'><span>{icon}</span><span style='margin-left: 5px;'>{row['description']}</span></div>",
                    f"<div>{row['category']}</div>",
                    f"<div>{row['date']}</div>",
                    f"<div style='{color}'>{row['amount_display']}</div>"
                ]
            
            # Áp dụng định dạng
            if not df.empty:
                # Tạo bảng tùy chỉnh
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
                    if cols[4].button("🗑️", key=f"delete_{row['id']}"):
                        utils.delete_transaction(row['id'])
                        st.rerun() # Changed here
                    
                    # Đường phân cách
                    st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Không có giao dịch nào")
    
    # Cột
    
    # Cột phải: Form thêm và biểu đồ
    with col_right:
        # Form thêm giao dịch
        st.markdown("<h3>Thêm giao dịch mới</h3>", unsafe_allow_html=True)
        
        with st.form(key="add_transaction_form"):
            # Loại giao dịch
            transaction_type = st.radio(
                "Loại giao dịch",
                options=["income", "expense"],
                format_func=lambda x: "Thu" if x == "income" else "Chi",
                horizontal=True,
                key="transaction_type"
            )
            
            # Số tiền
            amount = st.number_input(
                "Số tiền (VNĐ)",
                min_value=1000.0,
                step=10000.0,
                format="%g",
                key="amount"
            )
            
            # Mô tả
            description = st.text_input(
                "Mô tả",
                key="description"
            )
            
            # Danh mục
            category = st.selectbox(
                "Danh mục",
                options=utils.CATEGORIES[transaction_type],
                key="category"
            )
            
            # Ngày tháng
            date = st.date_input(
                "Ngày",
                value=datetime.now(),
                key="date"
            )
            
            # Nút thêm
            button_label = "Thêm khoản thu" if transaction_type == "income" else "Thêm khoản chi"
            button_color = "green" if transaction_type == "income" else "red"
            
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
                    st.experimental_rerun()
        
        # Biểu đồ chi tiêu theo danh mục
        st.markdown("<h3>Chi tiêu theo danh mục</h3>", unsafe_allow_html=True)
        
        # Lấy chi tiêu theo danh mục
        expense_by_category = utils.get_expense_by_category(st.session_state.transactions)
        
        if expense_by_category:
            fig = utils.plot_category_pie(expense_by_category)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu chi tiêu")

    # Khởi tạo dữ liệu mẫu (chỉ chạy một lần)
    if 'initialized' not in st.session_state:
        utils.initialize_data()
        st.session_state.initialized = True