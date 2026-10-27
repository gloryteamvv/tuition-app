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
        c.drawCentredString((col_x[3]+col_x
