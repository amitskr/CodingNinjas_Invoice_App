import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import zipfile
from datetime import datetime

st.set_page_config(page_title="Coding Ninjas Invoice Generator", page_icon="https://www.codingninjas.com/careercamp/wp-content/uploads/2025/10/cn-favicon.png", layout="centered")

st.markdown(
    """
    <div style="text-align:center">
        <img src="https://www.codingninjas.com/careercamp/wp-content/uploads/2025/10/CN_logo_white.png" width="160">
        <h2 style="color:#d5977e;">Coding Ninjas</h2>
        <h3 style="color:#d5977e;">Mentor/Alumni Invoice Generator</h3>
        <p>Upload your CSV file to automatically generate branded PDF invoices for each mentor/alumni.</p>
    </div>
    """ ,
    unsafe_allow_html=True
)

st.sidebar.header("⚙️ Invoice Settings")
invoice_date = st.sidebar.date_input("Invoice Date", datetime.now())
invoice_number_start = st.sidebar.number_input("Starting Invoice Number", min_value=1, value=1)

st.sidebar.markdown("### Company Details")
company_name = st.sidebar.text_input("Company Name", "SUNRISE MENTORS PVT LTD")
company_address_line1 = st.sidebar.text_input("Address Line 1", "UNITECH CYBER PARK, Unit 007 - 008, GF,")
company_address_line2 = st.sidebar.text_input("Address Line 2", "Tower A, Sector 39, Gurugram, Haryana 122003")

uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

def sanitize_text(text):
    """Remove or replace Unicode characters not supported by Helvetica font"""
    if not isinstance(text, str):
        text = str(text)
    
    replacements = {
        '–': '-', '—': '-', '"': '"', '"': '"', ''': "'", ''': "'",
        '…': '...', '₹': 'Rs.', '°': ' degrees', '×': 'x', '÷': '/',
        '±': '+/-', '≤': '<=', '≥': '>=', '≠': '!=', '™': '(TM)',
        '©': '(C)', '®': '(R)', '•': '*', '→': '->', '←': '<-',
        '↑': '^', '↓': 'v',
    }
    
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        st.success("✅ File uploaded successfully!")
        st.write(f"**Total rows loaded:** {len(df)}")
        st.dataframe(df.head(10))

        required_cols = {"Mentor/Alumni", "Session Date", "Amount", "Name", "Email", 
                        "Account Holder", "Pan Number", "Bank", "Account Number", "IFSC Code", "Branch"}
        
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Missing columns! Required: {', '.join(required_cols)}")
            st.write(f"Available columns: {', '.join(df.columns)}")
            st.stop()

        st.write("**Entries per Mentor/Alumni:**")
        mentor_counts = df.groupby("Mentor/Alumni").size().reset_index(name='Count')
        st.dataframe(mentor_counts)

        class PDF(FPDF):
            def __init__(self):
                super().__init__()
                self.set_auto_page_break(auto=True, margin=15)

        if st.button("🚀 Generate Invoices"):
            try:
                buffer = BytesIO()
                invoice_count = 0
                current_invoice_num = invoice_number_start
                
                with zipfile.ZipFile(buffer, "w") as zipf:
                    for mentor, data in df.groupby("Mentor/Alumni"):
                        data = data.reset_index(drop=True)
                        st.write(f"Processing {mentor}: {len(data)} entries")
                        
                        # Get mentor details from first row
                        first_row = data.iloc[0]
                        mentor_name = sanitize_text(str(first_row["Mentor/Alumni"]))
                        mentor_email = sanitize_text(str(first_row.get("Email", "")))
                        
                        # Handle phone number - convert to int to remove .0
                        phone_val = first_row.get("Phone", "")
                        if pd.notna(phone_val) and phone_val != "":
                            try:
                                mentor_phone = sanitize_text(str(int(float(phone_val))))
                            except (ValueError, TypeError):
                                mentor_phone = sanitize_text(str(phone_val))
                        else:
                            mentor_phone = ""
                        
                        mentor_address = sanitize_text(str(first_row.get("Address", "")))
                        
                        # Banking details
                        account_holder = sanitize_text(str(first_row.get("Account Holder", "")))
                        pan_number = sanitize_text(str(first_row.get("Pan Number", "")))
                        bank_name = sanitize_text(str(first_row.get("Bank", "")))
                        
                        # Handle account number - convert to int to remove .0
                        acc_val = first_row.get("Account Number", "")
                        if pd.notna(acc_val) and acc_val != "":
                            try:
                                account_number = sanitize_text(str(int(float(acc_val))))
                            except (ValueError, TypeError):
                                account_number = sanitize_text(str(acc_val))
                        else:
                            account_number = ""
                        
                        ifsc_code = sanitize_text(str(first_row.get("IFSC Code", "")))
                        branch = sanitize_text(str(first_row.get("Branch", "")))
                        
                        pdf = PDF()
                        pdf.add_page()
                        
                        # Logo (small, top-left)
                        logo_url = "https://www.codingninjas.com/careercamp/wp-content/uploads/2025/10/CN_Logo_Dark.png"
                        pdf.image(logo_url, x=10, y=8, w=35)
                        pdf.ln(25)
                        
                        # Right side - Mentor Details
                        pdf.set_font("Helvetica", "B", 16)
                        pdf.cell(0, 8, mentor_name, 0, 1, "R")
                        pdf.set_font("Helvetica", "", 10)
                        if mentor_email:
                            pdf.cell(0, 6, mentor_email, 0, 1, "R")
                        if mentor_phone:
                            pdf.cell(0, 6, mentor_phone, 0, 1, "R")
                        
                        pdf.ln(5)
                        
                        # Left side - Issued to
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(100, 8, "Issued to", 0, 0, "L")
                        
                        # Right side - Invoice details
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(45, 8, "Invoice No", 0, 0, "R")
                        pdf.set_font("Helvetica", "", 12)
                        pdf.cell(0, 8, str(current_invoice_num), 0, 1, "R")
                        
                        # Company details
                        pdf.set_font("Helvetica", "", 10)
                        pdf.cell(100, 6, company_name, 0, 0, "L")
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(45, 6, "Date", 0, 0, "R")
                        pdf.set_font("Helvetica", "", 12)
                        pdf.cell(0, 6, invoice_date.strftime("%d-%m-%Y"), 0, 1, "R")
                        
                        pdf.set_font("Helvetica", "", 10)
                        pdf.cell(0, 6, company_address_line1, 0, 1, "L")
                        pdf.cell(0, 6, company_address_line2, 0, 1, "L")
                        
                        pdf.ln(5)
                        
                        # Pay to section
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(0, 8, "Pay to", 0, 1, "L")
                        pdf.set_font("Helvetica", "", 10)
                        pdf.cell(0, 6, mentor_name, 0, 1, "L")
                        if mentor_address:
                            pdf.cell(0, 6, mentor_address, 0, 1, "L")
                        
                        pdf.ln(5)
                        
                        # Table Header
                        pdf.set_fill_color(0, 0, 0)
                        pdf.set_text_color(255, 255, 255)
                        pdf.set_font("Helvetica", "B", 11)
                        pdf.cell(80, 10, "Description", 1, 0, "L", True)
                        pdf.cell(45, 10, "Category", 1, 0, "L", True)
                        pdf.cell(35, 10, "Type", 1, 0, "L", True)
                        pdf.cell(30, 10, "Amount", 1, 1, "R", True)
                        
                        # Table rows
                        pdf.set_text_color(0, 0, 0)
                        pdf.set_font("Helvetica", "", 9)
                        total = 0
                        
                        for idx, row in data.iterrows():
                            description = sanitize_text(str(row.get("Name", row.get("Email", ""))))
                            category = sanitize_text(str(row.get("Category", "Alumni Connect")))
                            type_val = sanitize_text(str(row.get("Type", "Enrolled Lead")))
                            amount = row["Amount"]
                            
                            pdf.cell(80, 8, description[:45], 1, 0, "L")
                            pdf.cell(45, 8, category, 1, 0, "L")
                            pdf.cell(35, 8, type_val, 1, 0, "L")
                            pdf.cell(30, 8, f"{float(amount):,.2f}", 1, 1, "R")
                            
                            try:
                                total += float(amount)
                            except (ValueError, TypeError):
                                pass
                        
                        # Empty row for spacing
                        pdf.ln(5)
                        
                        # Total row
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(160, 10, "Total", 1, 0, "L")
                        pdf.cell(30, 10, f"Rs. {total:,.2f}", 1, 1, "R")
                        
                        pdf.ln(10)
                        
                        # Details section
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(0, 8, "Details", 0, 1, "L")
                        pdf.set_font("Helvetica", "", 10)
                        
                        details = [
                            ("Account Holder", account_holder),
                            ("Pan Number", pan_number),
                            ("Bank", bank_name),
                            ("Account Number", account_number),
                            ("IFSC Code", ifsc_code),
                            ("Branch", branch)
                        ]
                        
                        for label, value in details:
                            if value and value != "nan":
                                pdf.cell(50, 6, label, 0, 0, "L")
                                pdf.cell(10, 6, ":", 0, 0, "L")
                                pdf.cell(0, 6, value, 0, 1, "L")
                        
                        # Save PDF
                        pdf_bytes = pdf.output()
                        safe_filename = sanitize_text(str(mentor).replace(' ', '_').replace('/', '_'))
                        zipf.writestr(f"{safe_filename}_invoice_{current_invoice_num}.pdf", pdf_bytes)
                        
                        invoice_count += 1
                        current_invoice_num += 1

                buffer.seek(0)
                st.download_button(
                    "⬇️ Download All Invoices (ZIP)",
                    data=buffer,
                    file_name="CodingNinjas_Invoices.zip",
                    mime="application/zip"
                )

                st.success(f"✅ Generated {invoice_count} invoices successfully!")
            
            except Exception as e:
                st.error(f"❌ Error generating invoices: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {str(e)}")
        import traceback
        st.code(traceback.format_exc())