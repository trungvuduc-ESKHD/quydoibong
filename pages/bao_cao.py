import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils
from datetime import datetime

def show():
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
                st.experimental_rerun()
            
            # Đường phân cách
            st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Không có giao dịch nào trong tháng này")