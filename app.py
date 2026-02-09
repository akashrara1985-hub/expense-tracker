import streamlit as st
import pandas as pd
import PyPDF2
import re

st.title("Multi-Statement Expense Tracker")

CATEGORY_MAPPING = {
    'Food & Dining': ['canteen', 'restaurant', 'cafe', 'zomato', 'swiggy', 'food', 'tea', 'coffee', 'irani', 'sweet', 'bakery', 'caterers'],
    'Groceries': ['market', 'store', 'provision', 'blinkit', 'grocery', 'vegetables', 'fruits'],
    'Healthcare': ['medical', 'hospital', 'pharmacy', 'wellness', 'clinic', 'doctor', 'medicine', 'healthcare'],
    'Transport': ['uber', 'ola', 'taxi', 'auto', 'metro', 'bus', 'petrol', 'fuel'],
    'Shopping': ['amazon', 'flipkart', 'myntra', 'mall', 'shop', 'retail', 'zone', 'enterprise', 'honeybee'],
    'Entertainment': ['movie', 'cinema', 'netflix', 'prime', 'spotify', 'apple', 'youtube', 'game'],
    'Personal Care': ['salon', 'spa', 'barber', 'beauty', 'style'],
    'Utilities': ['electricity', 'water', 'gas', 'recharge', 'mobile', 'internet', 'telecom', 'phone', 'bhakti']
}

def categorize_transaction(description):
    description_lower = description.lower()
    for category, keywords in CATEGORY_MAPPING.items():
        for keyword in keywords:
            if keyword in description_lower:
                return category
    return 'Miscellaneous'

uploaded_files = st.file_uploader("Upload statements", type=['csv', 'pdf'], accept_multiple_files=True)
all_transactions = []

if uploaded_files:
    st.write(f"### Processing {len(uploaded_files)} file(s)...")
    
    for uploaded_file in uploaded_files:
        st.write(f"Processing: **{uploaded_file.name}**")
        
        if uploaded_file.name.endswith('.pdf'):
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # Try Paytm format first
                paytm_match = re.search(r'Total Money Paid\s*-?\s*Rs\.?\s*([\d,]+)', text, re.IGNORECASE)
                if paytm_match:
                    total_amount = float(paytm_match.group(1).replace(',', ''))
                    all_transactions.append({
                        'Date': 'Paytm Total',
                        'Description': 'Paytm Statement',
                        'Amount': total_amount,
                        'Category': 'Total',
                        'Source': uploaded_file.name
                    })
                    st.success(f"Paytm total: Rs.{total_amount:,.2f}")
                else:
                    # PhonePe format - just find all "INR" amounts
                    amounts = re.findall(r'INR\s+([\d,]+\.?\d*)', text)
                    
                    if amounts:
                        st.info(f"Found {len(amounts)} amounts in PhonePe PDF")
                        
                        # Also try to get merchant names
                        merchants = re.findall(r'Paid to\s+([^\n]+)', text)
                        
                        for i, amount_str in enumerate(amounts):
                            try:
                                amount = float(amount_str.replace(',', ''))
                                merchant = merchants[i].strip() if i < len(merchants) else "Unknown"
                                
                                all_transactions.append({
                                    'Date': f'Transaction {i+1}',
                                    'Description': merchant,
                                    'Amount': amount,
                                    'Category': categorize_transaction(merchant),
                                    'Source': uploaded_file.name
                                })
                            except:
                                continue
                        
                        total = sum([t['Amount'] for t in all_transactions if t['Source'] == uploaded_file.name])
                        st.success(f"PhonePe total: Rs.{total:,.2f}")
                    else:
                        st.warning("No amounts found")
                        
            except Exception as e:
                st.error(f"Error: {e}")
    
    if all_transactions:
        st.write("---")
        result_df = pd.DataFrame(all_transactions)
        result_for_categories = result_df[result_df['Category'] != 'Total'].copy()
        grand_total = result_df['Amount'].sum()
        
        st.success(f"# TOTAL: Rs.{grand_total:,.2f}")
        
        if not result_for_categories.empty:
            st.write("## Category Breakdown")
            category_summary = result_for_categories.groupby('Category')['Amount'].agg(['sum', 'count']).reset_index()
            category_summary.columns = ['Category', 'Total', 'Count']
            category_summary = category_summary.sort_values('Total', ascending=False)
            category_summary['Percentage'] = (category_summary['Total'] / category_summary['Total'].sum() * 100).round(1)
            
            for _, row in category_summary.iterrows():
                st.write(f"**{row['Category']}**: Rs.{row['Total']:,.2f} ({row['Percentage']}%) - {row['Count']} transactions")
        
        st.write("---")
        st.write("### All Transactions")
        display_df = result_df.copy()
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"Rs.{x:,.2f}")
        st.dataframe(display_df)
        
        csv = result_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "expenses.csv", "text/csv")
    else:
        st.warning("No data found")
else:
    st.info("Upload Paytm or PhonePe PDF files")