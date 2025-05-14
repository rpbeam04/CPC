import streamlit as st
import pandas as pd
from demand_forecast import smoothing
import os

# Labor Forecasting App
st.title("JR286 Labor Forecasting")

# Sidebar
st.sidebar.header("Sidebar Options")
st.sidebar.write("Use the sidebar to adjust additional settings.")

# Use the sidebar to switch between pages
page = st.sidebar.selectbox("Select Page", ["Forecasting", "Productivity Report"])

if page == "Forecasting":
    # Section 1: Demand Forecasting
    st.header("Step 1: Demand Forecasting")
    st.write("Given a dataset of past orders and qunatity, forecast future demand using a mathematical model.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upload Data")
        st.write("Data should be a monthly time series dataset with order numbers and total quantity.")
        demand_data = st.file_uploader("Upload Demand Data", type=["csv", "xlsx"])    
    with col2:
        st.subheader("Model Selection")
        st.write("Select the model for demand forecasting.")
        model = st.selectbox("Select Brand/Model", ["Nike Smoothing", "Dakine Smoothing"])

    if demand_data is not None:
        if demand_data.name.endswith('.csv'):
            demand_data = pd.read_csv(demand_data)
        else:
            demand_data = pd.read_excel(demand_data)

        st.write(f"Model selected: {model}")

        if model == "Nike Smoothing":
            st.write("Demand forecasting using Nike Smoothing model, which is a 12-month" \
            "exponential smooething model with log-transformation.")
            
        elif model == "Dakine Smoothing":
            st.write("Demand forecasting using Dakine Smoothing model, which is a 12-month" \
            "exponential smoothing model with log-transformation.")
            
        order_plot, qty_plot, order_table, qty_table = smoothing(demand_data)
        if type(order_plot) == str and qty_plot == 0:
            st.write(order_plot)
            
        o_col, q_col = st.columns(2)
        with o_col:
            st.image(order_plot)
            st.dataframe(order_table, use_container_width=True)
        with q_col:
            st.image(qty_plot)
            st.dataframe(qty_table, use_container_width=True)

        if os.path.exists(order_plot):
            os.remove(order_plot)
        if os.path.exists(qty_plot):
            os.remove(qty_plot)

    # Transaction Forecasting
    st.header("Step 2: Forecast Transaction Counts")
    st.write("Use the forecasts from the previous step or input your own numbers to calculate the neccesary transactions to handle demand.")

    col1, col2 = st.columns(2)
    with col1:
        orders = st.text_input("Enter the number of orders forecasted:")
    with col2:
        quantity = st.text_input("Enter the total quantity forecasted:")

    if orders and quantity:
        try:
            orders = float(orders)
            quantity = float(quantity)
            with col1:
                st.write(f"Forecasted Orders: {orders}")
            with col2:
                st.write(f"Forecasted Quantity: {quantity}")

            st.dataframe({
                "Forecasted Orders": [str(orders), "This code is currently under construction."],
                "Forecasted Quantity": [str(quantity), ""]
            }, use_container_width=True)

        except ValueError:
            st.write("Please enter valid numeric values for orders and quantity.")

    # Labor Optimization Model
    st.header("Step 3: Labor Optimization Model")
    st.write("Use the data from the transaction forecast with this model to determine the number of employees needed by brand/position.")

    col1, col2 = st.columns(2)
    with col1:
        transactions = st.file_uploader("Upload Trnasaction Forecast", type=["csv", "xlsx"])
    with col2:
        employees = st.file_uploader("Upload Employee Transaction Averages", type=["csv", "xlsx"])

    if transactions is not None and employees is not None:
        if transactions.name.endswith('.csv'):
            transactions = pd.read_csv(transactions)
        else:
            transactions = pd.read_excel(transactions)

        if employees.name.endswith('.csv'):
            employees = pd.read_csv(employees)
        else:
            employees = pd.read_excel(employees)

        st.write("Transaction and employee data uploaded successfully.")
        st.write("This code is currently under construction.")

if page == "Productivity Report":
    # Section 2: Productivity Report
    st.header("Part 2: Productivity Report")
    st.write("This section will provide a productivity report based on the employee data.")