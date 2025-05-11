import streamlit as st

# Set the title of the app
st.title("JR286 Labor Forecasting")

# Add a header
st.header("Demand Forecasting")

# Add some text 
st.write("Set the parameters for the demand forecasting to run the model.")

# Add an input box
orders = st.text_input("Number of orders:")
quantity = st.text_input("Total order quantity:")

# Add a header
st.header("Labor Forecast")

# Add some text
st.write("Run the labor forecasting model with the parameters set above.")