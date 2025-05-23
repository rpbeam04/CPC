import pandas as pd
import numpy as np
from datetime import datetime
import os

#Forecast 400 Quantity Based on Brand Shares
def forecast_400_from_shares(forecast_451, forecast_900):
    df400 = pd.read_csv('historical_breakdown_400_summary.csv')
    df451 = pd.read_csv('historical_breakdown_451_summary.csv')
    df900 = pd.read_csv('historical_breakdown_900_summary.csv')
    months = ['2024-10-01','2024-11-01','2024-12-01']
    s400 = df400[df400['Month'].isin(months)]['total_quantity']
    s451 = df451[df451['Month'].isin(months)]['total_quantity']
    s900 = df900[df900['Month'].isin(months)]['total_quantity']

    df_share = pd.DataFrame({'400':s400.values, '451':s451.values, '900':s900.values})
    df_share['total'] = df_share.sum(axis=1)
    df_share['share400'] = df_share['400'] / df_share['total']

    pattern = (df_share['share400'] / df_share['share400'].sum()).tolist() * 4
    pattern = pattern[:12]
    combined = sum(forecast_451) + sum(forecast_900)
    return [int(p * combined) for p in pattern]

def forecast_400_constant_ratio(forecast_451, forecast_900):
    # load history
    df400 = pd.read_csv('historical_breakdown_400_summary.csv')
    df451 = pd.read_csv('historical_breakdown_451_summary.csv')
    df900 = pd.read_csv('historical_breakdown_900_summary.csv')

    # sum the same three months
    months = ['2024-10-01','2024-11-01','2024-12-01']
    tot400 = df400.loc[df400['Month'].isin(months), 'total_quantity'].sum()
    tot451 = df451.loc[df451['Month'].isin(months), 'total_quantity'].sum()
    tot900 = df900.loc[df900['Month'].isin(months), 'total_quantity'].sum()

    ratio = tot400 / (tot451 + tot900)  # e.g. 0.055

    combined = np.array(forecast_451) + np.array(forecast_900)
    result   = (ratio * combined).round().astype(int).tolist()
    return result

#Project Transactions for Each Brand
def project_transactions(file_path, forecast_values, anchor_type='341'):
    df = pd.read_csv(file_path, low_memory=False)
    df['date'] = pd.to_datetime(df['date'])
    df['Month'] = df['date'].dt.to_period('M')

    txn_cols = [c for c in df.columns if c.endswith('_transactions')]
    qty_cols = [c for c in df.columns if c.endswith('_quantity')]

    total_txn = df[txn_cols].sum().sum()
    anchor_txn = df[f'{anchor_type}_transactions'].sum()
    anchor_qty = df[f'{anchor_type}_quantity'].sum()

    avg_qty_per_anchor = anchor_qty / anchor_txn
    anchor_share = anchor_txn / total_txn
    other_total = total_txn - anchor_txn

    shares = {t: df[f'{t}_transactions'].sum() / other_total
              for t in sorted(set(c.split('_')[0] for c in txn_cols) - {anchor_type})}

    months = pd.date_range('2025-01-01', periods=12, freq='MS')
    df_out = pd.DataFrame({'Month': months.strftime('%Y-%m-%d')})
    df_out[f'{anchor_type}_transactions'] = [v / avg_qty_per_anchor for v in forecast_values]
    df_out['Total Transactions'] = df_out[f'{anchor_type}_transactions'] / anchor_share

    for t, share in shares.items():
        df_out[f'{t}_transactions'] = (df_out['Total Transactions'] - df_out[f'{anchor_type}_transactions']) * share

    # Round transactions to integers
    txn_cols_out = [c for c in df_out.columns if c != 'Month']
    df_out[txn_cols_out] = df_out[txn_cols_out].round(0).astype(int)

    df_out.to_csv(f'projected_summary_{file_path.replace(".csv","")}.csv', index=False)
    return df_out

#Forecast No-Brand Transactions by Type
def forecast_no_brand_transactions(f451, f900, f400):
    df_no = pd.read_csv('no_brand_summary.csv', low_memory=False)
    df_no['date'] = pd.to_datetime(df_no['date'])
    df_no['Month'] = df_no['date'].dt.to_period('M').astype(str)
    df_no = df_no[df_no['Month'].isin(['2024-10','2024-11','2024-12'])]

    txn_cols = [c for c in df_no.columns if c.endswith('_transactions')]
    df_grp = df_no.groupby('Month')[txn_cols].sum()
    df_grp['total_no'] = df_grp.sum(axis=1)

    shares = {c: (df_grp[c] / df_grp['total_no']).mean() for c in txn_cols}

    # Read final projected brand transactions
    p451 = pd.read_csv('projected_summary_451_summary.csv')['Total Transactions']
    p900 = pd.read_csv('projected_summary_900_summary.csv')['Total Transactions']
    p400 = pd.read_csv('projected_summary_400_summary.csv')['Total Transactions']
    total_brand = p451 + p900 + p400

    hist_total = df_grp['total_no'].sum()
    brand_hist = sum([514877, 228341, 228831, 1689715, 1429982, 1500546, 1092, 972, 1134])
    ratio = hist_total / brand_hist

    df_f = pd.DataFrame({'Month': total_brand.index, 'total_no': (total_brand * ratio).round(0)})
    for c, s in shares.items():
        df_f[c] = (df_f['total_no'] * s).round(0)

    df_f.drop(columns='total_no', inplace=True)
    # Round to integers
    txn_cols_no = [c for c in df_f.columns if c != 'Month']
    df_f[txn_cols_no] = df_f[txn_cols_no].astype(int)

    df_f.to_csv('forecast_no_brand_transactions_by_type.csv', index=False)
    return df_f

def forecast_pipeline(summary_files, forecast_451, forecast_900):
    # === 1. Historical Summaries ===
    anchor_type = '341'

    for df in summary_files:
        df['date'] = pd.to_datetime(df['date'])
        df['Month'] = df['date'].dt.to_period('M')

        txn_cols = [c for c in df.columns if c.endswith('_transactions')]
        qty_cols = [c for c in df.columns if c.endswith('_quantity')]

        df['total_quantity'] = df[qty_cols].sum(axis=1)
        df['total_transactions'] = df[txn_cols].sum(axis=1)

        # Group and sum required columns
        cols_to_sum = ['total_quantity', 'total_transactions'] + qty_cols + txn_cols
        summary = (
            df.groupby('Month')[cols_to_sum]
            .sum()
            .reset_index()
        )

        # Add source column to indicate dataset
        summary['source'] = file.replace('.csv', '')

        # Format Month, reorder columns, and save
        summary['Month'] = summary['Month'].dt.to_timestamp().dt.strftime('%Y-%m-%d')
        cols_base = ['source', 'Month', 'total_quantity', 'total_transactions']
        cols_rest = [c for c in summary.columns if c not in cols_base]
        summary = summary[cols_base + cols_rest]

        summary.to_csv(f"historical_breakdown_{file.replace('.csv','')}.csv", index=False)

    # Nike (900) forecast for 4/2025-3/2026 = [1505719, 1203541, 1595364, 996914, 985506, 1107223, 1438985, 1150199, 1524656, 952731, 941827, 1058150]
    #Took actual order quantity for 1/2025, 2/2025, 3/2025, so it aligns with Dakine forecasting for 1/2025-12/2025

    # Generate 400 forecast from shares
    forecast_400 = forecast_400_from_shares(forecast_451, forecast_900)

    # Project transactions for each brand
    df_451 = project_transactions('451_summary.csv', forecast_451)
    df_900 = project_transactions('900_summary.csv', forecast_900)
    df_400 = project_transactions('400_summary.csv', forecast_400)

    # Forecast no-brand transactions using type shares
    df_no_brand = forecast_no_brand_transactions(forecast_451, forecast_900, forecast_400)

    # delete all csv files in current directory
    files = os.listdir('.')
    for file in files:
        if os.path.exists(file) and (file.endswith('.csv') or file.endswith('.xlsx')):
            os.remove(file)

    return df_400, df_451, df_900, df_no_brand
