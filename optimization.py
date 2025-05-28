import pandas as pd
import numpy as np
from scipy.optimize import linprog

# cleaning forecast columns to allow for retrieval

def clean_forecast_columns(df):
    cleaned_cols = []  # initialize cleaned cols
    col_map = {}       # initialize col mapping
    for col in df.columns:
        if col == "Month":
            cleaned_cols.append("Month")
            col_map[col] = "Month"  # keep month as is
        elif "_transactions" in col:
            try:
                trans_type = int(col.replace("_transactions", ""))
                cleaned_cols.append(trans_type)
                col_map[col] = trans_type  # removing the _transactions from the col name and making the number an int
            except ValueError:
                continue  # skip columns like "Total Transactions" bc gives error
    df = df[col_map.keys()]
    df.columns = cleaned_cols  # make the cols clean
    return df  # return df with cleaned cols


# OPTIMIZATION FUNCTION

def optimize_staffing_from_dataframe(df_capabilities, df_forecast, row_index=0):  # taking the dfs and row_index (month)

    roles = df_capabilities['Position'].tolist()  # getting role names
    capability_matrix = df_capabilities.drop(columns='Position')  # dropping position col to get numeric transaction capabilities
    transaction_types = capability_matrix.columns.astype(int).tolist()  # extracting types as ints

    C = capability_matrix.to_numpy()  # C[i][j] = number of type-j transactions one employee of role i can complete per month
    R = len(roles)  # number of roles

    # getting demand for selected month
    row = df_forecast.iloc[row_index]
    # making dictionary for required where: (keys = transaction type IDs) and (values = number of transactions needed for that type)
    required = {
        int(col): row[col]
        for col in df_forecast.columns if col != "Month" and not pd.isna(row[col])
    }

    # finding transaction types appearing in both the capabilities and the forecast (safety check so that
    # using transaction types that are both needed and possible to fulfill)
    common_types = sorted(set(transaction_types).intersection(set(required)))
    if not common_types:
        return {}, 0, False

    # subsetting the capability matrix C to only the needed transaction types
    # building demand vector D with one value per transaction type
    type_indices = [transaction_types.index(t) for t in common_types]
    C_reduced = C[:, type_indices]
    D = np.array([required[t] for t in common_types])

    # building linear program
    A_ub = -C_reduced.T
    b_ub = -D
    c = np.ones(R)
    bounds = [(0, None)] * R

    # solving linear program
    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    # output
    if res.success:
        staffing_solution = {
            roles[i]: int(np.ceil(res.x[i])) for i in range(R) if res.x[i] > 1e-3
        }
        total_employees = int(np.ceil(sum(res.x)))
        return staffing_solution, total_employees, True
    else:
        return {}, 0, False

def optimization_model(brands, forecasts, capabilities, row_index=0):
    # processing each brand
    staffings = []
    success = True
    totals = []
    
    for brand_name, df_forecast, df_cap in zip(brands, forecasts, capabilities):
        df_clean = clean_forecast_columns(df_forecast)

        staffing, total, success = optimize_staffing_from_dataframe(df_cap, df_clean, row_index=row_index)
        
        if not success:
            return [], [], False
        else:
            staffings.append(staffing)
            totals.append(total)
    
    return staffings, totals, True
    