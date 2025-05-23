import streamlit as st
import pandas as pd
from demand_forecast import smoothing
from orders_to_trans import forecast_pipeline
from optimization import optimization_model
import os

# Labor Forecasting App
st.title("JR286 Labor Forecasting")

# Sidebar
st.sidebar.header("Select an Interface")
st.sidebar.write("Use the dropdown to change interfaces.")

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
        st.subheader("Sample Data")
        st.write("Please reference the provided documentation for a comprehensive breakdown of data syntax and formatting.")
        st.dataframe(pd.DataFrame({
            'Date': ["2025-01-01","2025-02-01","2025-03-01","2025-03-12"],
            '100_Orders': [10, 12, 6, 8],
            '100_Quantity': [100, 120, 60, 80],
            '200_Orders': [20, 22, 10, 14],
            '200_Quantity': [200, 220, 100, 140]
        }), use_container_width=True, hide_index=True)

    if demand_data is not None:
        if demand_data.name.endswith('.csv'):
            demand_data = pd.read_csv(demand_data)
        elif demand_data.name.endswith('.xlsx'):
            demand_data = pd.read_excel(demand_data)
        else:
            st.write("Please upload a valid CSV or Excel file.")

        order_plots, qty_plots, order_tables, qty_tables, brands = smoothing(demand_data)
        if type(order_plots) == str and qty_plots == 0:
            st.write(order_plots)
        else:
            for i,brand in enumerate(brands):
                st.subheader(f"Brand {brand} Forecast:")
                if i < len(order_plots):
                    o_col, q_col = st.columns(2)
                    with o_col:
                        st.image(order_plots[i])
                        st.dataframe(order_tables[i], use_container_width=True)
                    with q_col:
                        st.image(qty_plots[i])
                        st.dataframe(qty_tables[i], use_container_width=True)

                    if os.path.exists(order_plots[i]):
                        os.remove(order_plots[i])
                    if os.path.exists(qty_plots[i]):
                        os.remove(qty_plots[i])
                else:
                    st.write(f"Brand {brand} needs at least 12 months of data to forecast.")

    # Transaction Forecasting
    st.header("Step 2: Forecast Transaction Counts")
    st.write("Use the forecasts from the previous step or input your own numbers to calculate the neccesary transactions to handle demand.")
    
    col1, col2 = st.columns(2)
    with col1:
        sum400 = st.file_uploader("Upload 400 Summary", type=["csv", "xlsx"])
        sum451 = st.file_uploader("Upload 451 Summary", type=["csv", "xlsx"])
    with col2:
        sum900 = st.file_uploader("Upload 900 Summary", type=["csv", "xlsx"])
        quantity_451 = st.text_input("Enter the total quantity forecasted for 451:")
        quantity_900 = st.text_input("Enter the total quantity forecasted for 900:")

    if sum400 is not None and sum451 is not None and sum900 is not None and quantity_451 and quantity_900:
        try:
            quantity_451 = float(quantity_451)
            quantity_900 = float(quantity_900)

            out400, out451, out900, outNB = forecast_pipeline([sum400, sum451, sum900], [quantity_451]*12, [quantity_900]*12)
            
            st.write("Transactions for 400:")
            st.dataframe(out400)

            st.write("Transactions for 451:")
            st.dataframe(out451)

            st.write("Transactions for 900:")
            st.dataframe(out900)

            st.write("Transactions for No Brand:")
            st.dataframe(outNB)

        # except ValueError:
        #     st.write("Please enter valid numeric values for orders and quantity.")
        except Exception as e:
            st.write(f"An error occurred: {e}")

    # Labor Optimization Model
    st.header("Step 3: Labor Optimization Model")
    st.write("Use the data from the transaction forecast with this model to determine the number of employees needed by brand/position.")

    col1, col2 = st.columns(2)
    with col1:
        transactions = st.file_uploader("Upload Trnasaction Forecast", type=["csv", "xlsx"])
    with col2:
        employees = st.file_uploader("Upload Employee Capabilities", type=["csv", "xlsx"])

    if transactions is not None and employees is not None:
        if transactions.name.endswith('.csv'):
            transactions = pd.read_csv(transactions)
        else:
            transactions = pd.read_excel(transactions)

        if employees.name.endswith('.csv'):
            employees = pd.read_csv(employees)
        else:
            employees = pd.read_excel(employees)

        brands = ["test"]
        row_index = st.slider("Select Month", 1, len(transactions), 1) - 1

        if row_index:
            staffing, total, success = optimization_model(brands, [transactions], [employees], row_index)

            if success:
                for brand_name in brands:
                    st.write(f"\n{brand_name} Staffing Plan (Month {row_index}):")
                    for role, count in staffing.items():
                        st.write(f"  {role}: {count}")
                    st.write(f"Total Employees Needed: {total}")
            else:
                st.write("An error occurred while optimizing staffing.")

if page == "Productivity Report":
    # Section 2: Productivity Report
    st.header("Productivity Report")
    st.write("This section will provide a productivity report based on the employee data.")