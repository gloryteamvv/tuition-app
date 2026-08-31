import streamlit as st
import pandas as pd
import csv
import io
import os
import datetime

st.set_page_config(page_title="ระบบเปรียบเทียบยอดค่าเทอม", layout="wide")
st.title("📊 โปรแกรมเปรียบเทียบและอัปเดตยอดค่าเทอมอัตโนมัติ")

# กำหนดชื่อไฟล์สำหรับเก็บฐานข้อมูลถาวร
DB_FILE = "master_database.csv"

def process_csv(file):
    outstanding_data = []
    content = file.getvalue().decode('cp874', errors='ignore')
    reader = csv.reader(io.StringIO(content))
    
    for row in reader:
        if not row: continue
        non_empty = [x.strip() for x in row if x.strip()]
        
        if non_empty and non_empty[0] == "รวมลูกค้า":
            try:
                student_name = non_empty[1]
                student_code = non_empty[2]
                total_str = non_empty[-1].replace(',', '')
                outstanding_data.append({
                    'รหัสนักเรียน': student_code,
                    'ชื่อ-นามสกุล': student_name,
                    'ยอดค้างชำระล่าสุด (บาท)': float(total_str)
                })
            except Exception:
                pass
    return outstanding_data

# ส่วนที่ 1: ตรวจสอบและโหลดฐานข้อมูลในระบบ
if os.path.exists(DB_FILE):
    df_old = pd.read_csv(DB_FILE)
    st.info(f"📁 ระบบตรวจพบฐานข้อมูลเดิม มีรายชื่อค้างชำระ {len(df_old)} รายการ (พร้อมเปรียบเทียบยอด)")
else:
    df_old = pd.DataFrame()
    st.warning("⚠️ ยังไม่มีฐานข้อมูลในระบบ (การอัปโหลดครั้งแรกจะถูกบันทึกเป็นฐานตั้งต้นโดยอัตโนมัติ)")

# ส่วนที่ 2: อัปโหลดข้อมูลใหม่
new_csvs = st.file_uploader("🆕 อัปโหลดไฟล์ CSV จากโปรแกรม Express เพื่อเช็คยอดล่าสุด", type=['csv'], accept_multiple_files=True)

if st.button("ประมวลผลและอัปเดตระบบ"):
    if new_csvs:
        all_data = []
        for file in new_csvs:
            all_data.extend(process_csv(file))
            
        if all_data:
            df_new = pd.DataFrame(all_data)
            
            # ถ้ามีข้อมูลเก่า ให้ทำการเปรียบเทียบ
            if not df_old.empty:
                df_old.rename(columns={'ยอดค้างชำระล่าสุด (บาท)': 'ยอดเดิม (บาท)'}, inplace=True)
                df_new.rename(columns={'ยอดค้างชำระล่าสุด (บาท)': 'ยอดใหม่ (บาท)'}, inplace=True)
                
                # เชื่อมตารางด้วยรหัสนักเรียน
                df_merge = pd.merge(df_old, df_new, on=['รหัสนักเรียน', 'ชื่อ-นามสกุล'], how='outer')
                df_merge['ยอดเดิม (บาท)'] = df_merge['ยอดเดิม (บาท)'].fillna(0)
                df_merge['ยอดใหม่ (บาท)'] = df_merge['ยอดใหม่ (บาท)'].fillna(0)
                df_merge['ส่วนต่าง (ชำระแล้ว)'] = df_merge['ยอดเดิม (บาท)'] - df_merge['ยอดใหม่ (บาท)']
                
                # จัดเรียงคอลัมน์
                cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดเดิม (บาท)', 'ยอดใหม่ (บาท)', 'ส่วนต่าง (ชำระแล้ว)']
                df_merge = df_merge[cols]
                
                # ฟังก์ชันไฮไลต์สี (เขียว=จ่ายแล้ว, แดง=ยอดเพิ่ม)
                def highlight_changes(row):
                    colors = [''] * len(row)
                    diff = row['ส่วนต่าง (ชำระแล้ว)']
                    
                    if diff > 0:
                        idx_new = df_merge.columns.get_loc('ยอดใหม่ (บาท)')
                        idx_diff = df_merge.columns.get_loc('ส่วนต่าง (ชำระแล้ว)')
                        colors[idx_new] = 'background-color: #d4edda; color: #155724;'
                        colors[idx_diff] = 'background-color: #d4edda; color: #155724;'
                    elif diff < 0:
                        idx_new = df_merge.columns.get_loc('ยอดใหม่ (บาท)')
                        idx_diff = df_merge.columns.get_loc('ส่วนต่าง (ชำระแล้ว)')
                        colors[idx_new] = 'background-color: #f8d7da; color: #721c24;'
                        colors[idx_diff] = 'background-color: #f8d7da; color: #721c24;'
                    return colors

                st.write("**ผลการเปรียบเทียบความเคลื่อนไหว:**")
                styled_df = df_merge.style.apply(highlight_changes, axis=1).format({
                    'ยอดเดิม (บาท)': '{:,.2f}',
                    'ยอดใหม่ (บาท)': '{:,.2f}',
                    'ส่วนต่าง (ชำระแล้ว)': '{:,.2f}'
                })
                st.dataframe(styled_df, use_container_width=True)
                
                # บันทึกทับเป็นฐานข้อมูลใหม่สำหรับใช้รอบหน้า
                df_new_to_save = df_new.rename(columns={'ยอดใหม่ (บาท)': 'ยอดค้างชำระล่าสุด (บาท)'})
                df_new_to_save.to_csv(DB_FILE, index=False)
                st.success("✅ โปรแกรมได้บันทึกยอดใหม่ล่าสุดนี้ ไว้เป็นฐานข้อมูลสำหรับเปรียบเทียบในรอบถัดไปเรียบร้อยแล้ว!")
                
                # ดาวน์โหลด Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_merge.to_excel(writer, index=False, sheet_name='รายงานสรุปยอด')
                
                st.download_button(
                    label="📥 ดาวน์โหลดตารางเปรียบเทียบ (Excel)",
                    data=output.getvalue(),
                    file_name=f"เปรียบเทียบยอด_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            else:
                # กรณีเพิ่งเริ่มใช้งานครั้งแรก (ยังไม่มีข้อมูลในระบบ)
                st.write("**ข้อมูลเริ่มต้นในระบบ:**")
                st.dataframe(df_new.style.format({'ยอดค้างชำระล่าสุด (บาท)': '{:,.2f}'}), use_container_width=True)
                df_new.to_csv(DB_FILE, index=False)
                st.success("✅ สร้างฐานข้อมูลตั้งต้นเรียบร้อยแล้ว! ในการอัปโหลดครั้งต่อไป ระบบจะนำยอดมาเปรียบเทียบให้ทันที")
