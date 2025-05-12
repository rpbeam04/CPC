import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import os

def smoothing(data: pd.DataFrame):    
    if list(data.columns) != ['Date', 'Total_Orders', 'Order_Quantity']: 
        return "ERROR: Dataframe must contain only 'Date', 'Total_Orders', and 'Order_Quantity' columns.", 0, 0, 0
    try:
        data['Date'] = pd.to_datetime(data['Date'])
    except ValueError as e:
        return "ERROR: Unable to convert 'Date' column to datetime. Ensure the date format is correct in the date column.", 0, 0, 0

    data = data.set_index('Date').asfreq('MS')

    # Log-transforming the data
    data['Log_Total_Orders'] = np.log(data['Total_Orders'])
    data['Log_Order_Quantity'] = np.log(data['Order_Quantity'])

    # Forecasting total orders (log-transformed)
    model_orders = ExponentialSmoothing(
        data['Log_Total_Orders'],
        trend='add',
        seasonal='add',
        seasonal_periods=6,
        initialization_method='legacy-heuristic'
    ).fit(optimized=True)
    forecast_log_orders = model_orders.forecast(12)
    forecast_orders = np.exp(forecast_log_orders)
    avg_orders = forecast_orders.mean()

    # Forecasting order quantity (log-transformed)
    model_quantity = ExponentialSmoothing(
        data['Log_Order_Quantity'],
        trend='add',
        seasonal='add',
        seasonal_periods=6,
        initialization_method='legacy-heuristic'
    ).fit(optimized=True)
    forecast_log_quantity = model_quantity.forecast(12)
    forecast_quantity = np.exp(forecast_log_quantity)
    avg_quantity = forecast_quantity.mean()

    # Temorary Images directory
    if not os.path.exists('Images'):
        os.makedirs('Images')

    # Creating forecasted plots
    plt.figure(figsize=(12, 5))
    plt.plot(data.index, data['Total_Orders'], label='Historical Orders', marker='o')
    plt.plot(forecast_orders.index, forecast_orders, label='Forecasted Orders', linestyle='--', marker='o')
    plt.axhline(avg_orders, color='gray', linestyle=':', label=f'Avg Forecast: {avg_orders:.0f}')
    plt.title('Log-Transformed Exponential Smoothing - Total Orders Forecast')
    plt.xlabel('Date')
    plt.ylabel('Total Orders')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('Images/total_orders_forecast_ENI.png')

    # Ploting order quantity
    plt.figure(figsize=(12, 5))
    plt.plot(data.index, data['Order_Quantity'], label='Actual Quantity', marker='x')
    plt.plot(forecast_quantity.index, forecast_quantity, label='Forecast Quantity', linestyle='--', marker='x')
    plt.axhline(avg_quantity, color='purple', linestyle=':', label=f'Avg Forecast: {avg_quantity:.0f}')
    plt.title('Log-Transformed Exponential Smoothing - Order Quantity Forecast')
    plt.xlabel('Date')
    plt.ylabel('Order Quantity')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('Images/order_quantity_forecast_ENI.png')

    order_data = pd.DataFrame({
                    'Forecasted Orders': forecast_orders,
                    'Avg Forecast Orders': avg_orders
                })
    qty_data = pd.DataFrame({
                    'Forecasted Quantity': forecast_quantity,
                    'Avg Forecast Quantity': avg_quantity
                })
    order_data.index = order_data.index.strftime('%Y-%m')
    qty_data.index = qty_data.index.strftime('%Y-%m')

    return (
        'Images/total_orders_forecast_ENI.png',
        'Images/order_quantity_forecast_ENI.png',
        order_data,
        qty_data
    )