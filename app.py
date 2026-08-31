import streamlit as st
import pandas as pd
import csv
import io
import datetime

st.set_page_config(page_title="ระบบเปรียบเทียบยอดค่าเทอม", layout="wide")
st.title("📊 โปรแกรมเปรียบเทียบและสรุปยอดค่าเทอมค้างชำระ")

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
                    'ยอดใหม่ (บาท)': float(total_str),
                    'อ้างอิงจากไฟล์': file.name
                })
            except Exception:
                pass
    return outstanding_data

# สร้างกล่องอัปโหลด 2 ฝั่ง (ซ้าย: ข้อมูลเก่า / ขวา: ข้อมูลใหม่)
col1, col2 = st.columns(2)
with col1:
    st.info("📁 1. ฐานข้อมูลเดิม")
    old_excel = st.file_uploader("อัปโหลดไฟล์ Excel สรุปยอดของรอบที่แล้ว (ถ้ามี)", type=['xlsx'])

with col2:
    st.success("🆕 2. ข้อมูลอัปเดตล่าสุด")
    new_csvs = st.file_uploader("อัปโหลดไฟล์ CSV จากโปรแกรม Express", type=['csv'], accept_multiple_files=True)

if st.button("ประมวลผลและเปรียบเทียบยอด"):
    df_old = pd.DataFrame()
    df_new = pd.DataFrame()

    # ดึงข้อมูลเก่า (ถ้ามีการอัปโหลด)
    if old_excel:
        try:
            df_old = pd.read_excel(old_excel)
            if 'รหัสนักเรียน' in df_old.columns and 'ยอดค้างชำระ (บาท)' in df_old.columns:
                df_old = df_old[['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดค้างชำระ (บาท)']]
                df_old.rename(columns={'ยอดค้างชำระ (บาท)': 'ยอดเดิม (บาท)'}, inplace=True)
            elif 'ยอดเดิม (บาท)' in df_old.columns:
                 df_old = df_old[['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดเดิม (บาท)']]
        except Exception as e:
            st.error(f"อ่านไฟล์ Excel ผิดพลาด: {e}")

    # ดึงข้อมูลใหม่
    if new_csvs:
        all_data = []
        for file in new_csvs:
            all_data.extend(process_csv(file))
        if all_data:
            df_new = pd.DataFrame(all_data)
        else:
            st.warning("ไม่พบข้อมูลลูกหนี้ในไฟล์ CSV ใหม่")

    # นำมาเปรียบเทียบกัน
    if not df_new.empty:
        if not df_old.empty:
            # รวมตารางด้วยรหัสนักเรียน
            df_merge = pd.merge(df_old, df_new, on=['รหัสนักเรียน', 'ชื่อ-นามสกุล'], how='outer')
            df_merge['ยอดเดิม (บาท)'] = df_merge['ยอดเดิม (บาท)'].fillna(0)
            df_merge['ยอดใหม่ (บาท)'] = df_merge['ยอดใหม่ (บาท)'].fillna(0)
            df_merge['ส่วนต่าง (ชำระแล้ว)'] = df_merge['ยอดเดิม (บาท)'] - df_merge['ยอดใหม่ (บาท)']
            
            # จัดเรียงคอลัมน์
            cols = ['รหัสนักเรียน', 'ชื่อ-นามสกุล', 'ยอดเดิม (บาท)', 'ยอดใหม่ (บาท)', 'ส่วนต่าง (ชำระแล้ว)', 'อ้างอิงจากไฟล์']
            df_merge = df_merge[[c for c in cols if c in df_merge.columns]]
            
            st.write(f"**สรุปผลการเปรียบเทียบ:** พบรายชื่อทั้งหมด {len(df_merge)} รายการ")
            
            # ฟังก์ชันไฮไลต์สี
            def highlight_changes(row):
                colors = [''] * len(row)
                diff = row['ส่วนต่าง (ชำระแล้ว)']
                
                # ถ้าจ่ายเงินแล้ว (ยอดใหม่น้อยกว่ายอดเดิม) -> ไฮไลต์สีเขียว
                if diff > 0:
                    idx_new = df_merge.columns.get_loc('ยอดใหม่ (บาท)')
                    idx_diff = df_merge.columns.get_loc('ส่วนต่าง (ชำระแล้ว)')
                    colors[idx_new] = 'background-color: #d4edda; color: #155724;'
                    colors[idx_diff] = 'background-color: #d4edda; color: #155724;'
                
                # ถ้าหนี้เพิ่ม (ยอดใหม่มากกว่ายอดเดิม) -> ไฮไลต์สีแดงอ่อน
                elif diff < 0:
                    idx_new = df_merge.columns.get_loc('ยอดใหม่ (บาท)')
                    idx_diff = df_merge.columns.get_loc('ส่วนต่าง (ชำระแล้ว)')
                    colors[idx_new] = 'background-color: #f8d7da; color: #721c24;'
                    colors[idx_diff] = 'background-color: #f8d7da; color: #721c24;'
                    
                return colors

            styled_df = df_merge.style.apply(highlight_changes, axis=1).format({
                'ยอดเดิม (บาท)': '{:,.2f}',
                'ยอดใหม่ (บาท)': '{:,.2f}',
                'ส่วนต่าง (ชำระแล้ว)': '{:,.2f}'
            })
            
            st.dataframe(styled_df, use_container_width=True)
            df_export = df_merge.copy()
            
        else:
            # กรณีอัปโหลดแค่ CSV อย่างเดียว (ไม่มีข้อมูลเดิมมาเทียบ)
            df_new.rename(columns={'ยอดใหม่ (บาท)': 'ยอดค้างชำระ (บาท)'}, inplace=True)
            st.write(f"**ดึงข้อมูลล่าสุด:** พบรายชื่อทั้งหมด {len(df_new)} รายการ (ไม่ได้อัปโหลดไฟล์เปรียบเทียบ)")
            st.dataframe(df_new.style.format({'ยอดค้างชำระ (บาท)': '{:,.2f}'}), use_container_width=True)
            df_export = df_new.copy()

        # ปุ่มดาวน์โหลด
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='รายงานยอดค้างชำระ')
            
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ตารางเปรียบเทียบ (Excel)",
            data=output.getvalue(),
            file_name=f"เปรียบเทียบยอดค่าเทอม_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
