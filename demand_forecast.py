import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import os
import re

def smoothing(data: pd.DataFrame) -> tuple:    
    if 'Date' != list(data.columns)[0]:
        return "ERROR: First column of the data must be a valid 'Date' column.", 0, 0, 0, 0
    clen = len(data.columns)
    cols = list(data.columns)
    i = 1
    brands = []
    while i < clen:
        if not re.match(r'^[0-9]{3}_Orders$', cols[i]):
            return "ERROR: Data must contain '###_Orders' and '###_Quantity' columns in that order for each desired brand ###.", 0, 0, 0, 0
        if not re.match(r'^[0-9]{3}_Quantity$', cols[i + 1]):
            return "ERROR: Data must contain '###_Orders' and '###_Quantity' columns in that order for each desired brand ###.", 0, 0, 0, 0
        if cols[i][:3] != cols[i + 1][:3]:
            return "ERROR: Mismatch between brands for an Orders-Quantity column pair detected. Ensure columns are ordered correctly and grouped by brand.", 0, 0, 0, 0
        brands.append(cols[i][:3])
        i += 2

    try:
        data['Date'] = pd.to_datetime(data['Date'])
    except ValueError as e:
        return "ERROR: Unable to convert 'Date' column to datetime. Ensure the date format is a valid format in the 'Date' column.", 0, 0, 0, 0

    data = data.set_index('Date').asfreq('MS')

    # Temorary Images directory
    if not os.path.exists('Images'):
        os.makedirs('Images')

    order_plots = []
    qty_plots = []
    order_data = []
    qty_data = []
    invalid_brands = []

    # Forecasting total orders (log-transformed)
    for brand in brands:
        # Log-transforming the data
        tot_orders = data[f'{brand}_Orders'].copy()
        tot_qty = data[f'{brand}_Quantity'].copy()
        hist_orders = np.log(data[f'{brand}_Orders'] + 1)
        hist_qty = np.log(data[f'{brand}_Quantity'] + 1)

        # Trim to valid date range from beginning
        for d in data.index:
            if data[f'{brand}_Orders'][d] == 0 and data[f'{brand}_Quantity'][d] == 0:
                tot_orders = tot_orders[tot_orders.index > d]
                tot_qty = tot_qty[tot_qty.index > d]
                hist_orders = hist_orders[hist_orders.index > d]
                hist_qty = hist_qty[hist_qty.index > d]
            else:
                break

        # Trim from the end
        for d in reversed(data.index):
            if data[f'{brand}_Orders'][d] == 0 and data[f'{brand}_Quantity'][d] == 0:
                tot_orders = tot_orders[tot_orders.index < d]
                tot_qty = tot_qty[tot_qty.index < d]
                hist_orders = hist_orders[hist_orders.index < d]
                hist_qty = hist_qty[hist_qty.index < d]
            else:
                break

        if len(hist_orders) < 12 or len(hist_qty) < 12:
            invalid_brands.append(brand)
            continue

        # Forecasting total orders
        model_orders = ExponentialSmoothing(
            hist_orders,
            trend='add',
            seasonal='add',
            seasonal_periods=6,
            initialization_method='legacy-heuristic'
        ).fit(optimized=True)
        forecast_log_orders = model_orders.forecast(12)
        forecast_orders = np.exp(forecast_log_orders)
        forecast_orders = forecast_orders - 1
        avg_orders = forecast_orders.mean()

        # Creating forecasted plots
        plt.figure(figsize=(12, 5))
        plt.plot(tot_orders.index, tot_orders, label='Historical Orders', marker='o')
        plt.plot(forecast_orders.index, forecast_orders, label='Forecasted Orders', linestyle='--', marker='o')
        plt.axhline(avg_orders, color='gray', linestyle=':', label=f'Avg Forecast: {avg_orders:.0f}')
        plt.xlabel('Date')
        plt.ylabel('Total Orders')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        filename = f'Images/total_orders_forecast_{brand}.png'
        plt.savefig(filename)
        order_plots.append(filename)
        plt.close()

        order_data.append(pd.DataFrame({
                            'Forecasted Orders': forecast_orders,
                            'Average Delta': np.subtract(forecast_orders, avg_orders)
                        }))
        order_data[-1].index = order_data[-1].index.strftime('%Y-%m')

        # Forecasting order quantity (log-transformed)
        model_quantity = ExponentialSmoothing(
            hist_qty,
            trend='add',
            seasonal='add',
            seasonal_periods=6,
            initialization_method='legacy-heuristic'
        ).fit(optimized=True)
        forecast_log_quantity = model_quantity.forecast(12)
        forecast_quantity = np.exp(forecast_log_quantity)
        forecast_quantity = forecast_quantity - 1
        avg_quantity = forecast_quantity.mean()

        # Ploting order quantity
        plt.figure(figsize=(12, 5))
        plt.plot(tot_qty.index, tot_qty, label='Actual Quantity', marker='x')
        plt.plot(forecast_quantity.index, forecast_quantity, label='Forecast Quantity', linestyle='--', marker='x')
        plt.axhline(avg_quantity, color='purple', linestyle=':', label=f'Avg Forecast: {avg_quantity:.0f}')
        plt.xlabel('Date')
        plt.ylabel('Order Quantity')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        filename = f'Images/order_quantity_forecast_{brand}.png'
        plt.savefig(filename)
        qty_plots.append(filename)
        plt.close()

        qty_data.append(pd.DataFrame({
                    'Forecasted Quantity': forecast_quantity,
                    'Average Delta': np.subtract(forecast_quantity, avg_quantity)
                }))
        qty_data[-1].index = qty_data[-1].index.strftime('%Y-%m')

    brands = [brand for brand in brands if brand not in invalid_brands]
    
    return (
        order_plots,
        qty_plots,
        order_data,
        qty_data,
        brands + invalid_brands
    )