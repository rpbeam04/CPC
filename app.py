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

        quantity = pd.DataFrame()

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

                    qty_tables: list[pd.DataFrame]
                    qty_tables[i].rename(columns = {'Forecasted Quantity': f'{brand}'}, inplace=True)
                    quantity = pd.concat([quantity, qty_tables[i][f'{brand}']], axis=1)

                    if os.path.exists(order_plots[i]):
                        os.remove(order_plots[i])
                    if os.path.exists(qty_plots[i]):
                        os.remove(qty_plots[i])
                else:
                    st.write(f"Brand {brand} needs at least 12 months of data to forecast.")

        st.subheader("Downloadable data for part 2:")
        quantity = quantity.reset_index(drop=False, names=['Date'])
        quantity = quantity.fillna(0)
        st.dataframe(quantity, use_container_width=True, hide_index=True)            

    # Section 2: Transaction Forecasting
    st.header("Step 2: Forecast Transaction Counts")
    st.write("Use the forecasts from the previous step or input your own numbers to calculate the neccesary transactions to handle demand.")
    
    col1, col2 = st.columns(2)
    with col1:
        summary = st.file_uploader("Upload Transaction Summary", type=["csv", "xlsx"])
    with col2:
        quantity = st.file_uploader("Upload Quantity Forecast", type=["csv", "xlsx"])
    if summary is not None and quantity is not None:
        try:
            if summary.name.endswith(".csv"):
                summary = pd.read_csv(summary)
            else:
                summary = pd.read_excel(summary)

            if quantity.name.endswith(".csv"):
                quantity = pd.read_csv(quantity)
            else:
                quantity = pd.read_excel(quantity)

            if "transactions" not in summary.columns or "quantity" not in summary.columns:
                st.write("ERROR: Transaction summary must have 'transactions' and 'quantity' columns.")
            elif not all(b in summary['brand'].astype(str).values for b in ["400", "451", "900", "no_brand"]):                
                st.write("ERROR: Transaction summary must have 'brand' column with brands 400, 451, 900, and no_brand.")
            
            elif "451" not in quantity.columns or "900" not in quantity.columns:
                st.write("ERROR: Brands '451' and '900' must be columns in the quantity forecast data.")
            elif "Date" not in quantity.columns:
                st.write("ERROR: Quantity forecast must have a 'Date' column.")
                        
            elif len(quantity["451"]) != 12 or len(quantity["900"]) != 12:
                st.write("ERROR: Quantity forecast must have 12 months of data for both brands '451' and '900'.")
            else:
                quantity = quantity.set_index("Date")

                forecast_451 = quantity["451"]
                forecast_900 = quantity["900"]
                
                out400, out451, out900, outNB = forecast_pipeline(summary, forecast_451, forecast_900)
                
                # add together the dataframes
                total = pd.concat([out400, out451, out900, outNB], axis=0)
                total = total.groupby('Month').sum().reset_index()
                total['Month'] = pd.to_datetime(total['Month']).dt.strftime('%Y-%m')
                total = total.rename(columns={'Month': 'Date'})
                total = total.fillna(0)

                st.write("Transactions for 400:")
                st.dataframe(out400, use_container_width=True, hide_index=True)

                st.write("Transactions for 451:")
                st.dataframe(out451, use_container_width=True, hide_index=True)

                st.write("Transactions for 900:")
                st.dataframe(out900, use_container_width=True, hide_index=True)

                st.write("Transactions for No Brand:")
                st.dataframe(outNB, use_container_width=True, hide_index=True)

                st.write("Total Transactions:")
                st.dataframe(total, use_container_width=True, hide_index=True)

        # except ValueError:
        #     st.write("Please enter valid numeric values for orders and quantity.")
        except Exception as e:
            st.write(f"An error occurred. Make sure files are the correct type and format. Error: {e}")
            raise e

    # Labor Optimization Model
    st.header("Step 3: Labor Optimization Model")
    st.write("Use the data from the transaction forecast with this model to determine the number of employees needed by brand/position.")

    # Use session state to persist data across reruns
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    if "employees" not in st.session_state:
        st.session_state.employees = []
    if "brands" not in st.session_state:
        st.session_state.brands = []

    with st.form("add_brand_form", clear_on_submit=True):
        brand = st.text_input("Brand Name")
        col1, col2 = st.columns(2)
        with col1:
            transaction = st.file_uploader("Upload Transaction Forecast", type=["csv", "xlsx"], key="transaction_file")
        with col2:
            employee = st.file_uploader("Upload Employee Capabilities", type=["csv", "xlsx"], key="employee_file")
        add_clicked = st.form_submit_button("Add Brand")
        if add_clicked:
            if brand and transaction is not None and employee is not None:
                if transaction.name.endswith('.csv'):
                    transaction_df = pd.read_csv(transaction)
                else:
                    transaction_df = pd.read_excel(transaction)
                if employee.name.endswith('.csv'):
                    employee_df = pd.read_csv(employee)
                else:
                    employee_df = pd.read_excel(employee)
                st.session_state.transactions.append(transaction_df)
                st.session_state.employees.append(employee_df)
                st.session_state.brands.append(brand)
                st.success(f"Added brand: {brand}")
            else:
                st.warning("Please provide a brand name and upload both files.")

    if st.session_state.brands:
        st.subheader("Brands Added:")
        for i, b in enumerate(st.session_state.brands):
            st.write(f"{i+1}. {b}")

    # Use session state to persist the selected month and optimization results
    if "opt_row_index" not in st.session_state:
        st.session_state.opt_row_index = 0
    if "opt_results" not in st.session_state:
        st.session_state.opt_results = None

    if st.session_state.transactions:
        run_opt = st.button("Run Optimization")

        row_index = st.slider("Select Month", 1, len(st.session_state.transactions[0]), 1, key="opt_slider") - 1

        # Only run optimization if button is clicked or slider is changed
        if run_opt or row_index != st.session_state.opt_row_index:
            st.session_state.opt_row_index = row_index
            staffings, totals, success = optimization_model(
                st.session_state.brands,
                st.session_state.transactions,
                st.session_state.employees,
                row_index
            )
            st.session_state.opt_results = (staffings, totals, success)

        # Display results if available
        if st.session_state.opt_results:
            staffings, totals, success = st.session_state.opt_results
            if success:
                for i, brand_name in enumerate(st.session_state.brands):
                    st.subheader(f"\n{brand_name} Staffing Plan (Month {st.session_state.opt_row_index}):")
                    col1, col2 = st.columns(2)
                    j = 0
                    for role, count in staffings[i].items():
                        if j / len(staffings[i]) < 0.5:
                            with col1:
                                st.write(f"  {role}: {count}")
                                j += 1
                        else:
                            with col2:
                                st.write(f"  {role}: {count}")
                                j += 1
                    st.write(f"Total Employees Needed: {totals[i]}")
            else:
                st.write("An error occurred while optimizing staffing.")
                
            st.subheader(f"Total Employees across All Brands: {sum(totals)}")

if page == "Productivity Report":
    # Section 2: Productivity Report
    st.header("Productivity Report")
    st.write("This section will provide a productivity report based on the employee data.")