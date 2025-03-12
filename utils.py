import pandas as pd
import streamlit as st
from datetime import datetime
import uuid
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Literal, Optional, TypedDict, Union
import sqlite3
from supabase import create_client, Client  # Import Supabase

# --- Data Types ---
class Transaction(TypedDict):
    id: str
    type: Literal['income', 'expense']
    amount: float
    description: str
    category: str
    date: str
    image_url: Optional[str]  # Add image_url

# --- Constants ---
CATEGORIES = {
    'income': ['Đóng phí', 'Tài trợ', 'Khác'],
    'expense': ['Sân bóng', 'Thiết bị', 'Nước uống', 'Đồng phục', 'Khác']
}

# --- Utility Functions ---
def format_currency(amount: float) -> str:
    return f"{amount:,.0f} VNĐ"

# --- Supabase Configuration ---
@st.cache_resource
def get_supabase_client():
    supabase_url = st.secrets["SUPABASE_URL"]  # CORRECT!
    supabase_key = st.secrets["SUPABASE_KEY"]
    return create_client(supabase_url, supabase_key)

# --- Database Configuration (SQLite) ---
DB_FILE = "data.db"

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        print("Successfully connected to SQLite database")  # Debug
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {e}")
    return conn

def create_table(conn):
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        category TEXT,
        date TEXT,
        image_url TEXT
    );
    """
    try:
        c = conn.cursor()
        c.execute(sql_create_table)
        print("Successfully created transactions table (if it didn't exist)") # Debug
    except sqlite3.Error as e:
        print(f"Error creating transactions table: {e}")

def insert_transaction(conn, transaction):
    sql = """
    INSERT INTO transactions(id, type, amount, description, category, date, image_url)
    VALUES(?,?,?,?,?,?,?)
    """
    cur = conn.cursor()
    cur.execute(sql, transaction)
    conn.commit()
    last_row_id = cur.lastrowid  # Get ID for the new row
    conn.close()  # Close connection *after* getting lastrowid
    print(f"✅ Saved to database transaction ID: {transaction[0]}")
    return last_row_id

def select_all_transactions(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()
    return rows

def delete_transaction_from_db(conn, transaction_id):
    sql = "DELETE FROM transactions WHERE id=?"
    cur = conn.cursor()
    cur.execute(sql, (transaction_id,))
    conn.commit()

def fetch_transactions_from_db():
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        transactions = select_all_transactions(conn)
        conn.close()
        print(f"✅ Loaded {len(transactions)} transactions from the database") # Debug
        return [
            {'id': row[0], 'type': row[1], 'amount': row[2], 'description': row[3], 'category': row[4], 'date': row[5],
             'image_url': row[6]}
            for row in transactions
        ]
    else:
        print(f"❌ Could not load database {DB_FILE}")
        return []

# --- Supabase Storage Functions ---
def upload_file_to_supabase(supabase_client: Client, bucket_name: str, file_path: str, file_object):
    try:
        res = supabase_client.storage.from_(bucket_name).upload(file_path, file_object, file_options={'upsert': True})  # Add upsert for overwriting
        return res
    except Exception as e:
        return str(e)

def get_file_url_from_supabase(supabase_client: Client, bucket_name: str, file_path: str):
    try:
        url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
        return url
    except Exception as e:
        return str(e)

# --- Transaction Management Functions ---
def add_transaction(transaction_data: Dict, image_file=None) -> None:
    """Add a new transaction to database and session state."""

    transaction_id = str(uuid.uuid4())
    supabase_client = get_supabase_client()
    bucket_name = "team-fund-images"  # Replace if different

    image_url = None  # Initialize image_url

    if image_file:
        try:
            # Upload image to Supabase Storage
            file_name = f"{transaction_id}_{image_file.name}"  # Unique file name
            upload_result = upload_file_to_supabase(supabase_client, bucket_name, file_name, image_file.read())

            if not isinstance(upload_result, str):  # Check for successful upload
                # Get public URL of the image
                image_url = get_file_url_from_supabase(supabase_client, bucket_name, file_name)
            else:
                st.error(f"Image upload failed: {upload_result}")
                image_url = None  # Set image_url to None if upload fails
        except Exception as e:
            st.error(f"Image processing error: {e}")
            image_url = None
    # Create the transaction object
    transaction = {
        'id': transaction_id,
        'type': transaction_data['type'],
        'amount': float(transaction_data['amount']),
        'description': transaction_data['description'],
        'category': transaction_data['category'],
        'date': transaction_data['date'],
        'image_url': image_url  # Store image URL or None
    }

    # Add to SQLite database
    conn = create_connection()
    if conn is not None:
        insert_transaction(conn, (transaction['id'], transaction['type'], transaction['amount'], transaction['description'], transaction['category'], transaction['date'], transaction['image_url']))
        conn.close()
    else:
        st.error("Failed to connect to SQLite database.")

    # Update session state (add to the beginning)
    st.session_state.transactions.insert(0, transaction)

    # Update summary
    update_summary()

def delete_transaction(transaction_id: str) -> None:
    """Delete a transaction from database and session state."""
    conn = create_connection()
    if conn is not None:
        delete_transaction_from_db(conn, transaction_id)
        conn.close()

    st.session_state.transactions = [t for t in st.session_state.transactions if t['id'] != transaction_id]

    # Update summary
    update_summary()

def update_summary() -> None:
    """Update summary information."""
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
    """Get a list of all months in the data."""
    months = set()

    for t in st.session_state.transactions:
        month = t['date'][:7]  # YYYY-MM
        months.add(month)

    return sorted(list(months), reverse=True)

def get_monthly_report(month: str) -> Dict:
    """Get the report for a specific month."""
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
    """Get expenses by category."""
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
    """Convert transaction list to DataFrame."""
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
    """Create income/expense bar chart."""
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
    """Create category pie chart."""
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
    """Initialize session state and database."""
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        conn.close()

    if 'transactions' not in st.session_state:
        st.session_state.transactions = fetch_transactions_from_db()

    # Update summary
    update_summary()
