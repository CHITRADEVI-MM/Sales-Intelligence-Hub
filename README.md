📊 Sales Intelligence Hub

A full-stack sales and payment tracking web application built with Python (Streamlit) and MySQL. Designed for multi-branch business operations, the application automates balance calculations, prevents overpayments using database triggers, enforces role-based access control, and provides real-time financial analytics.

🚀 Key Features

Role-Based Access Control (RBAC):

Super Admin: Full visibility and analytics across all branches (Coimbatore, Pune, Kolkata, Jaipur, Lucknow).

Branch Admin: Restricted access to view and manage sales and payments strictly for their assigned branch.

Automated Payment & Balance Tracking (MySQL Triggers):

Supports split/partial payments (UPI, Card, Cash, Bank Transfer) per customer sale.

AFTER INSERT, AFTER UPDATE, and AFTER DELETE triggers automatically recalculate received_amount, update the generated pending_amount column (gross_sales - received_amount), and flip payment_status between Open and Close.

Built-in overpayment protection (SIGNAL SQLSTATE '45000') blocks any payment that exceeds the total gross sale amount.

Interactive Sales Dashboard:

Live KPI cards displaying Total Sales, Amount Received, Amount Pending, and Collection Rate (%).

Dynamic filtering by Date Range, Branch, and Product (DATA SCI, CLOUD, AI/ML, WEB DEV, CYBERSEC, BA, DA), plus one-click CSV export.

SQL Analysis Module:

Allows evaluators and admins to run custom SELECT queries directly from the UI to inspect branch performance, payment mode breakdowns, and pending customer balances.

🛠️ Tech Stack

Frontend / Web Framework: Python, Streamlit

Database: MySQL (sales_db)

Database Connector & Data Handling: pymysql, pandas

🗄️ Database Schema (sales_db)

The relational database consists of four normalized tables:

branches – Stores branch IDs, branch names, and branch admin names.

users – Manages login credentials, assigned branch_id, and user roles (Super Admin / Admin).

customer_sales – Tracks customer details, product purchased, gross_sales, received_amount, a stored generated column pending_amount, and payment_status.

payment_splits – Records individual installment transactions linked to customer_sales via foreign key (ON DELETE CASCADE).

⚙️ Setup & Installation

1. Prerequisites

Python 3.8 or higher

MySQL Server & MySQL Workbench

2. Database Setup

Open MySQL Workbench and run the database creation script (CREATE DATABASE sales_db;), table definitions, and initial seed data (branches, users, customer_sales, payment_splits).

Execute the trigger script (trg_payment_insert, trg_payment_update, trg_payment_delete) using DELIMITER // so payment totals and statuses sync automatically.

3. Python Environment Setup

Clone or download this repository to your local machine:

git clone https://github.com/CHITRADEVI-MM/sales-intelligence-hub.git
cd sales-intelligence-hub


Install the required Python libraries:

pip install streamlit pymysql pandas


Update the database connection credentials (host, user, password, database='sales_db') in strm.py if needed.

4. Run the Application

streamlit run strm.py


The app will launch in your default browser at http://localhost:8501# Sales-Intelligence-Hub
