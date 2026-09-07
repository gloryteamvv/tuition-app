import streamlit as st
import pandas as pd
import csv
import io
import datetime
import os

# ไลบรารีสำหรับสร้าง PDF และคำอ่านภาษาไทย
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from bahttext import bahttext

st.set_page_config(page_title="ระบบสรุปยอดค่าเทอม", layout="wide")

# ==========================================
# ลงทะเบียนฟอนต์ภาษาไทยสำหรับ PDF
# ==========================================
# กรุณาตรวจสอบว่ามีไฟล์ฟอนต์นี้อัปโหลดอยู่บน GitHub ในโฟลเดอร์เดียวกัน
font_path = "THSarabunNew.ttf"
has_font = False
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('THSarabun', font_path))
    has_font = True

def create_receipts_pdf(df_paid):
    """ฟังก์ชันสร้างไฟล์ PDF ใบเสร็จรับเงิน"""
    packet = io.BytesIO()
    # ใช้ A4 แนวนอนตามรูปถ่ายใบเสร็จ
    c = canvas.Canvas(packet, pagesize=landscape(A4))
    
    if has_font:
        font_name = 'THSarabun'
    else:
        font_name = 'Helvetica' # กรณีไม่มีฟอนต์
    
    for idx, row in df_paid.iterrows():
        student_code = row['รหัสนักเรียน']
        student_name = row['ชื่อ-นามสกุล']
        amount = row['ยอดที่จ่าย (บาท)']
        amount_text = bahttext(amount) # แปลงเป็นคำอ่าน
        today_str = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # วาดโครงสร้างใบเสร็จ (ปรับแกน X, Y เป็นเซนติเมตร)
        c.setFont(font_name, 16)
        
        # ส่วนหัวบริษัท
        c.drawString(2*cm, 18*cm, "โรงเรียน ศิริมงคลศึกษา บางบัวทอง")
        c.setFont(font_name, 12)
        c.drawString(2*cm, 17.5*cm, "เลขที่ 91/1 ซอยศิริมงคล ถนนบางกรวย-ไทรน้อย ต.บางรักพัฒนา อ.บางบัวทอง จังหวัด นนทบุรี")
        c.drawString(2*cm, 17*cm, "FAX. 02-920-8133 TEL.08")
        c.drawString(2*cm, 16.5*cm, "เลขประจำตัวผู้เสียภาษี 0994000242379")
        
        # คำว่า ใบเสร็จรับเงิน
        c.setFont(font_name, 20)
        c.drawCentredString(14*cm, 18*cm, "ใบเสร็จรับเงิน")
        
        # ข้อมูลเอกสารมุมขวา
        c.setFont(font_name, 14)
        c.drawString(20*cm, 18*cm, "เลขที่ใบเสร็จ: ..............................")
        c.drawString(20*cm, 17.2*cm, f"วันที่: {today_str}")
        c.drawString(20*cm, 16.4*cm, "พนักงานขาย: ..............................")
        
        # ข้อมูลลูกค้า
        c.drawString(2*cm, 15*cm, f"ลูกค้า: {student_code}")
        c.drawString(2*cm, 14.3*cm, f"ชื่อลูกค้า: {student_name}")
        c.drawString(2*cm, 13.6*cm, "ที่อยู่ลูกค้า: ........................................................................")
        
        # ตารางรายการ
        # วาดเส้นขอบตารางหลัก
        c.rect(2*cm, 6*cm, 25*cm, 6*cm)
        # ขีดเส้นใต้หัวตาราง
        c.line(2*cm, 11*cm, 27*cm, 11*cm)
        
        # หัวคอลัมน์
        c.drawString(2.5*cm, 11.3*cm, "No.")
        c.drawString(5*cm, 11.3*cm, "ใบวางบิล")
        c.drawString(9*cm, 11.3*cm, "ใบกำกับ#")
        c.drawString(13*cm, 11.3*cm, "วันที่")
        c.drawString(16*cm, 11.3*cm, "ครบกำหนด")
        c.drawString(19*cm, 11.3*cm, "จำนวนเงิน")
        c.drawString(22*cm, 11.3*cm, "ยอดคงค้าง")
        c.drawString(24.5*cm, 11.3*cm, "ยอดชำระ")
        
        # ข้อมูลรายการ (บรรทัดที่ 1)
        c.drawString(2.5*cm, 10*cm, "1")
        c.drawString(5*cm, 10*cm, "ค่าเทอม/ค่าเล่าเรียน")
        # ตรงนี้เราใส่ยอดเงินที่จ่ายในช่อง "จำนวนเงิน" และ "ยอดชำระ"
        c.drawString(19*cm, 10*cm, f"{amount:,.2f}")
        c.drawString(24.5*cm, 10*cm, f"{amount:,.2f}")
        
        # เส้นกั้นรวมเงิน
        c.line(2*cm, 7.5*cm, 27*cm, 7.5*cm)
        c.drawString(2*cm, 6.5*cm, f"({amount_text})")
        c.drawString(16*cm, 6.5*cm, "รวมเป็นเงิน")
        c.drawString(24.5*cm, 6.5*cm, f"{amount:,.2f}")
        
        # ท้ายบิล
        c.drawString(2*cm, 5*cm, "การชำระเงินด้วยเช็คจะสมบูรณ์เมื่อบริษัทได้รับเงินตามเช็คเรียบร้อย")
        c.drawString(2*cm, 4*cm, "เงินสด ....................... เช็คธนาคาร ....................... เช็คเลขที่ ....................... ลงวันที่ ......./......./....... จำนวนเงิน .......................")
        c.drawString(2*cm, 3*cm, "ผู้รับเงิน ........................................ วันที่ ......./......./.......          ในนาม โรงเรียน ศิริมงคลศึกษา บางบัวทอง")
        c.drawString(15*cm, 3*cm, "ผู้รับมอบอำนาจ ........................................")
        
        # จบหน้า 1 คน
        c.showPage()
        
    c.save()
    packet.seek(0)
    return packet

# ==========================================
# หน้าจอหลัก (ดึงข้อมูลเหมือนเดิม)
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
    
    for row in reader:
        if not row: continue
        non_empty = [x.strip() for x in row if x.strip()]
        if not non_empty: continue
        
        if '/' in non_empty[0] and len(non_empty) >= 4:
            try:
                if non_empty[1].startswith('IV') or non_empty[1].startswith('RE'):
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
                
                results.append({
                    'รหัสนักเรียน': code,
                    'ชื่อ-นามสกุล': name,
                    'ยอดค้างเดิม (บาท)': round(sum_bill, 2),
                    'ยอดที่จ่าย (บาท)': round(sum_paid, 2),
                    'ยอดคงเหลือล่าสุด (บาท)': round(total_remain, 2),
                    'อ้างอิงไฟล์': file.name
                })
                sum_bill = 0.0
                sum_paid = 0.0
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
            cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดค้างเดิม (บาท)', 'ยอดที่จ่าย (บาท)', 'ยอดคงเหลือล่าสุด (บาท)', 'อ้างอิงไฟล์']
            df = df[cols]
            
            # กรองเฉพาะคนที่จ่ายเงิน เพื่อนำไปสร้างใบเสร็จ
            df_paid = df[df['ยอดที่จ่าย (บาท)'] > 0].copy()
            
            def highlight_paid(row):
                colors = [''] * len(row)
                paid = row['ยอดที่จ่าย (บาท)']
                if paid > 0:
                    idx_paid = df.columns.get_loc('ยอดที่จ่าย (บาท)')
                    colors[idx_paid] = 'background-color: #d4edda; color: #155724;'
                return colors

            st.success(f"✅ ประมวลผลเสร็จสิ้น! พบผู้ชำระเงิน {len(df_paid)} รายการ จากทั้งหมด {len(df)} รายการ")
            
            # --- ปุ่มดาวน์โหลด ---
            col1, col2 = st.columns(2)
            
            with col1:
                # 1. ดาวน์โหลด Excel
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='รายงานสรุปยอด')
                st.download_button("📥 1. ดาวน์โหลดตารางรวม (Excel)", data=output_excel.getvalue(), file_name=f"รายงานค่าเทอม_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
            with col2:
                # 2. ดาวน์โหลดใบเสร็จ PDF (เฉพาะคนจ่าย)
                if not df_paid.empty:
                    if not has_font:
                        st.warning("⚠️ ไม่พบไฟล์ฟอนต์ THSarabunNew.ttf ในระบบ (ภาษาไทยใน PDF อาจไม่สมบูรณ์)")
                    
                    pdf_packet = create_receipts_pdf(df_paid)
                    st.download_button(f"🖨️ 2. พิมพ์ใบเสร็จ {len(df_paid)} ใบ (PDF)", data=pdf_packet, file_name=f"ใบเสร็จรับเงิน_{datetime.datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            
            # --- แสดงตาราง ---
            styled_df = df.style.apply(highlight_paid, axis=1).format({'ยอดค้างเดิม (บาท)': '{:,.2f}', 'ยอดที่จ่าย (บาท)': '{:,.2f}', 'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'})
            st.dataframe(styled_df, use_container_width=True)
            
        else:
            st.warning("ไม่พบข้อมูลลูกหนี้")
