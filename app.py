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

# Add a sidebar
st.sidebar.header("Sidebar Options")
st.sidebar.write("Use the sidebar to adjust additional settings.")

# Add elements side by side
col1, col2 = st.columns(2)

with col1:
    st.subheader("Column 1")
    st.write("This is the first column.")

with col2:
    st.subheader("Column 2")
    st.write("This is the second column.")

# Add an expander
with st.expander("See more details"):
    st.write("Here you can add additional information or options.")

# Use container for grouping
with st.container():
    st.write("This is inside a container.")
    st.button("Click Me")