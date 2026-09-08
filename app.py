import streamlit as st
import pandas as pd
import csv
import io
import datetime
import os

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
        salesperson = row.get('พนักงานขาย (ระดับชั้น)', '') 
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
        table_top = 11*cm
        # ขยับเส้นขอบล่างตารางขึ้นมาจาก 6cm เป็น 8cm
        table_bottom = 8*cm
        
        c.setFillColor(colors.HexColor('#333333'))
        c.rect(2*cm, table_top-1*cm, 25.5*cm, 1*cm, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setLineWidth(1)
        # วาดกรอบตารางใหม่ให้พอดีกับที่ขยับขึ้น
        c.rect(2*cm, table_bottom, 25.5*cm, table_top-table_bottom) 
        
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
            
            data_y -= 0.8 * cm 
            
        if len(invoices) > 1:
            c.setFont(font_name, 16)
            c.drawCentredString((col_x[1]+col_x[2])/2, data_y, "รวมยอดชำระ")
            c.drawCentredString((col_x[7]+col_x[8])/2, data_y, f"{total_amount:,.2f}")
        
        # --- ส่วนสรุปยอดล่างสุด (ขยับขึ้น 2cm) ---
        c.drawString(2.5*cm, 7*cm, f"({amount_text})")
        c.drawString(22*cm, 7*cm, "รวมเป็นเงิน")
        
        c.rect(24.5*cm, 6.5*cm, 3*cm, 1*cm)
        c.drawCentredString((col_x[7]+col_x[8])/2, 6.8*cm, f"{total_amount:,.2f}")
        
        # --- ท้ายบิล (ขยับขึ้น 2cm) ---
        c.setFont(font_name, 16)
        c.drawString(2*cm, 5.5*cm, "การชำระเงินด้วยเช็คจะเสร็จสมบูรณ์เมื่อบริษัทได้รับเงินตามเช็คเรียบร้อย")
        c.drawString(2*cm, 4.5*cm, "เงินสด ....................... เช็คธนาคาร ....................... เช็คเลขที่ ....................... ลงวันที่ ......./......./....... จำนวนเงิน .......................")
        c.drawString(2*cm, 3.5*cm, "ในนามโรงเรียนศิริมงคลศึกษา บางบัวทอง")
        c.drawString(2*cm, 2.5*cm, "ผู้รับเงิน ........................................ วันที่ ......./......./.......      ผู้รับมอบอำนาจ ........................................")
        
        c.showPage()
        
    c.save()
    packet.seek(0)
    return packet

# ==========================================
# หน้าจอหลัก
# ==========================================
st.title("📊 โปรแกรมดึงข้อมูลและออกใบเสร็จ (Express)")

GRADE_MAP = {
    'ปถ1': 'ประถมศึกษาปีที่ 1',
    'ปถ2': 'ประถมศึกษาปีที่ 2',
    'ปถ3': 'ประถมศึกษาปีที่ 3',
    'ปถ4': 'ประถมศึกษาปีที่ 4',
    'ปถ5': 'ประถมศึกษาปีที่ 5',
    'ปถ6': 'ประถมศึกษาปีที่ 6',
    'อบ1': 'อนุบาล 1',
    'อบ2': 'อนุบาล 2',
    'อบ3': 'อนุบาล 3'
}

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
    
    for row in reader:
        if not row: continue
        non_empty = [x.strip() for x in row if x.strip()]
        if not non_empty: continue
        
        for cell in row:
            clean_cell = cell.strip()
            if clean_cell.startswith('RE') and clean_cell not in receipt_no_list:
                receipt_no_list.append(clean_cell)

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
                            sales_mapped = GRADE_MAP.get(sales_raw, sales_raw)
                            if sales_mapped not in salesperson_list:
                                salesperson_list.append(sales_mapped)
                    
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
                salesperson_str = salesperson_list[0] if salesperson_list else ""
                receipts_str = receipt_no_list[0] if receipt_no_list else ""
                
                if pay_date_list:
                    dates_str = pay_date_list[0]
                elif doc_date_list:
                    dates_str = doc_date_list[0]
                else:
                    dates_str = ""
                
                results.append({
                    'รหัสนักเรียน': code,
                    'ชื่อ-นามสกุล': name,
                    'เอกสารอ้างอิง': docs_str,
                    'วันที่จ่ายเงิน': dates_str, 
                    'พนักงานขาย (ระดับชั้น)': salesperson_str, 
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
            except Exception:
                pass
                
    return results

uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ CSV จาก Express", type=['csv'], accept_multiple_files=True)

if st.button("ประมวลผลข้อมูล"):
    if uploaded_files:
        all_data = []
        for file in uploaded_files:
            all_data.extend(process_csv(file))
            
        if all_data:
            df = pd.DataFrame(all_data)
            
            display_cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'เอกสารอ้างอิง', 'วันที่จ่ายเงิน', 'พนักงานขาย (ระดับชั้น)', 'เลขที่ใบเสร็จ', 'ยอดค้างเดิม (บาท)', 'ยอดที่จ่าย (บาท)', 'ยอดคงเหลือล่าสุด (บาท)', 'อ้างอิงไฟล์']
            df_display = df[display_cols]
            
            df_paid = df[df['ยอดที่จ่าย (บาท)'] > 0].copy()
            
            def highlight_paid(row):
                colors = [''] * len(row)
                paid = row['ยอดที่จ่าย (บาท)']
                if paid > 0:
                    idx_paid = df_display.columns.get_loc('ยอดที่จ่าย (บาท)')
                    colors[idx_paid] = 'background-color: #d4edda; color: #155724;'
                return colors

            st.success(f"✅ ประมวลผลเสร็จสิ้น! พบผู้ชำระเงิน {len(df_paid)} รายการ จากทั้งหมด {len(df)} รายการ")
            
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
            
            styled_df = df_display.style.apply(highlight_paid, axis=1).format({'ยอดค้างเดิม (บาท)': '{:,.2f}', 'ยอดที่จ่าย (บาท)': '{:,.2f}', 'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'})
            st.dataframe(styled_df, use_container_width=True)
            
        else:
            st.warning("ไม่พบข้อมูลลูกหนี้")
