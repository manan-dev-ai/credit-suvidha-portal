from flask import Flask, render_template, request, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import os
import re
from datetime import datetime, timedelta
import glob

app = Flask(__name__)

# --- CONFIGURATION ---
DATA_FOLDER = 'daily_leads'
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

PROFIT_FILE = 'MASTER_PROFIT_SHEET.xlsx'

# --- DATABASE HELPERS ---

def get_todays_file():
    """Returns filename for today, e.g., 'daily_leads/18-02-2026.xlsx'"""
    today_str = datetime.now().strftime("%d-%m-%Y")
    return os.path.join(DATA_FOLDER, f"{today_str}.xlsx")

def save_lead_to_excel(name, phone, amount, status, source="Manual"):
    """Saves or Updates a lead using Robust ID and Phone Matching"""
    try:
        file_path = get_todays_file()
        clean_phone = re.sub(r'\D', '', str(phone))
        unique_id = int(datetime.now().timestamp())
        
        new_row = {
            'ID': unique_id,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Name': name,
            'Phone': clean_phone,
            'Amount': amount,
            'Status': status,
            'Source': source
        }

        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            # Ensure phone column is string
            df['Phone'] = df['Phone'].astype(str).str.replace(r'\D', '', regex=True)
            mask = df['Phone'] == clean_phone
            
            if mask.any():
                idx = df[mask].index[0]
                
                # 1. Update Status (unless already closed)
                if df.at[idx, 'Status'] != "Deal Closed":
                    df.at[idx, 'Status'] = status
                
                # 2. Update Amount (if valid number)
                if str(amount).isdigit() and int(amount) > 0:
                    df.at[idx, 'Amount'] = int(amount)
                    
                # 3. SMART SOURCE UPDATE (Protects Bank Name)
                # If new source is a specific Bank Name, save it.
                if source not in ["WhatsApp", "Manual", "WhatsApp Web Bot"]:
                    df.at[idx, 'Source'] = source
                # If old source was generic, update it to the new one
                elif str(df.at[idx, 'Source']) in ["nan", "Manual", "WhatsApp", "WhatsApp Web Bot"]:
                    df.at[idx, 'Source'] = source

                df.at[idx, 'Timestamp'] = new_row['Timestamp']
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel(file_path, index=False)
        else:
            df = pd.DataFrame([new_row])
            df.to_excel(file_path, index=False)
    except Exception as e:
        print(f"❌ Database Error: {e}")

def add_to_profit_sheet(lead_data):
    """Moves paid deals to the Permanent Master Sheet"""
    try:
        final_amount = int(float(lead_data['Amount']))
    except:
        final_amount = 0

    profit_row = {
        'Closure Date': datetime.now().strftime("%Y-%m-%d"),
        'Customer Name': lead_data['Name'],
        'Phone Number': lead_data['Phone'],
        'Bill Amount': final_amount,
        'Bank/Card': lead_data.get('Source', 'Unknown')
    }
    
    if os.path.exists(PROFIT_FILE):
        try:
            df_profit = pd.read_excel(PROFIT_FILE)
            # Avoid duplicates based on Phone
            if not df_profit['Phone Number'].astype(str).str.contains(str(lead_data['Phone'])).any():
                df_profit = pd.concat([df_profit, pd.DataFrame([profit_row])], ignore_index=True)
                df_profit.to_excel(PROFIT_FILE, index=False)
                print(f"💰 Saved ₹{final_amount} to Profit Sheet!")
        except: pass
    else:
        df_profit = pd.DataFrame([profit_row])
        df_profit.to_excel(PROFIT_FILE, index=False)

def get_all_leads_sorted():
    """Reads ALL daily files and sorts by Date (Newest First)"""
    all_files = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx"))
    all_leads = []
    
    for file in all_files:
        try:
            df = pd.read_excel(file)
            for index, row in df.iterrows():
                lead_data = row.to_dict()
                lead_data['File'] = os.path.basename(file)
                lead_data['ID'] = int(row['ID']) 
                
                try:
                    visit_time = pd.to_datetime(row['Timestamp'])
                    time_diff = datetime.now() - visit_time
                    lead_data['DisplayDate'] = visit_time.strftime("%d %b, %I:%M %p")
                    lead_data['SortDate'] = visit_time
                except:
                    lead_data['DisplayDate'] = str(row['Timestamp'])
                    lead_data['SortDate'] = datetime.min

                lead_data['IsLate'] = False
                if lead_data['Status'] == "Visit Scheduled" and time_diff > timedelta(days=2):
                    lead_data['IsLate'] = True
                
                all_leads.append(lead_data)
        except: pass
    
    # Sort: Newest First
    all_leads.sort(key=lambda x: x['SortDate'], reverse=True)
    return all_leads

def get_profit_data():
    """Reads the Profit Sheet for the Dashboard"""
    if os.path.exists(PROFIT_FILE):
        try:
            df = pd.read_excel(PROFIT_FILE)
            df['Bill Amount'] = pd.to_numeric(df['Bill Amount'], errors='coerce').fillna(0)
            return df.to_dict('records')
        except: return []
    return []

# --- WHATSAPP LOGIC (DEBUG MODE) ---

@app.route('/whatsapp-webhook', methods=['POST'])
def whatsapp_hook():
    print("\n--------------------------------")
    print("📩 NEW MESSAGE RECEIVED!")
    
    incoming_msg = request.values.get('Body', '').strip().lower()
    sender_phone = request.values.get('From', '').replace('whatsapp:', '')
    sender_name = request.values.get('ProfileName', 'Unknown')
    
    print(f"👤 From: {sender_name} | Msg: {incoming_msg}")

    resp = MessagingResponse()
    msg = resp.message()

    # Keywords
    greetings = ['hi', 'hello', 'hii', 'hey', 'start', 'namaste']
    agreement = ['yes', 'ha', 'hanji', 'ok', 'ha']
    visit_keywords = ['visit', 'office', 'meet', 'coming', 'appointment']
    banks = ['hdfc', 'sbi', 'axis', 'icici', 'kotak', 'amex', 'bob', 'rbl', 'indusind', 'onecard', 'idfc']

    # 1. Visit
    if any(word in incoming_msg for word in visit_keywords):
        print("👉 Action: Sending Visit Info")
        msg.body("ચોક્કસ! અમારી ઓફિસ નો સમય સવારે 10 થી સાંજે 7 છે. (Address: CG Road). અમે તમારી રાહ જોઈશું! 🏢")
        save_lead_to_excel(sender_name, sender_phone, 0, "Visit Scheduled", "WhatsApp")

    # 2. Amount
    elif re.findall(r'\d+', incoming_msg):
        print("👉 Action: Saving Amount")
        amounts = re.findall(r'\d+', incoming_msg)
        extracted_amount = int(amounts[0])
        msg.body("નોંધાઈ ગયું! ✅ શું તમે ઓફિસ મુલાકાત લેશો કે ઓનલાઇન વાત કરવા માંગો છો?")
        save_lead_to_excel(sender_name, sender_phone, extracted_amount, "In Discussion", "WhatsApp")

    # 3. Bank Name
    elif any(bank in incoming_msg for bank in banks):
        print("👉 Action: Bank Name Found")
        bank_name = next(bank for bank in banks if bank in incoming_msg).upper()
        msg.body(f"આભાર! {bank_name} કાર્ડ માટે સર્વિસ ઉપલબ્ધ છે. ✅\n\nહવે તમારું નામ અને બિલની રકમ લખો.")
        # Save JUST the bank name
        save_lead_to_excel(sender_name, sender_phone, 0, f"Card: {bank_name}", bank_name)

    # 4. Agreement
    elif any(word in incoming_msg for word in agreement):
        print("👉 Action: Asking for Card")
        msg.body("તમે કઈ બેંકનું ક્રેડિટ કાર્ડ વાપરો છો? 💳\n(દા.ત. HDFC, SBI, Axis, ICICI)")
        save_lead_to_excel(sender_name, sender_phone, 0, "Asking Card Details", "WhatsApp")
        
    # 5. Default Greeting
    else:
        print("👉 Action: Default Greeting")
        msg.body("નમસ્તે! CredSuvidha માં સ્વાગત છે. શું તમારે ક્રેડિટ કાર્ડનું બિલ ભરવું છે? (Reply 'Yes')")
        save_lead_to_excel(sender_name, sender_phone, 0, "New Inquiry", "WhatsApp")

    print("✅ Reply Sent")
    return str(resp)

# --- ROUTES ---

@app.route('/')
def dashboard():
    active_leads = get_all_leads_sorted()
    closed_deals = get_profit_data()
    return render_template('dashboard.html', leads=active_leads, profits=closed_deals)

@app.route('/update_status/<path:filename>/<int:lead_id>/<status>')
def update_status(filename, lead_id, status):
    file_path = os.path.join(DATA_FOLDER, filename)
    try:
        df = pd.read_excel(file_path)
        mask = df['ID'] == lead_id
        
        if mask.any():
            idx = df[mask].index[0]
            
            # --- PROFIT LOGIC WITH SAFETY LOCK ---
            if status == "Deal Closed":
                # Check Amount First!
                try:
                    current_amount = float(df.at[idx, 'Amount'])
                except:
                    current_amount = 0
                
                if current_amount <= 0:
                    print("⚠️ Cannot Close: Amount is 0! Please enter valid amount first.")
                    return redirect(url_for('dashboard'))

                # Move to Profit Sheet
                lead_data = df.loc[idx].to_dict()
                lead_data['File'] = filename
                add_to_profit_sheet(lead_data)
                
                # Delete from Daily Sheet
                df = df.drop(idx)
            else:
                df.at[idx, 'Status'] = status
                
            df.to_excel(file_path, index=False)
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('dashboard'))

@app.route('/delete/<path:filename>/<int:lead_id>')
def delete_lead(filename, lead_id):
    file_path = os.path.join(DATA_FOLDER, filename)
    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df = df[df['ID'] != lead_id]
            df.to_excel(file_path, index=False)
    except: pass
    return redirect(url_for('dashboard'))

@app.route('/add', methods=['POST'])
def add_manual():
    save_lead_to_excel(request.form['name'], request.form['phone'], request.form['amount'], "New Inquiry", "Manual")
    return redirect(url_for('dashboard'))

# Optional: Route for Selenium Bot if you use it later
@app.route('/add_via_bot', methods=['POST'])
def add_via_bot():
    name = request.form.get('name')
    msg = request.form.get('msg', '')
    save_lead_to_excel(name, "Unknown", 0, "New Inquiry", "WhatsApp Web Bot")
    return "OK"

if __name__ == '__main__':
    app.run(debug=True, port=5000)