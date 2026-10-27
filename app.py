import streamlit as st
import pandas as pd
import csv
import io
import datetime
import os
import re

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib import colors
from bahttext import bahttext

st.set_page_config(page_title="ระบบสรุปยอดค่าเทอม", layout="wide")

# ==========================================
# ลงทะเบียนฟอนต์ภาษาไทยสำหรับ PDF
# ==========================================
font_path = "THSarabunNew.ttf"
has_font = False
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('THSarabun', font_path))
    has_font = True

# ==========================================
# ฟังก์ชันตัวช่วย (ทำความสะอาดชื่อ และแยกหมวดหมู่)
# ==========================================
def clean_name_th(name):
    n = str(name).replace(' ', '').strip()
    prefixes = ['ด.ช.', 'ด.ญ.', 'เด็กชาย', 'เด็กหญิง', 'นาย', 'นาง', 'นางสาว']
    for p in prefixes:
        if n.startswith(p):
            n = n[len(p):]
    return n

def extract_gender(name, title_from_form=""):
    if title_from_form:
        if 'ชาย' in str(title_from_form) or 'ด.ช.' in str(title_from_form): return 'ชาย'
        if 'หญิง' in str(title_from_form) or 'ด.ญ.' in str(title_from_form): return 'หญิง'
    
    n = str(name).replace(' ', '').strip()
    if n.startswith('ด.ช.') or n.startswith('เด็กชาย') or n.startswith('นาย'): return 'ชาย'
    if n.startswith('ด.ญ.') or n.startswith('เด็กหญิง') or n.startswith('นาง'): return 'หญิง'
    return 'ไม่ระบุ'

def get_grade_info(raw_grade):
    mapping = {
        'ปถ1': ('ประถมต้น', 'ประถมศึกษาปีที่ 1'),
        'ปถ2': ('ประถมต้น', 'ประถมศึกษาปีที่ 2'),
        'ปถ3': ('ประถมต้น', 'ประถมศึกษาปีที่ 3'),
        'ปถ4': ('ประถมปลาย', 'ประถมศึกษาปีที่ 4'),
        'ปถ5': ('ประถมปลาย', 'ประถมศึกษาปีที่ 5'),
        'ปถ6': ('ประถมปลาย', 'ประถมศึกษาปีที่ 6'),
        'อบ1': ('อนุบาล', 'อนุบาล 1'),
        'อบ2': ('อนุบาล', 'อนุบาล 2'),
        'อบ3': ('อนุบาล', 'อนุบาล 3'),
        'อนุบาล 1': ('อนุบาล', 'อนุบาล 1'),
        'อนุบาล 2': ('อนุบาล', 'อนุบาล 2'),
        'อนุบาล 3': ('อนุบาล', 'อนุบาล 3'),
        'ประถมศึกษาปีที่ 1': ('ประถมต้น', 'ประถมศึกษาปีที่ 1'),
        'ประถมศึกษาปีที่ 2': ('ประถมต้น', 'ประถมศึกษาปีที่ 2'),
        'ประถมศึกษาปีที่ 3': ('ประถมต้น', 'ประถมศึกษาปีที่ 3'),
        'ประถมศึกษาปีที่ 4': ('ประถมปลาย', 'ประถมศึกษาปีที่ 4'),
        'ประถมศึกษาปีที่ 5': ('ประถมปลาย', 'ประถมศึกษาปีที่ 5'),
        'ประถมศึกษาปีที่ 6': ('ประถมปลาย', 'ประถมศึกษาปีที่ 6'),
    }
    clean_raw = str(raw_grade).strip()
    return mapping.get(clean_raw, ('ไม่ระบุ', clean_raw))

# ==========================================
# ฟังก์ชันสร้าง PDF
# ==========================================
def create_receipts_pdf(df_paid):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=landscape(A4))
    
    if has_font:
        font_name = 'THSarabun'
    else:
        font_name = 'Helvetica'
    
    for idx, row in df_paid.iterrows():
        student_code = row['รหัสนักเรียน']
        student_name = row['ชื่อ-นามสกุล']
        salesperson = row.get('พนักงานขาย (ระดับชั้นย่อย)', '') 
        receipt_no = row['เลขที่ใบเสร็จ'] 
        pay_date = row.get('วันที่จ่ายเงิน', '') 
        total_amount = row['ยอดที่จ่าย (บาท)']
        amount_text = bahttext(total_amount)
        
        today_str = str(pay_date)
        
        invoices = row.get('รายการบิล', [])
        if not isinstance(invoices, list) or len(invoices) == 0:
            invoices = [{'doc_no': row['เอกสารอ้างอิง'], 'paid': total_amount, 'remain': row['ยอดคงเหลือล่าสุด (บาท)']}]
        
        # --- ส่วนหัว (Header) ---
        c.setFont(font_name, 22)
        c.drawString(2*cm, 18*cm, "โรงเรียนศิริมงคลศึกษา บางบัวทอง")
        
        c.setFont(font_name, 14)
        c.drawString(2*cm, 17.2*cm, "เลขที่ 91/1 ซอยศิริมงคล ถนนบางกรวย-ไทรน้อย ต.บางรักพัฒนา อ.บางบัวทอง จังหวัดนนทบุรี")
        c.drawString(2*cm, 16.5*cm, "FAX. 02-920-8133 TEL.08")
        c.drawString(2*cm, 15.8*cm, "เลขประจำตัวผู้เสียภาษี 0994000242379")
        
        c.setFont(font_name, 24)
        c.drawRightString(27.5*cm, 17*cm, "ใบเสร็จรับเงิน / Receipt")
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(2*cm, 14.5*cm, 27.5*cm, 14.5*cm)
        
        # --- ข้อมูลลูกค้าและเอกสาร ---
        c.setFont(font_name, 16)
        
        left_label = 2 * cm
        left_colon = 5 * cm
        left_val = 5.3 * cm
        
        c.drawString(left_label, 13.5*cm, "ลูกค้า (รหัสลูกค้า)")
        c.drawString(left_colon, 13.5*cm, ":")
        c.drawString(left_val, 13.5*cm, f"{student_code}")
        
        c.drawString(left_label, 12.8*cm, "ชื่อ-สกุล")
        c.drawString(left_colon, 12.8*cm, ":")
        c.drawString(left_val, 12.8*cm, f"{student_name}")
        
        c.drawString(left_label, 12.1*cm, "ที่อยู่")
        c.drawString(left_colon, 12.1*cm, ":")
        c.drawString(left_val, 12.1*cm, "........................................................................")
        
        right_label = 16.5 * cm
        right_colon = 19 * cm
        right_val = 19.3 * cm
        
        c.drawString(right_label, 13.5*cm, "เลขที่ใบเสร็จ")
        c.drawString(right_colon, 13.5*cm, ":")
        c.drawString(right_val, 13.5*cm, f"{receipt_no}")
        
        c.drawString(right_label, 12.8*cm, "วันที่")
        c.drawString(right_colon, 12.8*cm, ":")
        c.drawString(right_val, 12.8*cm, f"{today_str}")
        
        c.drawString(right_label, 12.1*cm, "พนักงานขาย")
        c.drawString(right_colon, 12.1*cm, ":")
        c.drawString(right_val, 12.1*cm, f"{salesperson}")
        
        # --- ตารางรายการ ---
        table_top = 11 * cm
        row_height = 0.8 * cm 
        
        num_rows = len(invoices)
        if num_rows > 1: 
            num_rows += 1 
            
        table_height = (num_rows * row_height) + 0.5 * cm
        if table_height < 2 * cm: 
            table_height = 2 * cm 
            
        table_bottom = table_top - table_height
        
        c.setFillColor(colors.HexColor('#333333'))
        c.rect(2*cm, table_top-1*cm, 25.5*cm, 1*cm, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setLineWidth(1)
        c.rect(2*cm, table_bottom, 25.5*cm, table_height) 
        
        col_x = [2*cm, 3.5*cm, 7.5*cm, 11.5*cm, 14.5*cm, 17.5*cm, 21.5*cm, 24.5*cm, 27.5*cm]
        
        for x in col_x[1:-1]:
            c.line(x, table_top, x, table_bottom)
            
        c.setFillColor(colors.white)
        c.setFont(font_name, 14)
        c.drawCentredString((col_x[0]+col_x[1])/2, table_top-0.7*cm, "No.")
        c.drawCentredString((col_x[1]+col_x[2])/2, table_top-0.7*cm, "ใบวางบิล")
        c.drawCentredString((col_x[2]+col_x[3])/2, table_top-0.7*cm, "ใบกำกับ#")
        c.drawCentredString((col_x[3]+col_x[4])/2, table_top-0.7*cm, "วันที่")
        c.drawCentredString((col_x[4]+col_x[5])/2, table_top-0.7*cm, "ครบกำหนด")
        c.drawCentredString((col_x[5]+col_x[6])/2, table_top-0.7*cm, "จำนวนเงิน")
        c.drawCentredString((col_x[6]+col_x[7])/2, table_top-0.7*cm, "ยอดคงค้าง")
        c.drawCentredString((col_x[7]+col_x[8])/2, table_top-0.7*cm, "ยอดชำระ")
        
        # --- ข้อมูลในตาราง ---
        c.setFillColor(colors.black)
        
        data_y = table_top - 1.5*cm
        for i, inv in enumerate(invoices):
            c.setFont(font_name, 16)
            c.drawCentredString((col_x[0]+col_x[1])/2, data_y, str(i+1))
            c.drawCentredString((col_x[1]+col_x[2])/2, data_y, "ค่าเทอม/ค่าเล่าเรียน")
            
            c.setFont(font_name, 14)
            c.drawCentredString((col_x[2]+col_x[3])/2, data_y, str(inv['doc_no']))
            c.drawCentredString((col_x[3]+col_x[4])/2, data_y, str(today_str)) 
            
            c.setFont(font_name, 16)
            c.drawCentredString((col_x[5]+col_x[6])/2, data_y, f"{inv['paid']:,.2f}") 
            c.drawCentredString((col_x[6]+col_x[7])/2, data_y, f"{inv['remain']:,.2f}")
            c.drawCentredString((col_x[7]+col_x[8])/2, data_y, f"{inv['paid']:,.2f}")
            
            data_y -= row_height 
            
        if len(invoices) > 1:
            c.setFont(font_name, 16)
            c.drawCentredString((col_x[1]+col_x[2])/2, data_y, "รวมยอดชำระ")
            c.drawCentredString((col_x[7]+col_x[8])/2, data_y, f"{total_amount:,.2f}")
        
        # --- ส่วนสรุปยอด ---
        summary_y = table_bottom - 1 * cm
        
        c.drawString(2.5*cm, summary_y, f"({amount_text})")
        c.drawString(22*cm, summary_y, "รวมเป็นเงิน")
        
        box_y = table_bottom - 1.5 * cm
        c.rect(24.5*cm, box_y, 3*cm, 1*cm)
        c.drawCentredString((col_x[7]+col_x[8])/2, box_y + 0.3*cm, f"{total_amount:,.2f}")
        
        # --- ท้ายบิล ---
        footer_y1 = table_bottom - 2.5 * cm
        footer_y2 = table_bottom - 3.5 * cm
        footer_y3 = table_bottom - 4.5 * cm
        footer_y4 = table_bottom - 5.3 * cm
        
        c.setFont(font_name, 16)
        c.drawString(2*cm, footer_y1, "การชำระเงินด้วยเช็คจะเสร็จสมบูรณ์เมื่อบริษัทได้รับเงินตามเช็คเรียบร้อย")
        c.drawString(2*cm, footer_y2, "เงินสด ....................... เช็คธนาคาร ....................... เช็คเลขที่ ....................... ลงวันที่ ......./......./....... จำนวนเงิน .......................")
        c.drawString(2*cm, footer_y3, "ในนามโรงเรียนศิริมงคลศึกษา บางบัวทอง")
        c.drawString(2*cm, footer_y4, "ผู้รับเงิน ........................................ วันที่ ......./......./.......      ผู้รับมอบอำนาจ ........................................")
        
        c.showPage()
        
    c.save()
    packet.seek(0)
    return packet


# --- ฟังก์ชันดึงข้อมูลจาก Google Sheet ---
@st.cache_data(ttl=60)
def pull_google_sheet_data(sheet_url):
    results = []
    try:
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return []
        
        sheet_id = match.group(1)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        df_gs = pd.read_csv(csv_url)
        
        for idx, row in df_gs.iterrows():
            try:
                col_amount = [c for c in df_gs.columns if 'ยอดเงิน' in str(c)]
                amount_raw = str(row[col_amount[-1]]).replace(',', '') if col_amount else "0"
                
                if amount_raw.replace('.','',1).isdigit():
                    amount = float(amount_raw)
                    if amount > 0:
                        title_student = str(row.iloc[4]).strip() 
                        first_name = str(row.iloc[5]).strip()
                        last_name = str(row.iloc[6]).strip()
                        full_name = f"{first_name} {last_name}"
                        
                        grade_raw = str(row.iloc[7]).strip() 
                        main_grade, sub_grade = get_grade_info(grade_raw)
                        gender = extract_gender(full_name, title_student)
                        
                        raw_time = str(row.iloc[0]).split(' ')[0] 
                        try:
                            d, m, y = raw_time.split('/')
                            year = int(y)
                            if year < 2500: year += 543
                            timestamp = f"{int(d):02d}/{int(m):02d}/{year}"
                        except:
                            timestamp = raw_time
                        
                        results.append({
                            'รหัสนักเรียน': '-', 
                            'ชื่อ-นามสกุล': full_name,
                            'เพศ': gender,
                            'กลุ่มช่วงชั้น': main_grade,
                            'พนักงานขาย (ระดับชั้นย่อย)': sub_grade,
                            'เอกสารอ้างอิง': '-',
                            'วันที่จ่ายเงิน': timestamp, 
                            'เลขที่ใบเสร็จ': 'โอนผ่านฟอร์ม', 
                            'ยอดค้างเดิม (บาท)': amount, 
                            'ยอดที่จ่าย (บาท)': amount,
                            'ยอดคงเหลือล่าสุด (บาท)': 0,
                            'รายการบิล': [{'doc_no': '-', 'bill': amount, 'paid': amount, 'remain': 0}],
                            'อ้างอิงไฟล์': 'Google Sheet'
                        })
            except Exception:
                continue
                
    except Exception as e:
        st.error(f"⚠️ ไม่สามารถเชื่อมต่อกับ Google Sheet ได้ รายละเอียด: {e}")
        
    return results

# --- ฟังก์ชันอ่านไฟล์ CSV Express ---
def process_csv(file):
    results = []
    try:
        content = file.getvalue().decode('utf-8')
    except UnicodeDecodeError:
        content = file.getvalue().decode('cp874', errors='ignore')
        
    reader = csv.reader(io.StringIO(content))
    sum_bill = 0.0
    sum_paid = 0.0
    doc_list = [] 
    doc_date_list = [] 
    pay_date_list = [] 
    salesperson_list = [] 
    receipt_no_list = []
    invoices_paid = [] 
    
    current_name = ""
    
    for row in reader:
        if not row: continue
        non_empty = [x.strip() for x in row if x.strip()]
        if not non_empty: continue
        
        for cell in row:
            clean_cell = cell.strip()
            if clean_cell.startswith('RE') and clean_cell not in receipt_no_list:
                receipt_no_list.append(clean_cell)

        if len(non_empty) >= 5 and non_empty[1] == "" and non_empty[2] == "" and non_empty[3] != "" and non_empty[4] != "":
            if "หน้า" not in non_empty[3] and "พนักงานขาย" not in non_empty[3] and "ประเภทลูกค้า" not in non_empty[1]:
                current_name = " ".join(non_empty[3].split())

        if '/' in non_empty[0] and len(non_empty) >= 5:
            try:
                if non_empty[1].startswith('IV'):
                    doc_date_list.append(non_empty[0])
                    doc_list.append(non_empty[1])
                    
                bill_str = non_empty[-3].replace(',', '')
                paid_str = non_empty[-2].replace(',', '')
                remain_str = non_empty[-1].replace(',', '')
                
                if bill_str.replace('.','',1).isdigit() and paid_str.replace('.','',1).isdigit() and remain_str.replace('.','',1).isdigit():
                    bill = float(bill_str)
                    paid = float(paid_str)
                    remain = float(remain_str)
                    
                    if len(non_empty) >= 6:
                        sales_raw = non_empty[2]
                        if sales_raw and not sales_raw.startswith('RE') and not sales_raw.replace('.','').isdigit():
                            salesperson_list.append(sales_raw) 
                    
                    sum_bill += bill
                    sum_paid += paid
                    
                    if paid > 0:
                        invoices_paid.append({
                            'doc_no': non_empty[1], 
                            'bill': bill, 
                            'paid': paid, 
                            'remain': remain 
                        })
            except ValueError:
                pass
                
        if len(row) >= 10 and not row[1].strip().startswith('รวม'):
            if row[8].strip() and not row[7].strip():
                for cell in row[8:]:
                    cell_str = cell.strip()
                    if len(cell_str) >= 6 and cell_str.count('/') >= 1:
                        if cell_str not in pay_date_list:
                            pay_date_list.append(cell_str)
                        break
                        
        if non_empty[0] == "รวมลูกค้า":
            try:
                name = " ".join(non_empty[1].split())
                code = non_empty[2]
                total_remain = float(non_empty[-1].replace(',', ''))
                
                if sum_bill == 0 and total_remain > 0:
                    sum_bill = total_remain
                
                docs_str = ", ".join(doc_list)
                receipts_str = receipt_no_list[0] if receipt_no_list else ""
                
                sales_raw = salesperson_list[0] if salesperson_list else ""
                main_grade, sub_grade = get_grade_info(sales_raw)
                gender = extract_gender(name)
                
                if pay_date_list:
                    dates_str = pay_date_list[0]
                elif doc_date_list:
                    dates_str = doc_date_list[0]
                else:
                    dates_str = ""
                
                results.append({
                    'รหัสนักเรียน': code,
                    'ชื่อ-นามสกุล': name,
                    'เพศ': gender,
                    'กลุ่มช่วงชั้น': main_grade,
                    'พนักงานขาย (ระดับชั้นย่อย)': sub_grade,
                    'เอกสารอ้างอิง': docs_str,
                    'วันที่จ่ายเงิน': dates_str, 
                    'เลขที่ใบเสร็จ': receipts_str, 
                    'ยอดค้างเดิม (บาท)': round(sum_bill, 2),
                    'ยอดที่จ่าย (บาท)': round(sum_paid, 2),
                    'ยอดคงเหลือล่าสุด (บาท)': round(total_remain, 2),
                    'รายการบิล': invoices_paid, 
                    'อ้างอิงไฟล์': file.name
                })
                
                sum_bill = 0.0
                sum_paid = 0.0
                doc_list = []
                doc_date_list = []
                pay_date_list = []
                salesperson_list = []
                receipt_no_list = []
                invoices_paid = []
                current_name = ""
            except Exception:
                pass
                
    return results


# ==========================================
# หน้าจอหลัก (UI) และ Session State
# ==========================================
st.title("📊 โปรแกรมดึงข้อมูลและออกใบเสร็จ (พร้อม Dashboard)")

if 'processed_data' not in st.session_state:
    st.session_state['processed_data'] = []

st.subheader("1️⃣ ข้อมูลจาก Google Form (สลิปโอนเงิน)")
gsheet_url = st.text_input("ลิงก์ Google Sheet:", "https://docs.google.com/spreadsheets/d/153j9DQjxc4ucll6myNsQNMN-rQuK9DxChft0Vh69LFU/edit?usp=sharing")
use_gsheet = st.checkbox("✅ ดึงข้อมูลอัตโนมัติจาก Google Form", value=True)

st.divider()

st.subheader("2️⃣ ข้อมูลจากโปรแกรม Express (จ่ายเงินสด/เช็ค)")
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ CSV", type=['csv'], accept_multiple_files=True)

if st.button("🚀 ประมวลผลข้อมูล"):
    csv_data = []
    
    if uploaded_files:
        for file in uploaded_files:
            csv_data.extend(process_csv(file))
            
    csv_dict = {}
    for r in csv_data:
        cname = clean_name_th(r['ชื่อ-นามสกุล'])
        csv_dict[cname] = r
        
    all_data = []
    
    if use_gsheet and gsheet_url:
        gsheet_data = pull_google_sheet_data(gsheet_url)
        
        for g in gsheet_data:
            cname = clean_name_th(g['ชื่อ-นามสกุล'])
            
            if cname in csv_dict:
                csv_record = csv_dict[cname]
                
                g['รหัสนักเรียน'] = csv_record['รหัสนักเรียน']
                g['ยอดค้างเดิม (บาท)'] = csv_record['ยอดค้างเดิม (บาท)']
                
                if g['เพศ'] == 'ไม่ระบุ': g['เพศ'] = csv_record['เพศ']
                if g['กลุ่มช่วงชั้น'] == 'ไม่ระบุ': g['กลุ่มช่วงชั้น'] = csv_record['กลุ่มช่วงชั้น']
                if g['พนักงานขาย (ระดับชั้นย่อย)'] == 'ไม่ระบุ': g['พนักงานขาย (ระดับชั้นย่อย)'] = csv_record['พนักงานขาย (ระดับชั้นย่อย)']
                
                g['ยอดคงเหลือล่าสุด (บาท)'] = g['ยอดค้างเดิม (บาท)'] - g['ยอดที่จ่าย (บาท)']
                
                if csv_record['รายการบิล']:
                    g['รายการบิล'][0]['doc_no'] = csv_record['รายการบิล'][0]['doc_no']
                    g['รายการบิล'][0]['remain'] = g['ยอดคงเหลือล่าสุด (บาท)']
                else:
                    g['รายการบิล'][0]['doc_no'] = csv_record['เอกสารอ้างอิง']
                
                del csv_dict[cname]
            
            all_data.append(g)
            
    all_data.extend(list(csv_dict.values()))
    
    st.session_state['processed_data'] = all_data

# ==========================================
# แสดงผลข้อมูลเมื่อมีการประมวลผลแล้ว
# ==========================================
if st.session_state['processed_data']:
    df = pd.DataFrame(st.session_state['processed_data'])
    df_paid = df[df['ยอดที่จ่าย (บาท)'] > 0].copy()
    
    tab1, tab2 = st.tabs(["📄 สรุปยอดและใบเสร็จ", "📈 แดชบอร์ดสรุป (Dashboard)"])
    
    with tab1:
        st.success(f"✅ ประมวลผลเสร็จสิ้น! พบผู้ชำระเงิน {len(df_paid)} รายการ จากทั้งหมด {len(df)} รายการ")
        
        display_cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'เพศ', 'พนักงานขาย (ระดับชั้นย่อย)', 'เอกสารอ้างอิง', 'วันที่จ่ายเงิน', 'เลขที่ใบเสร็จ', 'ยอดค้างเดิม (บาท)', 'ยอดที่จ่าย (บาท)', 'ยอดคงเหลือล่าสุด (บาท)', 'อ้างอิงไฟล์']
        df_display = df[display_cols]
        
        col1, col2 = st.columns(2)
        
        with col1:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_display.to_excel(writer, index=False, sheet_name='รายงานสรุปยอด')
            st.download_button("📥 1. ดาวน์โหลดตารางรวม (Excel)", data=output_excel.getvalue(), file_name=f"รายงานค่าเทอม_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
        with col2:
            if not df_paid.empty:
                if not has_font:
                    st.warning("⚠️ ไม่พบไฟล์ฟอนต์ THSarabunNew.ttf ในระบบ (ภาษาไทยใน PDF อาจไม่สมบูรณ์)")
                
                pdf_packet = create_receipts_pdf(df_paid)
                st.download_button(f"🖨️ 2. พิมพ์ใบเสร็จ {len(df_paid)} ใบ (PDF)", data=pdf_packet, file_name=f"ใบเสร็จรับเงิน_{datetime.datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        
        def highlight_paid(row):
            colors = [''] * len(row)
            paid = row['ยอดที่จ่าย (บาท)']
            if paid > 0:
                idx_paid = df_display.columns.get_loc('ยอดที่จ่าย (บาท)')
                colors[idx_paid] = 'background-color: #d4edda; color: #155724;'
            return colors
            
        styled_df = df_display.style.apply(highlight_paid, axis=1).format({'ยอดค้างเดิม (บาท)': '{:,.2f}', 'ยอดที่จ่าย (บาท)': '{:,.2f}', 'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'})
        st.dataframe(styled_df, use_container_width=True)

    with tab2:
        st.header("📈 แดชบอร์ดสรุปการรับชำระเงิน")
        
        if df_paid.empty:
            st.info("ยังไม่มีข้อมูลการชำระเงินในระบบ")
        else:
            # --- ส่วนฟิลเตอร์ (Drop-down) ---
            st.markdown("**🔍 คัดกรองข้อมูล (Filters)**")
            fcol1, fcol2 = st.columns(2)
            
            gender_list = ['ทั้งหมด'] + list(df_paid['เพศ'].unique())
            selected_gender = fcol1.selectbox("เลือกเพศ:", gender_list)
            
            grade_list = ['ทั้งหมด'] + list(df_paid['กลุ่มช่วงชั้น'].unique())
            selected_grade = fcol2.selectbox("เลือกกลุ่มช่วงชั้น:", grade_list)
            
            # กรองข้อมูลตาม Drop-down
            df_filtered = df_paid.copy()
            if selected_gender != 'ทั้งหมด':
                df_filtered = df_filtered[df_filtered['เพศ'] == selected_gender]
            if selected_grade != 'ทั้งหมด':
                df_filtered = df_filtered[df_filtered['กลุ่มช่วงชั้น'] == selected_grade]
                
            # แสดงตัวเลขหลังกรอง
            total_amt = df_filtered['ยอดที่จ่าย (บาท)'].sum()
            total_ppl = len(df_filtered)
            
            mcol1, mcol2 = st.columns(2)
            mcol1.metric("👥 จำนวนนักเรียนที่ชำระแล้ว (ตามเงื่อนไข)", f"{total_ppl} คน")
            mcol2.metric("💰 ยอดรับชำระรวม (ตามเงื่อนไข)", f"{total_amt:,.2f} บาท")
            
            st.divider()
            
            # --- ส่วนกราฟ (Drop-down) ---
            view_type = st.selectbox(
                "📊 เลือกรูปแบบกราฟสรุปยอด:",
                ["🏫 สรุปตามกลุ่มช่วงชั้น (อนุบาล/ประถมต้น/ประถมปลาย)", 
                 "📚 สรุปตามระดับชั้นย่อย (อ.1 - ป.6)", 
                 "👦👧 สรุปตามเพศ (ชาย/หญิง)"]
            )
            
            if len(df_filtered) > 0:
                if "กลุ่มช่วงชั้น" in view_type:
                    summary = df_filtered.groupby('กลุ่มช่วงชั้น')['ยอดที่จ่าย (บาท)'].sum().reset_index()
                    st.bar_chart(summary.set_index('กลุ่มช่วงชั้น'))
                    st.dataframe(summary.style.format({'ยอดที่จ่าย (บาท)': '{:,.2f}'}), use_container_width=True)
                    
                elif "ระดับชั้นย่อย" in view_type:
                    summary = df_filtered.groupby('พนักงานขาย (ระดับชั้นย่อย)')['ยอดที่จ่าย (บาท)'].sum().reset_index()
                    st.bar_chart(summary.set_index('พนักงานขาย (ระดับชั้นย่อย)'))
                    st.dataframe(summary.style.format({'ยอดที่จ่าย (บาท)': '{:,.2f}'}), use_container_width=True)
                    
                elif "เพศ" in view_type:
                    summary = df_filtered.groupby('เพศ')['ยอดที่จ่าย (บาท)'].sum().reset_index()
                    st.bar_chart(summary.set_index('เพศ'))
                    st.dataframe(summary.style.format({'ยอดที่จ่าย (บาท)': '{:,.2f}'}), use_container_width=True)
            else:
                st.warning("ไม่มีข้อมูลตรงกับเงื่อนไขที่เลือก")
