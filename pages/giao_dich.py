import streamlit as st
import pandas as pd
import utils

def show():
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