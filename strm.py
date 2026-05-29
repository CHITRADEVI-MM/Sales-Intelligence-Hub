import streamlit as st
import pymysql
from datetime import date
import pandas as pd

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Sales Intelligence Hub", layout="wide")

# ------------------- DATABASE CONNECTION -------------------
def connect_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='12345',
        database='sales_db'
    )

# ------------------- AUTHENTICATION -------------------
def login_check(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    sql = """
        SELECT user_id, username, email, branch_id, role
        FROM users
        WHERE username = %s AND password = %s
    """
    cursor.execute(sql, (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

# ------------------- DATA FUNCTIONS -------------------
def get_branches():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT branch_id, branch_name FROM branches ORDER BY branch_name")
    branches = cursor.fetchall()
    conn.close()
    return branches

def get_products():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT product_name FROM customer_sales ORDER BY product_name")
    products = [p[0] for p in cursor.fetchall()]
    conn.close()
    return products

def get_branch_name(branch_id):
    if not branch_id:
        return "All Branches"
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT branch_name FROM branches WHERE branch_id = %s", (branch_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Unknown"

def get_dashboard_totals(start_date, end_date, branch_name, product_name, user_role, user_branch_id):
    conn = connect_db()
    cursor = conn.cursor()

    sql = """
        SELECT
            SUM(cs.gross_sales) AS total_sales,
            COALESCE(SUM(ps.amount_paid), 0) AS total_received,
            SUM(cs.pending_amount) AS total_pending
        FROM customer_sales cs
        LEFT JOIN branches b ON cs.branch_id = b.branch_id
        LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
        WHERE 1=1
    """
    params = []

    if user_role == 'Admin' and user_branch_id:
        sql += " AND cs.branch_id = %s"
        params.append(user_branch_id)
    if start_date:
        sql += " AND cs.sale_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND cs.sale_date <= %s"
        params.append(end_date)
    if branch_name!= "All Branches":
        sql += " AND b.branch_name = %s"
        params.append(branch_name)
    if product_name!= "All Products":
        sql += " AND cs.product_name = %s"
        params.append(product_name)

    cursor.execute(sql, params)
    result = cursor.fetchone()
    conn.close()

    gross = result[0] if result[0] else 0
    received = result[1] if result[1] else 0
    pending = result[2] if result[2] else 0
    return gross, received, pending

def get_sales_list(start_date, end_date, branch_name, product_name, user_role, user_branch_id):
    conn = connect_db()
    cursor = conn.cursor()

    sql = """
        SELECT
            cs.sale_id,
            b.branch_name,
            cs.customer_name,
            cs.mobile_number,
            cs.product_name,
            cs.gross_sales,
            COALESCE(SUM(ps.amount_paid), 0) AS amount_paid,
            cs.pending_amount,
            cs.payment_status,
            cs.sale_date
        FROM customer_sales cs
        LEFT JOIN branches b ON cs.branch_id = b.branch_id
        LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
        WHERE 1=1
    """
    params = []

    if user_role == 'Admin' and user_branch_id:
        sql += " AND cs.branch_id = %s"
        params.append(user_branch_id)
    if start_date:
        sql += " AND cs.sale_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND cs.sale_date <= %s"
        params.append(end_date)
    if branch_name!= "All Branches":
        sql += " AND b.branch_name = %s"
        params.append(branch_name)
    if product_name!= "All Products":
        sql += " AND cs.product_name = %s"
        params.append(product_name)

    sql += " GROUP BY cs.sale_id ORDER BY cs.sale_date DESC"

    cursor.execute(sql, params)
    data = cursor.fetchall()
    conn.close()
    return data

def add_sale(branch_id, customer_name, mobile, product_name, gross_sales, sale_date):
    conn = connect_db()
    cursor = conn.cursor()
    sql = """
        INSERT INTO customer_sales
        (branch_id, customer_name, mobile_number, product_name, gross_sales, sale_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (branch_id, customer_name, mobile, product_name, gross_sales, sale_date))
    sale_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sale_id

def add_payment(sale_id, payment_date, amount_paid, payment_method):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (sale_id, payment_date, amount_paid, payment_method))
        conn.commit()
        conn.close()
        return True, "Payment recorded successfully"
    except Exception as e:
        conn.close()
        return False, str(e)

def get_open_sales(user_role, user_branch_id):
    conn = connect_db()
    cursor = conn.cursor()
    if user_role == 'Admin' and user_branch_id:
        sql = """
            SELECT sale_id, customer_name, gross_sales, pending_amount
            FROM customer_sales
            WHERE payment_status = 'Open' AND branch_id = %s
            ORDER BY sale_date DESC
        """
        cursor.execute(sql, (user_branch_id,))
    else:
        sql = """
            SELECT sale_id, customer_name, gross_sales, pending_amount
            FROM customer_sales
            WHERE payment_status = 'Open'
            ORDER BY sale_date DESC
        """
        cursor.execute(sql)
    data = cursor.fetchall()
    conn.close()
    return data

def get_payments_for_sale(sale_id):
    conn = connect_db()
    cursor = conn.cursor()
    sql = """
        SELECT payment_id, payment_date, amount_paid, payment_method
        FROM payment_splits
        WHERE sale_id = %s
        ORDER BY payment_date DESC
    """
    cursor.execute(sql, (sale_id,))
    data = cursor.fetchall()
    conn.close()
    return data

# ------------------- SESSION STATE -------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ------------------- LOGIN PAGE -------------------
if not st.session_state.logged_in:
    st.title("Sales Intelligence Hub")
    st.subheader("Login to Continue")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_check(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.email = user[2]
            st.session_state.branch_id = user[3]
            st.session_state.role = user[4]
            st.rerun()
        else:
            st.error("Invalid username or password")

# MAIN APPLICATION
else:
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.write(f"Role: {st.session_state.role}")
    st.sidebar.write(f"Branch: {get_branch_name(st.session_state.branch_id)}")
    st.sidebar.divider()

    # LEFT SIDE NAVIGATION
    menu = st.sidebar.radio("Modules", ["Dashboard", "Add Sale", "Add Payment", "SQL Analysis"]) 

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # ------------------- DASHBOARD -------------------
    if menu == "Dashboard":
        st.title("Sales Dashboard")

        col_main, col_filter = st.columns([3, 1])

        with col_filter:
            st.subheader("Filters")
            start_date = st.date_input("Start Date", value=None)
            end_date = st.date_input("End Date", value=None)

            branches = ["All Branches"] + [b[1] for b in get_branches()]
            branch_filter = st.selectbox("Branch", branches)

            products = ["All Products"] + get_products()
            product_filter = st.selectbox("Product", products)

        with col_main:
            gross, received, pending = get_dashboard_totals(
                start_date, end_date, branch_filter, product_filter,
                st.session_state.role, st.session_state.branch_id
            )
            collection_rate = (received / gross * 100) if gross > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Sales", f"Rs. {gross:,.2f}")
            c2.metric("Amount Received", f"Rs. {received:,.2f}")
            c3.metric("Amount Pending", f"Rs. {pending:,.2f}")
            c4.metric("Collection Rate", f"{collection_rate:.2f}%")

            st.divider()
            st.subheader("Sales Records")

            sales_data = get_sales_list(
                start_date, end_date, branch_filter, product_filter,
                st.session_state.role, st.session_state.branch_id
            )

            if sales_data:
                df = pd.DataFrame(sales_data, columns=[
                    "Sale ID", "Branch", "Customer", "Mobile", "Product", "Gross Amount",
                    "Paid Amount", "Pending Amount", "Status", "Sale Date"
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "sales_report.csv", "text/csv")
            else:
                st.info("No records found for selected filters")

    # ------------------- ADD SALE -------------------
    if menu == "Add Sale":
        st.title("Add New Sale")

        branches = get_branches()
        branch_map = {name: id for id, name in branches}

        if st.session_state.role == 'Super Admin':
            branch_name = st.selectbox("Branch", list(branch_map.keys()))
            branch_id = branch_map[branch_name]
        else:
            branch_id = st.session_state.branch_id
            branch_name = get_branch_name(branch_id)
            st.text_input("Branch", value=branch_name, disabled=True)

        customer_name = st.text_input("Customer Name")
        mobile = st.text_input("Mobile Number", max_chars=10)
        product_list = ["DATA SCI", "CLOUD", "AI/ML", "WEB DEV", "CYBERSEC", "BA", "DA", "FSD", "DS"]
        product_name = st.selectbox("Product Name", product_list)
        gross_amount = st.number_input("Gross Sales Amount", min_value=0.0, step=100.0)
        sale_date = st.date_input("Sale Date", value=date.today())

        if st.button("Save Sale", type="primary"):
            if customer_name and mobile and gross_amount > 0:
                try:
                    sale_id = add_sale(branch_id, customer_name, mobile, product_name, gross_amount, sale_date)
                    st.success(f"Sale saved successfully. Sale ID: {sale_id}")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please fill all required fields")

    # ------------------- ADD PAYMENT -------------------
    if menu == "Add Payment":
        st.title("Record Payment")

        open_sales = get_open_sales(st.session_state.role, st.session_state.branch_id)

        if open_sales:
            sale_dict = {f"ID {s[0]} - {s[1]} | Pending: Rs.{s[3]:,.0f}": s[0] for s in open_sales}
            selected = st.selectbox("Select Sale", list(sale_dict.keys()))
            sale_id = sale_dict[selected]

            st.subheader("Payment History")
            payments = get_payments_for_sale(sale_id)
            if payments:
                pay_df = pd.DataFrame(payments, columns=["Payment ID", "Date", "Amount", "Method"])
                st.dataframe(pay_df, use_container_width=True, hide_index=True)
                total_paid = pay_df['Amount'].sum()
                st.write(f"Total Paid for this Sale: Rs. {total_paid:,.2f}")
            else:
                st.info("No payments recorded yet")

            st.divider()
            st.subheader("Add New Payment")

            pay_date = st.date_input("Payment Date", value=date.today())
            pay_amount = st.number_input("Amount", min_value=0.0, step=100.0)
            pay_method = st.selectbox("Payment Method", ["Cash", "Card", "UPI", "Bank Transfer"])

            if st.button("Save Payment", type="primary"):
                if pay_amount > 0:
                    success, msg = add_payment(sale_id, pay_date, pay_amount, pay_method)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
                else:
                    st.error("Amount must be greater than zero")
        else:
            st.info("No open sales available")

    # ------------------- SQL ANALYSIS -------------------
    if menu == "SQL Analysis":
        st.title("SQL Analysis")

        queries = {
            "1. Retrieve all records from customer_sales table": "SELECT * FROM customer_sales",
            "2. Retrieve all records from branches table": "SELECT * FROM branches",
            "3. Retrieve all records from payment_splits table": "SELECT * FROM payment_splits",
            "4. Display all sales with status = Open": "SELECT * FROM customer_sales WHERE payment_status = 'Open'",
            "5. Calculate total gross sales across all branches": "SELECT SUM(gross_sales) AS Total_Gross_Sales FROM customer_sales",
            "6. Calculate total received amount across all sales": "SELECT SUM(received_amount) AS Total_Received FROM customer_sales",
            "7. Calculate total pending amount across all sales": "SELECT SUM(pending_amount) AS Total_Pending FROM customer_sales",
            "8. Count total number of sales per branch": "SELECT b.branch_name, COUNT(cs.sale_id) AS Sales_Count FROM branches b LEFT JOIN customer_sales cs ON b.branch_id = cs.branch_id GROUP BY b.branch_name",
            "9. Retrieve sales details along with branch name": "SELECT cs.sale_id, cs.customer_name, cs.gross_sales, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id",
            "10. Sales details with total payment received": "SELECT cs.sale_id, cs.customer_name, cs.gross_sales, COALESCE(SUM(ps.amount_paid), 0) AS Total_Paid FROM customer_sales cs LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id GROUP BY cs.sale_id, cs.customer_name, cs.gross_sales",
            "11. Branch-wise total gross sales using JOIN": "SELECT b.branch_name, SUM(cs.gross_sales) AS Total_Gross FROM branches b JOIN customer_sales cs ON b.branch_id = cs.branch_id GROUP BY b.branch_name",
            "12. Sales along with payment method used": "SELECT cs.sale_id, cs.customer_name, ps.payment_method, ps.amount_paid FROM customer_sales cs JOIN payment_splits ps ON cs.sale_id = ps.sale_id",
            "13. Sales where pending amount greater than 5000": "SELECT sale_id, customer_name, pending_amount FROM customer_sales WHERE pending_amount > 5000",
            "14. Top 3 highest gross sales": "SELECT sale_id, customer_name, gross_sales FROM customer_sales ORDER BY gross_sales DESC LIMIT 3",
            "15. Branch with highest total gross sales": "SELECT b.branch_name, SUM(cs.gross_sales) AS Total_Gross FROM branches b JOIN customer_sales cs ON b.branch_id = cs.branch_id GROUP BY b.branch_name ORDER BY Total_Gross DESC LIMIT 1"
        }

        selected_query = st.selectbox("Select Predefined Query", list(queries.keys()))
        st.code(queries[selected_query], language="sql")

        if st.button("Run Query", type="primary"):
            try:
                conn = connect_db()
                query_to_run = queries[selected_query]

                if st.session_state.role == 'Admin':
                    if "customer_sales cs" in query_to_run and "WHERE" in query_to_run:
                        query_to_run = query_to_run.replace("WHERE", f"WHERE cs.branch_id={st.session_state.branch_id} AND", 1)
                    elif "customer_sales" in query_to_run and "WHERE" not in query_to_run and "JOIN" not in query_to_run:
                        query_to_run += f" WHERE branch_id={st.session_state.branch_id}"
                    elif "JOIN customer_sales cs" in query_to_run and "WHERE" not in query_to_run:
                        query_to_run += f" WHERE cs.branch_id={st.session_state.branch_id}"

                df = pd.read_sql_query(query_to_run, conn)
                conn.close()
                st.success(f"Query executed successfully. {len(df)} rows returned")
                st.dataframe(df, use_container_width=True, hide_index=True)

                if not df.empty:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Result as CSV", csv, "query_result.csv", "text/csv")

            except Exception as e:
                st.error(f"Query Error: {e}")

        st.divider()
        st.subheader("Custom SQL Query")
        custom_query = st.text_area(
            "Enter your SQL query here",
            height=150,
            placeholder="SELECT * FROM customer_sales LIMIT 10"
        )

        if st.button("Execute Custom Query"):
            if custom_query.strip():
                try:
                    conn = connect_db()
                    df = pd.read_sql_query(custom_query, conn)
                    conn.close()
                    st.success(f"Custom query executed. {len(df)} rows returned")
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    if not df.empty:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download Result", csv, "custom_query_result.csv", "text/csv")

                except Exception as e:
                    st.error(f"Query Error: {e}")
            else:
                st.warning("Please enter a SQL query")