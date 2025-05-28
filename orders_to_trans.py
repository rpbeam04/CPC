import pandas as pd
import numpy as np
from datetime import datetime
import os

def forecast_400_constant_ratio(summary, forecast_451, forecast_900):
    tot400 = summary.loc[summary['brand'] == '400', 'quantity'].sum()
    tot451 = summary.loc[summary['brand'] == '451', 'quantity'].sum()
    tot900 = summary.loc[summary['brand'] == '900', 'quantity'].sum()

    if tot451 + tot900 == 0:
        # If both 451 and 900 have no quantity, return a zero-filled list
        return [0] * len(forecast_451)

    ratio = tot400 / (tot451 + tot900)  # e.g. 0.055

    combined = np.array(forecast_451) + np.array(forecast_900)
    result   = (ratio * combined).round().astype(int).tolist()
    return result

#Project Transactions for Each Brand
def project_transactions(summary, brand, forecast_values, first_mo, anchor_type='341'):
    df = summary[summary['brand'] == str(brand)].copy()
    
    txn_cols = [c for c in df.columns if c.endswith('_transactions')]

    total_txn = df[txn_cols].sum().sum()
    anchor_txn = df[f'{anchor_type}_transactions'].sum()
    anchor_qty = df[f'{anchor_type}_quantity'].sum()

    avg_qty_per_anchor = anchor_qty / anchor_txn
    anchor_share = anchor_txn / total_txn
    other_total = total_txn - anchor_txn

    shares = {t: df[f'{t}_transactions'].sum() / other_total
              for t in sorted(set(c.split('_')[0] for c in txn_cols) - {anchor_type})}

    months = pd.date_range(first_mo, periods=12, freq='MS')
    df_out = pd.DataFrame({'Month': months.strftime('%Y-%m')})
    df_out[f'{anchor_type}_transactions'] = [v / avg_qty_per_anchor for v in forecast_values]
    df_out['Total Transactions'] = df_out[f'{anchor_type}_transactions'] / anchor_share

    for t, share in shares.items():
        df_out[f'{t}_transactions'] = (df_out['Total Transactions'] - df_out[f'{anchor_type}_transactions']) * share

    # Round transactions to integers
    txn_cols_out = [c for c in df_out.columns if c != 'Month']
    df_out[txn_cols_out] = df_out[txn_cols_out].round(0).astype(int)

    df_out.to_csv(f'projected_summary_{brand}.csv', index=False)
    return df_out

#Forecast No-Brand Transactions by Type
def forecast_no_brand_transactions(summary, first_mo):
    df_no = summary[summary['brand'] == 'no_brand'].copy()
    
    txn_cols = [c for c in df_no.columns if c.endswith('_transactions')]
    
    shares = {c: (list(df_no[c])[0] / list(df_no['transactions'])[0]) for c in txn_cols}

    for c in shares:
        if pd.isna(shares[c]):
            shares[c] = 0

    # Read final projected brand transactions
    p451 = pd.read_csv('projected_summary_451.csv')['Total Transactions']
    p900 = pd.read_csv('projected_summary_900.csv')['Total Transactions']
    p400 = pd.read_csv('projected_summary_400.csv')['Total Transactions']
    total_brand = p451 + p900 + p400

    hist_total = list(df_no['transactions'])[0]
    brand_hist = sum([514877, 228341, 228831, 1689715, 1429982, 1500546, 1092, 972, 1134])
    ratio = hist_total / brand_hist

    months = pd.date_range(first_mo, periods=12, freq='MS')
    df_f = pd.DataFrame({'Month': months.strftime("%Y-%m"), 'total_no': (total_brand * ratio).round(0)})
    for c, s in shares.items():
        df_f[c] = (df_f['total_no'] * s).round(0)

    df_f.drop(columns='total_no', inplace=True)
    # Round to integers
    txn_cols_no = [c for c in df_f.columns if c != 'Month']
    df_f[txn_cols_no] = df_f[txn_cols_no].astype(int)
    df_f['Total Transactions'] = df_f[txn_cols_no].sum(axis=1)

    df_f.to_csv('projected_summary_no_brand.csv', index=False)
    return df_f

def forecast_pipeline(summary, forecast_451, forecast_900):
    # Generate 400 forecast from shares
    forecast_400 = forecast_400_constant_ratio(summary, forecast_451, forecast_900)
    
    first_mo = str(forecast_451.index[0])

    # Project transactions for each brand
    df_451 = project_transactions(summary, '451', forecast_451, first_mo)
    df_900 = project_transactions(summary, '900', forecast_900, first_mo)
    df_400 = project_transactions(summary, '400', forecast_400, first_mo)

    # Forecast no-brand transactions using type shares
    df_no_brand = forecast_no_brand_transactions(summary, first_mo)

    # delete all csv files in current directory
    files = os.listdir('.')
    for file in files:
        if os.path.exists(file) and (file.endswith('.csv') or file.endswith('.xlsx')):
            os.remove(file)

    return df_400, df_451, df_900, df_no_brand
