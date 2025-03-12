import pandas as pd
import streamlit as st
from datetime import datetime
import uuid
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Literal, Optional, TypedDict, Union
import gspread
from google.oauth2.service_account import Credentials

# --- Data Types ---
class Transaction(TypedDict):
    id: str
    type: Literal['income', 'expense']
    amount: float
    description: str
    category: str
    date: str
    image_url: Optional[str]

# --- Constants ---
CATEGORIES = {
    'income': ['Đóng phí', 'Tài trợ', 'Khác'],
    'expense': ['Sân bóng', 'Thiết bị', 'Nước uống', 'Đồng phục', 'Khác']
}

# --- Utility Functions ---
def format_currency(amount: float) -> str:
    return f"{amount:,.0f} VNĐ"

# --- Google Sheets Configuration ---
def get_google_sheet():
    """Connects to Google Sheets using credentials from Streamlit secrets."""
    try:
        # Get credentials from Streamlit secrets
        creds_dict = st.secrets["gcp_service_account"]  # Assuming you named the secret 'gcp_service_account'

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"  # Add Drive API for permissions
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.service_account(filename=None, creds=creds)  # Use creds parameter
        spreadsheet_id = st.secrets["spreadsheet_id"] # Assuming you named the secret 'spreadsheet_id'

        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.sheet1  # Or use sh.worksheet("Sheet Name")

        return worksheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# --- Transaction Management Functions (Google Sheets) ---
def add_transaction(transaction_data: Dict, image_file=None) -> None:
    """Adds a new transaction to Google Sheets and session state."""
    try:
        transaction_id = str(uuid.uuid4())
        #  No supabase storage, will add later

        # Create the transaction object
        transaction = {
            'id': transaction_id,
            'type': transaction_data['type'],
            'amount': float(transaction_data['amount']),
            'description': transaction_data['description'],
            'category': transaction_data['category'],
            'date': transaction_data['date'],
            'image_url': None  # Or implement Google Drive storage if needed
        }
        # Write data to google sheet
        worksheet = get_google_sheet()
        if worksheet is None:
            st.error("Could not connect to Google Sheets")
            return

        row = [transaction['id'], transaction['type'], transaction['amount'], transaction['description'], transaction['category'], transaction['date'], transaction['image_url']]

        worksheet.append_row(row)  # Appends a row to the spreadsheet

        # Update session state (add to the beginning)
        st.session_state.transactions.insert(0, transaction)

        # Update summary
        update_summary()

    except Exception as e:
        st.error(f"Error adding transaction to Google Sheets: {e}")

def delete_transaction(transaction_id: str) -> None:
    """Deletes a transaction from Google Sheets and session state."""
    try:
        worksheet = get_google_sheet()
        if worksheet is None:
            st.error("Could not connect to Google Sheets")
            return

        # Find the row to delete (inefficient, optimize if needed)
        transactions = get_transactions_from_sheet()  # Reload from sheet
        row_index = None
        for i, transaction in enumerate(transactions):
            if transaction['id'] == transaction_id:
                row_index = i + 2 # +2 because Google Sheets is 1-indexed and has a header row
                break

        if row_index:
            worksheet.delete_rows(row_index)  # Deletes the row

            # Update session state
            st.session_state.transactions = [t for t in st.session_state.transactions if t['id'] != transaction_id]

            # Update summary
            update_summary()
        else:
            st.warning(f"Transaction with ID '{transaction_id}' not found.")

    except Exception as e:
        st.error(f"Error deleting transaction from Google Sheets: {e}")

def get_transactions_from_sheet() -> List[Dict]:
    """Loads transactions from Google Sheets."""
    try:
        worksheet = get_google_sheet()
        if worksheet is None:
            st.error("Could not connect to Google Sheets")
            return []

        # Get all records from the worksheet
        records = worksheet.get_all_records()  # Returns a list of dictionaries

        # The headers from a single row
        header = ['id', 'type', 'amount', 'description', 'category', 'date', 'image_url']
        if not records:
            print(f"Warning, no records on google sheet {spreadsheet_id}, generating header")
            worksheet.append_row(header)
            return []

        # The keys (as a single dict)
        return [
            {header[0]: row['id'], header[1]: row['type'], header[2]: row['amount'], header[3]: row['description'], header[4]: row['category'],
            header[5]: row['date'], header[6]: row['image_url']}
            for row in records  # Correctly iterates through the retrieved data
        ]
    except Exception as e:
        st.error(f"Error loading transactions from Google Sheets: {e}")
        return []

# --- Remaining Functions (Mostly Unchanged) ---
def update_summary() -> None:
    """Updates summary information based on session state."""
    if 'summary' not in st.session_state:
        st.session_state.summary = {
            'current_balance': 0,
            'total_income': 0,
            'total_expense': 0
        }

    total_income = sum(t['amount'] for t in st.session_state.transactions if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in st.session_state.transactions if t['type'] == 'expense')
    current_balance = total_income - total_expense

    st.session_state.summary = {
        'current_balance': current_balance,
        'total_income': total_income,
        'total_expense': total_expense
    }

def get_all_months() -> List[str]:
    """Gets a list of all months in the data."""
    months = set()

    for t in st.session_state.transactions:
        month = t['date'][:7]  # YYYY-MM
        months.add(month)

    return sorted(list(months), reverse=True)

def get_monthly_report(month: str) -> Dict:
    """Gets the report for a specific month."""
    monthly_transactions = [t for t in st.session_state.transactions if t['date'].startswith(month)]

    total_income = sum(t['amount'] for t in monthly_transactions if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in monthly_transactions if t['type'] == 'expense')
    balance = total_income - total_expense

    return {
        'month': month,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'transactions': monthly_transactions
    }

def get_expense_by_category(transactions: List[Transaction]) -> Dict[str, float]:
    """Gets expenses by category."""
    expenses_by_category = {}

    for t in transactions:
        if t['type'] == 'expense':
            category = t['category']
            if category in expenses_by_category:
                expenses_by_category[category] += t['amount']
            else:
                expenses_by_category[category] = t['amount']

    return expenses_by_category

def get_transaction_df(transactions: List[Transaction]) -> pd.DataFrame:
    """Converts transaction list to DataFrame."""
    if not transactions:
        return pd.DataFrame()

    df = pd.DataFrame(transactions)

    # Add display columns
    df['amount_display'] = df.apply(
        lambda row: (f"+ {format_currency(row['amount'])}" if row['type'] == 'income'
                    else f"- {format_currency(row['amount'])}"),
        axis=1
    )

    df['color'] = df['type'].apply(lambda x: 'green' if x == 'income' else 'red')

    return df

def plot_income_expense_bar(income: float, expense: float) -> go.Figure:
    """Creates income/expense bar chart."""
    fig = go.Figure(data=[
        go.Bar(
            x=['Thu', 'Chi'],
            y=[income, expense],
            marker_color=['#4ade80', '#f87171']
        )
    ])

    fig.update_layout(
        title='Thu - Chi',
        xaxis_title='Loại',
        yaxis_title='Số tiền (VNĐ)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=0),
        height=250
    )

    # Add labels on bars
    fig.update_traces(
        text=[format_currency(income), format_currency(expense)],
        textposition='outside'
    )

    return fig

def plot_category_pie(expense_by_category: Dict[str, float]) -> Optional[go.Figure]:
    """Creates category pie chart."""
    if not expense_by_category:
        return None

    labels = list(expense_by_category.keys())
    values = list(expense_by_category.values())

    fig = px.pie(
        names=labels,
        values=values,
        title='Chi tiêu theo danh mục',
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hoverinfo='label+percent+value',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=0),
        height=250
    )

    return fig

# --- Initialization ---
def initialize_data():
    """Initializes session state from Google Sheets."""
    if 'transactions' not in st.session_state:
        st.session_state.transactions = get_transactions_from_sheet()

    # Update summary
    update_summary()
