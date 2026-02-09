import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FirstCry Store Auditor", layout="wide")

# --- DATABASE LOGIC ---
HISTORY_FILE = "cashbook_history.csv"

def save_entry(data):
    file_exists = os.path.isfile(HISTORY_FILE)
    df_history = pd.DataFrame([data])
    # Append to file
    df_history.to_csv(HISTORY_FILE, mode='a', index=False, header=not file_exists)

# --- COLORING FUNCTION ---
def color_variance(val):
    color = ''
    if isinstance(val, (int, float)):
        if val < -0.1: # Shortage (Red)
            color = 'background-color: #ffcccc; color: black'
        elif val > 0.1: # Excess (Green)
            color = 'background-color: #ccffcc; color: black'
    return color

# --- SIDEBAR TOOLS ---
st.sidebar.header("🛠️ Admin Controls")
if st.sidebar.button("🗑️ Reset All History"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        st.sidebar.success("History cleared! You can start fresh.")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("Step 1: Sync POS Data")
uploaded_file = st.sidebar.file_uploader("Upload 'Daywise Report.csv' (Generated NOW)", type="csv")

st.title("🏦 FirstCry Automated Cashbook & Audit")
st.markdown("---")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry (Shift Handover)", "📊 Monthly Variance Dashboard"])

if uploaded_file:
    # --- RIGOROUS DATA CLEANING ---
    try:
        df_pos = pd.read_csv(uploaded_file)
        # Clean column names and date values
        df_pos.columns = [col.strip() for col in df_pos.columns]
        df_pos['Date'] = df_pos['Date'].astype(str).str.strip()
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()
    
    with tab1:
        st.header("Shift Cash Reconciliation")
        with st.form("audit_form"):
            # Shift Details
            col_date, col_shift, col_mgr = st.columns(3)
            audit_date = col_date.date_input("Date", datetime.now())
            shift_type = col_shift.selectbox("Audit Type", ["Day End Closing", "8:00 PM Shift Handover"])
            mgr_name = col_mgr.text_input("Manager Name (Who is counting?)")

            st.markdown("---")
            
            # Collection Entry
            st.subheader("1. Manager Collection Entry (Actuals)")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash Collected (₹)", min_value=0.0, step=1.0)
            mgr_upi = c2.number_input("Actual UPI Collected (₹)", min_value=0.0, step=1.0)
            mgr_card = c3.number_input("Actual Card Collected (₹)", min_value=0.0, step=1.0)
            
            # Manual Billing
            st.markdown("---")
            st.subheader("2. Manual Billing (Not in POS)")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
            manual_mode = m_col2.selectbox("Mode", ["None", "Cash", "UPI", "Card"])

            # Denominations
            st.markdown("---")
            st.subheader("3. Physical Cash Denominations")
            col_den, col_bank = st.columns(2)
            with col_den:
                n500 = st.number_input("500 x", min_value=0, step=1)
                n200 = st.number_input("200 x", min_value=0, step=1)
                n100 = st.number_input("100 x", min_value=0, step=1)
                n50 = st.number_input("50 x", min_value=0, step=1)
                n20 = st.number_input("20 x", min_value=0, step=1)
                n10 = st.number_input("10 x", min_value=0, step=1)
                c5 = st.number_input("5 x", min_value=0, step=1)
                c2 = st.number_input("2 x", min_value=0, step=1)
                c1 = st.number_input("1 x", min_value=0, step=1)
            
            with col_bank:
                bank_dep = st.number_input("Bank Deposit (₹)", min_value=0.0)

            submit = st.form_submit_button("Verify, Save & Show Variance")

        if submit:
            if not mgr_name:
                st.error("⚠️ Please enter Manager Name before saving!")
            else:
                search_date = audit_date.strftime("%d-%m-%Y")
                pos_row = df_pos[df_pos['Date'].str.contains(search_date)]
                
                if pos_row.empty:
                    st.error(f"❌ Date '{search_date}' not found in the uploaded report.")
                else:
                    # Extraction
                    p_cash = pos_row.iloc[0]['ReceivedCashAmount']
                    p_upi = pos_row.iloc[0]['WalletAmount']
                    p_card = pos_row.iloc[0]['CardAmount']

                    # Adjust for Manual Bills
                    exp_cash = p_cash + (manual_amt if manual_mode == "Cash" else 0)
                    exp_upi = p_upi + (manual_amt if manual_mode == "UPI" else 0)
                    exp_card = p_card + (manual_amt if manual_mode == "Card" else 0)

                    # Physical Total
                    physical = (n500*500)+(n200*200)+(n100*100)+(n50*50)+(n20*20)+(n10*10)+(c5*5)+(c2*2)+(c1*1)
                    
                    # Save to History
                    save_entry({
                        "Date": search_date,
                        "Shift": shift_type,
                        "Manager": mgr_name,
                        "Actual_Cash": mgr_cash, "POS_Cash_Exp": exp_cash,
                        "Actual_UPI": mgr_upi, "POS_UPI_Exp": exp_upi,
                        "Actual_Card": mgr_card, "POS_Card_Exp": exp_card,
                        "Physical_Drawer": physical, "Bank_Deposit": bank_dep
                    })
                    
                    # --- DAILY RESULTS ---
                    st.markdown("---")
                    st.header(f"Audit Result: {shift_type} ({mgr_name})")
                    st.info(f"💵 **Net Physical Cash Counted: ₹{physical}**")

                    v1, v2, v3 = st.columns(3)
                    v1.metric("Cash vs POS", f"₹{mgr_cash}", f"{round(mgr_cash - exp_cash, 2)} Var", delta_color="inverse")
                    v2.metric("UPI vs POS", f"₹{mgr_upi}", f"{round(mgr_upi - exp_upi, 2)} Var", delta_color="inverse")
                    v3.metric("Card vs POS", f"₹{mgr_card}", f"{round(mgr_card - exp_card, 2)} Var", delta_color="inverse")
                    
                    if physical == mgr_cash:
                        st.success(f"✅ Drawer Tally: Matches (₹{physical})")
                        if mgr_cash == exp_cash: st.balloons()
                    else:
                        st.error(f"⚠️ Drawer Mismatch: Physical ₹{physical} vs Entered ₹{mgr_cash}")

    with tab2:
        st.header("Monthly Variance & Handover Log")
        if os.path.isfile(HISTORY_FILE):
            h_df = pd.read_csv(HISTORY_FILE)
            
            # --- CRITICAL FIX: Ensure Data is Numeric for Calculations ---
            cols_to_numeric = ['Actual_Cash', 'POS_Cash_Exp', 'Actual_UPI', 'POS_UPI_Exp', 'Actual_Card', 'POS_Card_Exp', 'Physical_Drawer', 'Bank_Deposit']
            for col in cols_to_numeric:
                if col in h_df.columns:
                    h_df[col] = pd.to_numeric(h_df[col], errors='coerce').fillna(0)

            # Check if columns exist (Schema Check)
            if 'Shift' not in h_df.columns:
                 st.error("⚠️ History file format is old. Please click 'Reset All History' in the sidebar to add Shift columns.")
            else:
                # Calculate Variances
                h_df['Cash_Var'] = h_df['Actual_Cash'] - h_df['POS_Cash_Exp']
                h_df['UPI_Var'] = h_df['Actual_UPI'] - h_df['POS_UPI_Exp']
                h_df['Card_Var'] = h_df['Actual_Card'] - h_df['POS_Card_Exp']
                h_df['Drawer_Diff'] = h_df['Physical_Drawer'] - h_df['Actual_Cash']

                # Select Columns to Show
                display_cols = ['Date', 'Shift', 'Manager', 
                                'Actual_Cash', 'POS_Cash_Exp', 'Cash_Var',
                                'UPI_Var', 'Card_Var', 'Drawer_Diff', 'Bank_Deposit']

                # Display Table with Highlighting
                st.dataframe(
                    h_df[display_cols].style.applymap(color_variance, subset=['Cash_Var', 'UPI_Var', 'Card_Var', 'Drawer_Diff']),
                    use_container_width=True
                )
                
                # --- MONTHLY NET VARIANCE SUMMARY ---
                st.markdown("---")
                st.subheader("Monthly Net Performance")
                
                m1, m2, m3, m4 = st.columns(4)
                # Calculating Sums explicitly
                net_cash_var = h_df['Cash_Var'].sum()
                net_upi_var = h_df['UPI_Var'].sum()
                net_card_var = h_df['Card_Var'].sum()
                total_deposit = h_df['Bank_Deposit'].sum()

                m1.metric("Net Cash Variance", f"₹{round(net_cash_var, 2)}", delta=f"{round(net_cash_var, 2)}", delta_color="inverse")
                m2.metric("Net UPI Variance", f"₹{round(net_upi_var, 2)}", delta=f"{round(net_upi_var, 2)}", delta_color="inverse")
                m3.metric("Net Card Variance", f"₹{round(net_card_var, 2)}", delta=f"{round(net_card_var, 2)}", delta_color="inverse")
                m4.metric("Total Bank Deposits", f"₹{round(total_deposit, 2)}")
        else:
            st.info("No entries yet. Submit an audit to see history.")
else:
    st.warning("Please upload the POS Report CSV in the sidebar.")
