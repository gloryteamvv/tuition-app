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
    """ฟังก์ชันสร้างไฟล์ PDF ใบเสร็จรับเงิน"""
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=landscape(A4))
    
    if has_font:
        font_name = 'THSarabun'
    else:
        font_name = 'Helvetica'
    
    for idx, row in df_paid.iterrows():
        student_code = row['รหัสนักเรียน']
        student_name = row['ชื่อ-นามสกุล']
        doc_no = row['เอกสารอ้างอิง']
        receipt_no = row['เลขที่ใบเสร็จ'] # ดึงเลขที่ใบเสร็จจากพนักงานขาย
        amount = row['ยอดที่จ่าย (บาท)']
        remain = row['ยอดคงเหลือล่าสุด (บาท)']
        amount_text = bahttext(amount)
        today_str = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # --- ส่วนหัว (Header) ---
        c.setFont(font_name, 22)
        c.drawString(2*cm, 18*cm, "โรงเรียนศิริมงคลศึกษา บางบัวทอง")
        
        c.setFont(font_name, 14)
        c.drawString(2*cm, 17.2*cm, "เลขที่ 91/1 ซอยศิริมงคล ถนนบางกรวย-ไทรน้อย ต.บางรัก")
        c.drawString(2*cm, 16.5*cm, "พัฒนา อ.บางบัวทอง จังหวัดนนทบุรี")
        c.drawString(2*cm, 15.8*cm, "FAX. 02-920-8133 TEL.08")
        c.drawString(2*cm, 15.1*cm, "เลขประจำตัวผู้เสียภาษี 0994000242379")
        
        c.setFont(font_name, 24)
        c.drawRightString(27.5*cm, 17*cm, "ใบเสร็จรับเงิน / Receipt")
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(2*cm, 14.5*cm, 27.5*cm, 14.5*cm)
        
        # --- ข้อมูลลูกค้าและเอกสาร ---
        c.setFont(font_name, 16)
        c.drawString(2*cm, 13.5*cm, f"ลูกค้า (รหัสลูกค้า)     {student_code}")
        c.drawString(2*cm, 12.8*cm, f"ชื่อ-สกุล                  {student_name}")
        c.drawString(2*cm, 12.1*cm, "ที่อยู่                       ........................................................................")
        
        # ใส่เลขที่ใบเสร็จที่ดึงมา
        c.drawString(17*cm, 13.5*cm, f"เลขที่ใบเสร็จ     {receipt_no}")
        c.drawString(17*cm, 12.8*cm, f"วันที่                 {today_str}")
        c.drawString(17*cm, 12.1*cm, "พนักงานขาย     ..............................")
        
        # --- ตารางรายการ ---
        table_top = 11*cm
        table_bottom = 6*cm
        
        c.setFillColor(colors.HexColor('#333333'))
        c.rect(2*cm, table_top-1*cm, 25.5*cm, 1*cm, fill=1, stroke=1)
        
        c.setFillColor(colors.black)
        c.setLineWidth(1)
        c.rect(2*cm, table_bottom, 25.5*cm, 5*cm) 
        
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
        c.setFont(font_name, 16)
        
        data_y = table_top - 1.7*cm
        c.drawCentredString((col_x[0]+col_x[1])/2, data_y, "1")
        c.drawCentredString((col_x[1]+col_x[2])/2, data_y, "ค่าเทอม/ค่าเล่าเรียน")
        
        c.setFont(font_name, 14)
        c.drawCentredString((col_x[2]+col_x[3])/2, data_y, str(doc_no))
        c.setFont(font_name, 16)
        
        c.drawCentredString((col_x[6]+col_x[7])/2, data_y, f"{remain:,.2f}")
        c.drawCentredString((col_x[7]+col_x[8])/2, data_y, f"{amount:,.2f}")
        
        # --- ส่วนสรุปยอด ---
        c.drawString(2.5*cm, 5*cm, f"({amount_text})")
        c.drawString(22*cm, 5*cm, "รวมเป็นเงิน")
        
        c.rect(24.5*cm, 4.5*cm, 3*cm, 1*cm)
        c.drawCentredString((col_x[7]+col_x[8])/2, 4.8*cm, f"{amount:,.2f}")
        
        # --- ท้ายบิล ---
        c.setFont(font_name, 16)
        c.drawString(2*cm, 3.5*cm, "การชำระเงินด้วยเช็คจะเสร็จสมบูรณ์เมื่อบริษัทได้รับเงินตามเช็คเรียบร้อย")
        c.drawString(2*cm, 2.5*cm, "เงินสด ....................... เช็คธนาคาร ....................... เช็คเลขที่ ....................... ลงวันที่ ......./......./....... จำนวนเงิน .......................")
        c.drawString(2*cm, 1.5*cm, "ในนามโรงเรียนศิริมงคลศึกษา บางบัวทอง")
        c.drawString(2*cm, 0.7*cm, "ผู้รับเงิน ........................................ วันที่ ......./......./.......      ผู้รับมอบอำนาจ ........................................")
        
        c.showPage()
        
    c.save()
    packet.seek(0)
    return packet

# ==========================================
# หน้าจอหลัก
# ==========================================
st.title("📊 โปรแกรมดึงข้อมูลและออกใบเสร็จ (Express)")

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
    receipt_no_list = [] # เก็บพนักงานขายมาทำเป็นเลขที่ใบเสร็จ
    
    for row in reader:
        if not row: continue
        non_empty = [x.strip() for x in row if x.strip()]
        if not non_empty: continue
        
        if '/' in non_empty[0] and len(non_empty) >= 4:
            try:
                if non_empty[1].startswith('IV') or non_empty[1].startswith('RE'):
                    doc_list.append(non_empty[1])
                    
                    # ตำแหน่งพนักงานขายใน Express มักจะอยู่ก่อนจำนวนเงินในบิล
                    salesperson = non_empty[-4]
                    if salesperson and salesperson not in receipt_no_list:
                        receipt_no_list.append(salesperson)
                        
                    bill = float(non_empty[-3].replace(',', ''))
                    paid = float(non_empty[-2].replace(',', ''))
                    sum_bill += bill
                    sum_paid += paid
            except ValueError:
                pass
                
        if non_empty[0] == "รวมลูกค้า":
            try:
                name = " ".join(non_empty[1].split())
                code = non_empty[2]
                total_remain = float(non_empty[-1].replace(',', ''))
                
                if sum_bill == 0 and total_remain > 0:
                    sum_bill = total_remain
                
                docs_str = ", ".join(doc_list)
                receipts_str = ", ".join(receipt_no_list)
                
                results.append({
                    'รหัสนักเรียน': code,
                    'ชื่อ-นามสกุล': name,
                    'เอกสารอ้างอิง': docs_str,
                    'เลขที่ใบเสร็จ': receipts_str, # เพิ่มในตาราง
                    'ยอดค้างเดิม (บาท)': round(sum_bill, 2),
                    'ยอดที่จ่าย (บาท)': round(sum_paid, 2),
                    'ยอดคงเหลือล่าสุด (บาท)': round(total_remain, 2),
                    'อ้างอิงไฟล์': file.name
                })
                
                sum_bill = 0.0
                sum_paid = 0.0
                doc_list = []
                receipt_no_list = []
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
            # จัดเรียงคอลัมน์ใหม่ให้แสดงเลขที่ใบเสร็จด้วย
            cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'เอกสารอ้างอิง', 'เลขที่ใบเสร็จ', 'ยอดค้างเดิม (บาท)', 'ยอดที่จ่าย (บาท)', 'ยอดคงเหลือล่าสุด (บาท)', 'อ้างอิงไฟล์']
            df = df[cols]
            
            df_paid = df[df['ยอดที่จ่าย (บาท)'] > 0].copy()
            
            def highlight_paid(row):
                colors = [''] * len(row)
                paid = row['ยอดที่จ่าย (บาท)']
                if paid > 0:
                    idx_paid = df.columns.get_loc('ยอดที่จ่าย (บาท)')
                    colors[idx_paid] = 'background-color: #d4edda; color: #155724;'
                return colors

            st.success(f"✅ ประมวลผลเสร็จสิ้น! พบผู้ชำระเงิน {len(df_paid)} รายการ จากทั้งหมด {len(df)} รายการ")
            
            col1, col2 = st.columns(2)
            
            with col1:
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='รายงานสรุปยอด')
                st.download_button("📥 1. ดาวน์โหลดตารางรวม (Excel)", data=output_excel.getvalue(), file_name=f"รายงานค่าเทอม_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
            with col2:
                if not df_paid.empty:
                    if not has_font:
                        st.warning("⚠️ ไม่พบไฟล์ฟอนต์ THSarabunNew.ttf ในระบบ (ภาษาไทยใน PDF อาจไม่สมบูรณ์)")
                    
                    pdf_packet = create_receipts_pdf(df_paid)
                    st.download_button(f"🖨️ 2. พิมพ์ใบเสร็จ {len(df_paid)} ใบ (PDF)", data=pdf_packet, file_name=f"ใบเสร็จรับเงิน_{datetime.datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            
            styled_df = df.style.apply(highlight_paid, axis=1).format({'ยอดค้างเดิม (บาท)': '{:,.2f}', 'ยอดที่จ่าย (บาท)': '{:,.2f}', 'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'})
            st.dataframe(styled_df, use_container_width=True)
            
        else:
            st.warning("ไม่พบข้อมูลลูกหนี้")
