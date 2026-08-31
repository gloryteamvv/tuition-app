import streamlit as st
import pandas as pd
import csv
import io
import os
import datetime

st.set_page_config(page_title="ระบบเปรียบเทียบยอดค่าเทอม", layout="wide")
DB_FILE = "master_database.csv"

# ==========================================
# เมนูจัดการฐานข้อมูลด้านข้าง (Sidebar)
# ==========================================
with st.sidebar:
    st.header("⚙️ จัดการฐานข้อมูลตั้งต้น")
    
    if os.path.exists(DB_FILE):
        st.success("🟢 สถานะ: มีฐานข้อมูลในระบบ")
        with open(DB_FILE, "rb") as f:
            st.download_button(
                label="💾 ดาวน์โหลดฐานข้อมูลปัจจุบัน", 
                data=f, 
                file_name=f"database_backup_{datetime.datetime.now().strftime('%Y%m%d')}.csv", 
                mime="text/csv"
            )
        
        if st.button("🗑️ ล้างฐานข้อมูลเพื่อเริ่มใหม่"):
            os.remove(DB_FILE)
            st.rerun()
    else:
        st.warning("🔴 สถานะ: ยังไม่มีฐานข้อมูล")

    st.divider()
    
    st.subheader("เปลี่ยนไฟล์ฐานข้อมูลใหม่")
    st.write("อัปโหลดไฟล์ Excel/CSV (คอลัมน์: รหัส, ชื่อ, ยอดเงิน)")
    uploaded_db = st.file_uploader("เลือกไฟล์", type=['csv', 'xlsx'])
    
    if uploaded_db is not None:
        if st.button("🔄 อัปเดตเป็นฐานข้อมูลนี้"):
            try:
                if uploaded_db.name.lower().endswith('.csv'):
                    try:
                        df_upload = pd.read_csv(uploaded_db, encoding='utf-8')
                    except UnicodeDecodeError:
                        uploaded_db.seek(0)
                        df_upload = pd.read_csv(uploaded_db, encoding='cp874')
                else:
                    df_upload = pd.read_excel(uploaded_db, engine='openpyxl')
                
                if len(df_upload.columns) >= 3:
                    df_upload = df_upload.iloc[:, :3]
                    df_upload.columns = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดค้างเดิม (บาท)']
                    df_upload['ยอดค้างเดิม (บาท)'] = pd.to_numeric(df_upload['ยอดค้างเดิม (บาท)'], errors='coerce').fillna(0)
                    df_upload = df_upload[df_upload['ยอดค้างเดิม (บาท)'] != 0]
                    df_upload.to_csv(DB_FILE, index=False)
                    
                    st.success("บันทึกฐานข้อมูลใหม่สำเร็จ!")
                    st.rerun()
                else:
                    st.error("ไฟล์ต้องมีอย่างน้อย 3 คอลัมน์ (รหัสนักเรียน, ชื่อ-นามสกุล, ยอดเงิน)")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")

# ==========================================
# หน้าจอหลัก (Main Page)
# ==========================================
st.title("📊 โปรแกรมเปรียบเทียบและอัปเดตยอดค่าเทอมอัตโนมัติ")

def process_csv(file):
    outstanding_data = []
    content = file.getvalue().decode('cp874', errors='ignore')
    reader = csv.reader(io.StringIO(content))
    
    for row in reader:
        if not row: continue
        non_empty = [x.strip() for x in row if x.strip()]
        
        if non_empty and non_empty[0] == "รวมลูกค้า":
            try:
                student_name = " ".join(non_empty[1].split())
                student_code = non_empty[2]
                total_str = non_empty[-1].replace(',', '')
                outstanding_data.append({
                    'รหัสนักเรียน': student_code,
                    'ชื่อ-นามสกุล': student_name,
                    'ยอดคงเหลือล่าสุด (บาท)': float(total_str)
                })
            except Exception:
                pass
    return outstanding_data

if os.path.exists(DB_FILE):
    df_old = pd.read_csv(DB_FILE)
    st.info(f"📁 ระบบพร้อมใช้งาน: มีรายชื่อค้างชำระในฐานข้อมูล {len(df_old)} รายการ (คุณสามารถจัดการไฟล์นี้ได้ที่เมนูด้านซ้าย)")
else:
    df_old = pd.DataFrame()
    st.warning("⚠️ ยังไม่มีฐานข้อมูลในระบบ (การอัปโหลดไฟล์ด้านล่างนี้ครั้งแรก จะเป็นการสร้างฐานข้อมูลตั้งต้น)")

new_csvs = st.file_uploader("🆕 อัปโหลดไฟล์ CSV จากโปรแกรม Express เพื่อเช็คยอดล่าสุด", type=['csv'], accept_multiple_files=True)

if st.button("ประมวลผลและอัปเดตระบบ"):
    if new_csvs:
        all_data = []
        for file in new_csvs:
            all_data.extend(process_csv(file))
            
        if all_data:
            df_new = pd.DataFrame(all_data)
            
            if not df_old.empty:
                df_old.columns = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดค้างเดิม (บาท)']
                
                df_merge = pd.merge(df_old, df_new, on='รหัสนักเรียน', how='outer', suffixes=('_เก่า', '_ใหม่'))
                df_merge['ชื่อ-นามสกุล'] = df_merge['ชื่อ-นามสกุล_ใหม่'].fillna(df_merge['ชื่อ-นามสกุล_เก่า'])
                
                df_merge['ยอดค้างเดิม (บาท)'] = df_merge['ยอดค้างเดิม (บาท)'].fillna(0)
                df_merge['ยอดคงเหลือล่าสุด (บาท)'] = df_merge['ยอดคงเหลือล่าสุด (บาท)'].fillna(0)
                
                # เปลี่ยนชื่อจาก ยอดที่ชำระเข้ามา เป็น ยอดที่จ่าย
                df_merge['ยอดที่จ่าย (บาท)'] = (df_merge['ยอดค้างเดิม (บาท)'] - df_merge['ยอดคงเหลือล่าสุด (บาท)']).round(2)
                
                cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดค้างเดิม (บาท)', 'ยอดที่จ่าย (บาท)', 'ยอดคงเหลือล่าสุด (บาท)']
                df_merge = df_merge[cols]
                
                def highlight_changes(row):
                    colors = [''] * len(row)
                    paid = row['ยอดที่จ่าย (บาท)']
                    
                    if paid > 0:
                        idx_paid = df_merge.columns.get_loc('ยอดที่จ่าย (บาท)')
                        colors[idx_paid] = 'background-color: #d4edda; color: #155724;'
                    elif paid < 0:
                        idx_remain = df_merge.columns.get_loc('ยอดคงเหลือล่าสุด (บาท)')
                        idx_paid = df_merge.columns.get_loc('ยอดที่จ่าย (บาท)')
                        colors[idx_remain] = 'background-color: #f8d7da; color: #721c24;'
                        colors[idx_paid] = 'background-color: #f8d7da; color: #721c24;'
                    return colors

                st.write("**ผลการเปรียบเทียบความเคลื่อนไหว:**")
                styled_df = df_merge.style.apply(highlight_changes, axis=1).format({
                    'ยอดค้างเดิม (บาท)': '{:,.2f}',
                    'ยอดที่จ่าย (บาท)': '{:,.2f}',
                    'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'
                })
                st.dataframe(styled_df, use_container_width=True)
                
                df_new_to_save = df_merge[['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดคงเหลือล่าสุด (บาท)']]
                df_new_to_save = df_new_to_save[df_new_to_save['ยอดคงเหลือล่าสุด (บาท)'] != 0]
                df_new_to_save.to_csv(DB_FILE, index=False)
                st.success("✅ อัปเดตฐานข้อมูลเรียบร้อยแล้ว!")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_merge.to_excel(writer, index=False, sheet_name='รายงานสรุปยอด')
                
                st.download_button(
                    label="📥 ดาวน์โหลดตารางเปรียบเทียบ (Excel)",
                    data=output.getvalue(),
                    file_name=f"เปรียบเทียบยอด_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            else:
                st.write("**ข้อมูลเริ่มต้นในระบบ:**")
                st.dataframe(df_new.style.format({'ยอดคงเหลือล่าสุด (บาท)': '{:,.2f}'}), use_container_width=True)
                df_new.to_csv(DB_FILE, index=False)
                st.success("✅ สร้างฐานข้อมูลตั้งต้นเรียบร้อยแล้ว!")
