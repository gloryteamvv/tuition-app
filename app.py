import streamlit as st
import pandas as pd
import csv
import io
import datetime

st.set_page_config(page_title="ระบบสรุปยอดค่าเทอม", layout="wide")
st.title("📊 โปรแกรมดึงข้อมูลชำระค่าเทอมจาก Express")
st.markdown("ระบบจะดึง **ยอดในบิล (ยอดค้างเดิม)** และ **ยอดชำระ (ยอดที่จ่าย)** จากไฟล์ CSV โดยตรง")

def process_csv(file):
    results = []
    # รองรับภาษาไทยทั้ง utf-8 และ cp874
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
        
        # 1. ค้นหาบรรทัดใบแจ้งหนี้ (มีวันที่และเอกสาร IV) เพื่อเก็บยอด
        if '/' in non_empty[0] and len(non_empty) >= 4:
            try:
                if non_empty[1].startswith('IV'):
                    bill = float(non_empty[-3].replace(',', ''))
                    paid = float(non_empty[-2].replace(',', ''))
                    sum_bill += bill
                    sum_paid += paid
            except ValueError:
                pass
                
        # 2. ค้นหาบรรทัดสรุปรวมลูกค้า
        if non_empty[0] == "รวมลูกค้า":
            try:
                name = " ".join(non_empty[1].split())
                code = non_empty[2]
                total_remain = float(non_empty[-1].replace(',', ''))
                
                # กรณีดึงบิลไม่ได้ ให้ดึงยอดคงเหลือมาเป็นตั้งต้นแทน
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
                
                # รีเซ็ตตัวเลขเพื่อเตรียมนับของนักเรียนคนต่อไป
                sum_bill = 0.0
                sum_paid = 0.0
            except Exception:
                pass
                
    return results

# ==========================================
# หน้าจออัปโหลดและแสดงผล
# ==========================================
uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ CSV จากโปรแกรม Express", type=['csv'], accept_multiple_files=True)

if st.button("ประมวลผลข้อมูล"):
    if uploaded_files:
        all_data = []
        for file in uploaded_files:
            all_data.extend(process_csv(file))
            
        if all_data:
            df = pd.DataFrame(all_data)
            
            # เรียงลำดับคอลัมน์
            cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดค้างเดิม (บาท)', 'ยอดที่จ่าย (บาท)', 'ยอดคงเหลือล่าสุด (บาท)', 'อ้างอิงไฟล์']
            df = df[cols]
            
            def highlight_paid(row):
                colors = [''] * len(row)
                paid = row['ยอดที่จ่าย (บาท)']
                
                # สาดสีเขียวเฉพาะคนที่จ่ายเงิน
                if paid > 0:
                    idx_paid = df.columns.get_loc('ยอดที่จ่าย (บาท)')
                    colors[idx_paid] = 'background-color: #d4edda; color: #155724;'
                return colors

            st.success(f"✅ ดึงข้อมูลเสร็จสิ้น! พบรายชื่อทั้งหมด {len(df)} รายการ")
            
            styled_df = df.style.apply(highlight_paid, axis=1).format({
                'ยอดค้างเดิม (บาท)': '{:,.2f}',
                'ยอดที่จ่าย (บาท)': '{:,.2f}',
                'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'
            })
            st.dataframe(styled_df, use_container_width=True)
            
            # ส่งออกเป็น Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='รายงานสรุปยอด')
            
            st.download_button(
                label="📥 ดาวน์โหลดตาราง (Excel)",
                data=output.getvalue(),
                file_name=f"รายงานค่าเทอม_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("ไม่พบข้อมูลลูกหนี้ในไฟล์ที่อัปโหลด")
