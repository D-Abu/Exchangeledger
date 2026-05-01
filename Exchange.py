import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION & STORAGE ---
LOG_FILE = "pharmacy_logs.csv"

def load_data():
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        # Ensure the Timestamp is treated as a date
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    else:
        return pd.DataFrame(columns=["Timestamp", "Medicine", "Quantity", "Price_Per_Unit", "Total_Amount", "From", "To"])

# --- APP INTERFACE ---
st.set_page_config(page_title="Pharmacy Exchange Pro", layout="wide")
st.title("💊 Pharmacy Exchange & Settlement")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter & History")
data = load_data()

# Create Month/Year selection
if not data.empty:
    data['Month_Year'] = data['Timestamp'].dt.strftime('%B %Y')
    unique_months = data['Month_Year'].unique()
    selected_month = st.sidebar.selectbox("Select Month for Settlement", unique_months)
    filtered_df = data[data['Month_Year'] == selected_month]
else:
    filtered_df = data

# --- INPUT FORM ---
with st.form("exchange_form", clear_on_submit=True):
    st.subheader("Log New Exchange")
    col1, col2 = st.columns(2)
    
    with col1:
        med_name = st.text_input("Medicine Name")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price per Unit (₹)", min_value=0.0, step=0.5)
        
    with col2:
        from_pharmacy = st.text_input("Sending Pharmacy").strip().upper()
        to_pharmacy = st.text_input("Receiving Pharmacy").strip().upper()
    
    submit_button = st.form_submit_button("Record & Calculate")

# --- SAVING LOGIC ---
if submit_button:
    if med_name and from_pharmacy and to_pharmacy:
        total_amount = quantity * price
        new_entry = {
            "Timestamp": datetime.now(),
            "Medicine": med_name,
            "Quantity": quantity,
            "Price_Per_Unit": price,
            "Total_Amount": total_amount,
            "From": from_pharmacy,
            "To": to_pharmacy
        }
        
        df_to_save = pd.concat([load_data(), pd.DataFrame([new_entry])], ignore_index=True)
        df_to_save.to_csv(LOG_FILE, index=False)
        st.success(f"Logged! Total Value: ₹{total_amount}")
        st.rerun() # Refresh to update calculations
    else:
        st.error("Please fill all fields.")

# --- SETTLEMENT DASHBOARD ---
st.divider()
st.header(f"Settlement for {selected_month if not data.empty else 'Current Period'}")

if not filtered_df.empty:
    # 1. Calculate totals per pharmacy pair
    # How much did each pharmacy "send" in total value?
    summary = filtered_df.groupby(['From', 'To'])['Total_Amount'].sum().reset_index()
    
    # Simple display of the math
    st.subheader("Summary of Transactions")
    st.table(summary)

    # 2. Net Settlement Logic
    pharmacies = pd.unique(filtered_df[['From', 'To']].values.ravel())
    if len(pharmacies) >= 2:
        p1, p2 = pharmacies[0], pharmacies[1]
        
        val_p1_to_p2 = summary[(summary['From'] == p1) & (summary['To'] == p2)]['Total_Amount'].sum()
        val_p2_to_p1 = summary[(summary['From'] == p2) & (summary['To'] == p1)]['Total_Amount'].sum()
        
        diff = val_p1_to_p2 - val_p2_to_p1
        
        st.info("### Final Settlement Recommendation")
        if diff > 0:
            st.write(f"👉 **{p2}** owes **{p1}**:  **₹{abs(diff):,.2f}**")
        elif diff < 0:
            st.write(f"👉 **{p1}** owes **{p2}**:  **₹{abs(diff):,.2f}**")
        else:
            st.write("👉 All accounts are settled perfectly!")

# --- FULL HISTORY ---
st.divider()
st.subheader("Detailed Transaction History")
st.dataframe(filtered_df.sort_values(by="Timestamp", ascending=False), use_container_width=True)