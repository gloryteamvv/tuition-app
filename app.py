import streamlit as st
import pandas as pd
import csv
import io
import datetime
import os
import re
import base64

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib import colors
from bahttext import bahttext

# =========================================================
# ตั้งค่าหน้าเพจ
# ต้องเรียก set_page_config ก่อนคำสั่ง Streamlit อื่นเสมอ
# =========================================================
st.set_page_config(
    page_title="Vieng Center - สรุปยอดค่าเทอม",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# Custom CSS
# หมายเหตุ: ไม่ซ่อน stToolbar และไม่ซ่อนไอคอน SVG ของ Streamlit
# เพื่อให้ปุ่มเปิด/ยุบ Sidebar ทำงานตามระบบเดิม
# =========================================================
st.markdown(
    """
    <style>
        h1 { font-size: 26px !important; margin-bottom: 10px !important; color: #009460 !important; }
        h2 { font-size: 22px !important; color: #ff6e8a !important; }
        h3 { font-size: 18px !important; color: #009460 !important; }
        h4 { font-size: 16px !important; color: #009460 !important; }
        h5 { font-size: 15px !important; color: #185f93 !important; }

        [data-testid="stSidebar"] {
            background-color: #B8e7ca;
        }
        [data-testid="stSidebar"] * {
            color: #185f93;
            font-size: 14px;
        }
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4 {
            color: #009460 !important;
        }
        [data-testid="stSidebar"] button * {
            font-size: 16px !important;
            font-weight: bold;
        }

        button[kind="primary"] {
            background-color: #ff6e8a !important;
            border-color: #ff6e8a !important;
            color: #185f93 !important;
        }
        button[kind="primary"]:hover {
            background-color: #ff8d6d !important;
            border-color: #ff8d6d !important;
            color: white !important;
        }

        div[data-baseweb="select"] span[data-baseweb="tag"] {
            background-color: #f5e0a4 !important;
            color: #185f93 !important;
            border: 1px solid #f5e0a4 !important;
        }
        div[data-baseweb="select"] span[data-baseweb="tag"] span,
        div[data-baseweb="select"] span[data-baseweb="tag"] svg {
            color: #185f93 !important;
            fill: #185f93 !important;
        }
        div[data-baseweb="select"] span[data-baseweb="tag"] div[role="button"]:hover {
            background-color: #e6c875 !important;
        }

        .stApp {
            background-color: #fafafa;
        }

        /* อย่าซ่อน Toolbar หรือ SVG ปุ่ม Sidebar
           บังคับให้ปุ่มเปิด Sidebar ที่ถูกยุบมองเห็นได้ */
        [data-testid="stSidebarCollapsedControl"] {
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 1000000 !important;
        }
        [data-testid="stSidebarCollapsedControl"] button {
            visibility: visible !important;
            opacity: 1 !important;
            background-color: white !important;
            border: 2px solid #ff6e8a !important;
            border-radius: 8px !important;
            min-width: 42px !important;
            min-height: 42px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.10) !important;
        }
        [data-testid="stSidebarCollapsedControl"] button:hover {
            background-color: #ff6e8a !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] button[kind="header"] {
            visibility: visible !important;
            opacity: 1 !important;
        }

        .kpi-card {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            border: 1px solid #f0f0f0;
            border-left: 5px solid #009460;
            margin-bottom: 15px;
        }
        .kpi-card.green { border-left-color: #009460; }
        .kpi-card.yellow { border-left-color: #f5e0a4; }
        .kpi-card.pink { border-left-color: #ff6e8a; }
        .kpi-card.orange { border-left-color: #ff8d6d; }

        .kpi-title {
            font-size: 13px;
            color: #185f93;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .kpi-value {
            font-size: 24px;
            font-weight: bold;
            color: #009460;
        }
        .kpi-unit {
            font-size: 13px;
            color: #ff6e8a;
            font-weight: normal;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 5px;
            background-color: white;
            padding: 5px 10px 0 10px;
            border-radius: 8px 8px 0 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            background-color: #fefefe;
            border-radius: 4px 4px 0 0;
            color: #185f93;
            font-weight: 600;
            font-size: 14px;
            padding: 0 15px;
            border: 1px solid #f1f5f9;
            border-bottom: none;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ff6e8a !important;
            color: #185f93 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# ลงทะเบียนฟอนต์ภาษาไทยสำหรับ PDF
# =========================================================
font_path = "THSarabunNew.ttf"
has_font = False

if os.path.exists(font_path):
    try:
        if "THSarabun" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("THSarabun", font_path))
        has_font = True
    except Exception as exc:
        st.sidebar.warning(f"โหลดฟอนต์ THSarabunNew.ttf ไม่สำเร็จ: {exc}")

# =========================================================
# ฟังก์ชันตัวช่วย
# =========================================================
def clean_name_th(name):
    """ลบคำนำหน้าและช่องว่างเพื่อช่วยจับคู่ชื่อ"""
    n = str(name).replace(" ", "").strip()
    prefixes = ["เด็กชาย", "เด็กหญิง", "ด.ช.", "ด.ญ.", "นางสาว", "นาย", "นาง"]
    for prefix in prefixes:
        if n.startswith(prefix):
            n = n[len(prefix):]
            break
    return n


def extract_gender(name, title_from_form=""):
    title = str(title_from_form).strip()
    if title:
        if "ด.ช." in title or "เด็กชาย" in title or title == "นาย":
            return "ชาย"
        if "ด.ญ." in title or "เด็กหญิง" in title or title in ("นาง", "นางสาว"):
            return "หญิง"

    n = str(name).replace(" ", "").strip()
    if n.startswith(("ด.ช.", "เด็กชาย", "นาย")):
        return "ชาย"
    if n.startswith(("ด.ญ.", "เด็กหญิง", "นาง", "นางสาว")):
        return "หญิง"
    return "ไม่ระบุ"


def get_grade_info(raw_grade):
    clean_raw = str(raw_grade).replace(" ", "").strip()

    if ("ป" in clean_raw or "ประถม" in clean_raw):
        for number in range(1, 7):
            if str(number) in clean_raw:
                group = "ประถมต้น" if number <= 3 else "ประถมปลาย"
                return group, f"ประถมศึกษาปีที่ {number}"

    if "อ" in clean_raw or "อนุบาล" in clean_raw:
        for number in range(1, 4):
            if str(number) in clean_raw:
                return "อนุบาล", f"อนุบาล {number}"

    return "ไม่ระบุ", str(raw_grade).strip()


def get_image_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def to_float(value, default=0.0):
    """แปลงตัวเลขที่มี comma หรือช่องว่างเป็น float อย่างปลอดภัย"""
    try:
        cleaned = str(value).replace(",", "").strip()
        if cleaned == "" or cleaned.lower() in ("nan", "none"):
            return default
        return float(cleaned)
    except (TypeError, ValueError):
        return default


# =========================================================
# ฟังก์ชันสร้าง PDF ใบเสร็จ
# =========================================================
def create_receipts_pdf(df_paid):
    packet = io.BytesIO()
    pdf_canvas = canvas.Canvas(packet, pagesize=landscape(A4))
    font_name = "THSarabun" if has_font else "Helvetica"

    for _, row in df_paid.iterrows():
        student_code = str(row.get("รหัสนักเรียน", "-"))
        student_name = str(row.get("ชื่อ-นามสกุล", ""))
        salesperson = str(row.get("พนักงานขาย (ระดับชั้นย่อย)", ""))
        receipt_no = str(row.get("เลขที่ใบเสร็จ", ""))
        pay_date = str(row.get("วันที่จ่ายเงิน", ""))
        total_amount = to_float(row.get("ยอดที่จ่าย (บาท)", 0))
        amount_text = bahttext(total_amount)

        invoices = row.get("รายการบิล", [])
        if not isinstance(invoices, list) or not invoices:
            invoices = [{
                "doc_no": row.get("เอกสารอ้างอิง", "-"),
                "bill": total_amount,
                "paid": total_amount,
                "remain": to_float(row.get("ยอดคงเหลือล่าสุด (บาท)", 0)),
            }]

        # ส่วนหัวเอกสาร
        pdf_canvas.setFont(font_name, 22)
        pdf_canvas.drawString(2 * cm, 18 * cm, "โรงเรียนศิริมงคลศึกษา บางบัวทอง")

        pdf_canvas.setFont(font_name, 14)
        pdf_canvas.drawString(
            2 * cm, 17.2 * cm,
            "เลขที่ 91/1 ซอยศิริมงคล ถนนบางกรวย-ไทรน้อย ต.บางรักพัฒนา อ.บางบัวทอง จังหวัดนนทบุรี"
        )
        pdf_canvas.drawString(2 * cm, 16.5 * cm, "FAX. 02-920-8133 TEL. 08")
        pdf_canvas.drawString(2 * cm, 15.8 * cm, "เลขประจำตัวผู้เสียภาษี 0994000242379")

        pdf_canvas.setFont(font_name, 24)
        pdf_canvas.drawRightString(27.5 * cm, 17 * cm, "ใบเสร็จรับเงิน / Receipt")
        pdf_canvas.setStrokeColor(colors.black)
        pdf_canvas.setLineWidth(0.5)
        pdf_canvas.line(2 * cm, 14.5 * cm, 27.5 * cm, 14.5 * cm)

        # ข้อมูลลูกค้า
        pdf_canvas.setFont(font_name, 16)
        left_label, left_colon, left_val = 2 * cm, 5 * cm, 5.3 * cm
        pdf_canvas.drawString(left_label, 13.5 * cm, "ลูกค้า (รหัสลูกค้า)")
        pdf_canvas.drawString(left_colon, 13.5 * cm, ":")
        pdf_canvas.drawString(left_val, 13.5 * cm, student_code)
        pdf_canvas.drawString(left_label, 12.8 * cm, "ชื่อ-สกุล")
        pdf_canvas.drawString(left_colon, 12.8 * cm, ":")
        pdf_canvas.drawString(left_val, 12.8 * cm, student_name)
        pdf_canvas.drawString(left_label, 12.1 * cm, "ที่อยู่")
        pdf_canvas.drawString(left_colon, 12.1 * cm, ":")
        pdf_canvas.drawString(left_val, 12.1 * cm, "........................................................................")

        right_label, right_colon, right_val = 16.5 * cm, 19 * cm, 19.3 * cm
        pdf_canvas.drawString(right_label, 13.5 * cm, "เลขที่ใบเสร็จ")
        pdf_canvas.drawString(right_colon, 13.5 * cm, ":")
        pdf_canvas.drawString(right_val, 13.5 * cm, receipt_no)
        pdf_canvas.drawString(right_label, 12.8 * cm, "วันที่")
        pdf_canvas.drawString(right_colon, 12.8 * cm, ":")
        pdf_canvas.drawString(right_val, 12.8 * cm, pay_date)
        pdf_canvas.drawString(right_label, 12.1 * cm, "พนักงานขาย")
        pdf_canvas.drawString(right_colon, 12.1 * cm, ":")
        pdf_canvas.drawString(right_val, 12.1 * cm, salesperson)

        # ตารางรายการบิล
        table_top = 11 * cm
        row_height = 0.8 * cm
        num_rows = len(invoices) + (1 if len(invoices) > 1 else 0)
        table_height = max((num_rows * row_height) + 0.5 * cm, 2 * cm)
        table_bottom = table_top - table_height

        # จำกัดจำนวนรายการต่อใบเสร็จเพื่อไม่ให้ตารางทับส่วนท้ายกระดาษ
        # หากมีรายการมาก จะยังสร้างรายการที่มีอยู่ แต่แจ้งเตือนในหน้าแอป
        pdf_canvas.setFillColor(colors.HexColor("#333333"))
        pdf_canvas.rect(2 * cm, table_top - 1 * cm, 25.5 * cm, 1 * cm, fill=1, stroke=1)
        pdf_canvas.setFillColor(colors.black)
        pdf_canvas.setLineWidth(1)
        pdf_canvas.rect(2 * cm, table_bottom, 25.5 * cm, table_height)

        col_x = [2 * cm, 3.5 * cm, 7.5 * cm, 11.5 * cm, 14.5 * cm,
                 17.5 * cm, 21.5 * cm, 24.5 * cm, 27.5 * cm]
        for x in col_x[1:-1]:
            pdf_canvas.line(x, table_top, x, table_bottom)

        pdf_canvas.setFillColor(colors.white)
        pdf_canvas.setFont(font_name, 14)
        headers = ["No.", "ใบวางบิล", "ใบกำกับ#", "วันที่", "ครบกำหนด",
                   "จำนวนเงิน", "ยอดคงค้าง", "ยอดชำระ"]
        for i, header in enumerate(headers):
            pdf_canvas.drawCentredString(
                (col_x[i] + col_x[i + 1]) / 2,
                table_top - 0.7 * cm,
                header
            )

        pdf_canvas.setFillColor(colors.black)
        data_y = table_top - 1.5 * cm
        for i, invoice in enumerate(invoices):
            paid = to_float(invoice.get("paid", 0))
            remain = to_float(invoice.get("remain", 0))
            pdf_canvas.setFont(font_name, 16)
            pdf_canvas.drawCentredString((col_x[0] + col_x[1]) / 2, data_y, str(i + 1))
            pdf_canvas.drawCentredString((col_x[1] + col_x[2]) / 2, data_y, "ค่าเทอม/ค่าเล่าเรียน")
            pdf_canvas.setFont(font_name, 14)
            pdf_canvas.drawCentredString((col_x[2] + col_x[3]) / 2, data_y, str(invoice.get("doc_no", "-")))
            pdf_canvas.drawCentredString((col_x[3] + col_x[4]) / 2, data_y, pay_date)
            pdf_canvas.setFont(font_name, 16)
            pdf_canvas.drawCentredString((col_x[5] + col_x[6]) / 2, data_y, f"{to_float(invoice.get('bill', paid)):,.2f}")
            pdf_canvas.drawCentredString((col_x[6] + col_x[7]) / 2, data_y, f"{remain:,.2f}")
            pdf_canvas.drawCentredString((col_x[7] + col_x[8]) / 2, data_y, f"{paid:,.2f}")
            data_y -= row_height

        if len(invoices) > 1:
            pdf_canvas.setFont(font_name, 16)
            pdf_canvas.drawCentredString((col_x[1] + col_x[2]) / 2, data_y, "รวมยอดชำระ")
            pdf_canvas.drawCentredString((col_x[7] + col_x[8]) / 2, data_y, f"{total_amount:,.2f}")

        summary_y = table_bottom - 1 * cm
        pdf_canvas.setFont(font_name, 16)
        pdf_canvas.drawString(2.5 * cm, summary_y, f"({amount_text})")
        pdf_canvas.drawString(22 * cm, summary_y, "รวมเป็นเงิน")

        box_y = table_bottom - 1.5 * cm
        pdf_canvas.rect(24.5 * cm, box_y, 3 * cm, 1 * cm)
        pdf_canvas.drawCentredString((col_x[7] + col_x[8]) / 2, box_y + 0.3 * cm, f"{total_amount:,.2f}")

        footer_y1 = table_bottom - 2.5 * cm
        footer_y2 = table_bottom - 3.5 * cm
        footer_y3 = table_bottom - 4.5 * cm
        footer_y4 = table_bottom - 5.3 * cm
        pdf_canvas.setFont(font_name, 16)
        pdf_canvas.drawString(2 * cm, footer_y1, "การชำระเงินด้วยเช็คจะเสร็จสมบูรณ์เมื่อบริษัทได้รับเงินตามเช็คเรียบร้อย")
        pdf_canvas.drawString(2 * cm, footer_y2, "เงินสด ....................... เช็คธนาคาร ....................... เช็คเลขที่ ....................... ลงวันที่ ......./......./....... จำนวนเงิน .......................")
        pdf_canvas.drawString(2 * cm, footer_y3, "ในนามโรงเรียนศิริมงคลศึกษา บางบัวทอง")
        pdf_canvas.drawString(2 * cm, footer_y4, "ผู้รับเงิน ........................................ วันที่ ......./......./.......      ผู้รับมอบอำนาจ ........................................")
        pdf_canvas.showPage()

    pdf_canvas.save()
    packet.seek(0)
    return packet


# =========================================================
# ดึงข้อมูลจาก Google Sheets
# =========================================================
@st.cache_data(ttl=60, show_spinner=False)
def pull_google_sheet_data(sheet_url):
    results = []
    try:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
        if not match:
            return []

        sheet_id = match.group(1)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_gs = pd.read_csv(csv_url)

        amount_cols = [column for column in df_gs.columns if "ยอดเงิน" in str(column)]
        if not amount_cols:
            return []

        for _, row in df_gs.iterrows():
            try:
                amount = to_float(row.get(amount_cols[-1], 0))
                if amount <= 0:
                    continue

                # ใช้ตำแหน่งคอลัมน์ตามแบบฟอร์มเดิม
                if len(row) < 8:
                    continue
                title_student = str(row.iloc[4]).strip()
                first_name = str(row.iloc[5]).strip()
                last_name = str(row.iloc[6]).strip()
                full_name = f"{first_name} {last_name}".strip()
                grade_raw = str(row.iloc[7]).strip()
                main_grade, sub_grade = get_grade_info(grade_raw)
                gender = extract_gender(full_name, title_student)

                raw_time = str(row.iloc[0]).split(" ")[0]
                try:
                    d, m, y = raw_time.split("/")
                    year = int(y)
                    if year < 2500:
                        year += 543
                    timestamp = f"{int(d):02d}/{int(m):02d}/{year}"
                except (ValueError, AttributeError):
                    timestamp = raw_time

                results.append({
                    "รหัสนักเรียน": "-",
                    "ชื่อ-นามสกุล": full_name,
                    "เพศ": gender,
                    "กลุ่มช่วงชั้น": main_grade,
                    "พนักงานขาย (ระดับชั้นย่อย)": sub_grade,
                    "เอกสารอ้างอิง": "-",
                    "วันที่จ่ายเงิน": timestamp,
                    "เลขที่ใบเสร็จ": "โอนผ่านฟอร์ม",
                    "ยอดค้างเดิม (บาท)": amount,
                    "ยอดที่จ่าย (บาท)": amount,
                    "ยอดคงเหลือล่าสุด (บาท)": 0.0,
                    "รายการบิล": [{
                        "doc_no": "-",
                        "bill": amount,
                        "paid": amount,
                        "remain": 0.0,
                    }],
                    "อ้างอิงไฟล์": "Google Sheet",
                    "source": "online",
                })
            except (ValueError, TypeError, IndexError):
                continue

    except Exception as exc:
        # แสดงสาเหตุเพื่อช่วยตรวจสอบการเชื่อมต่อ
        st.sidebar.error(f"ไม่สามารถเชื่อมต่อ Google Sheets ได้: {exc}")

    return results


# =========================================================
# อ่านไฟล์ CSV จาก Express
# =========================================================
def process_csv(file):
    results = []
    raw_bytes = file.getvalue()

    try:
        content = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw_bytes.decode("cp874", errors="replace")

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
        if not row:
            continue

        non_empty = [cell.strip() for cell in row if cell.strip()]
        if not non_empty:
            continue

        for cell in row:
            clean_cell = cell.strip()
            if clean_cell.startswith("RE") and clean_cell not in receipt_no_list:
                receipt_no_list.append(clean_cell)

        # จับชื่อผู้เรียนจากรูปแบบรายงานเดิม
        if len(row) >= 5:
            row_clean = [cell.strip() for cell in row]
            if row_clean[1] == "" and row_clean[2] == "" and row_clean[3] and row_clean[4]:
                candidate = row_clean[3]
                if "หน้า" not in candidate and "พนักงานขาย" not in candidate:
                    current_name = " ".join(candidate.split())

        # อ่านบรรทัดรายการเอกสาร
        if len(row) >= 5 and "/" in row[0].strip():
            try:
                row_clean = [cell.strip() for cell in row]
                if len(row_clean) > 1 and row_clean[1].startswith("IV"):
                    doc_date_list.append(row_clean[0])
                    doc_list.append(row_clean[1])

                if len(non_empty) < 3:
                    continue
                bill_str = non_empty[-3].replace(",", "")
                paid_str = non_empty[-2].replace(",", "")
                remain_str = non_empty[-1].replace(",", "")
                bill = to_float(bill_str, default=float("nan"))
                paid = to_float(paid_str, default=float("nan"))
                remain = to_float(remain_str, default=float("nan"))

                if pd.notna(bill) and pd.notna(paid) and pd.notna(remain):
                    sales_raw = row_clean[2] if len(row_clean) > 2 else ""
                    if sales_raw and not sales_raw.startswith("RE") and not sales_raw.replace(".", "").isdigit():
                        salesperson_list.append(sales_raw)

                    sum_bill += bill
                    sum_paid += paid
                    if paid > 0:
                        invoices_paid.append({
                            "doc_no": row_clean[1] if len(row_clean) > 1 else "-",
                            "bill": bill,
                            "paid": paid,
                            "remain": remain,
                        })
            except (ValueError, IndexError):
                pass

        # พยายามอ่านวันที่ชำระตามรูปแบบไฟล์เดิม
        if len(row) >= 10 and not row[1].strip().startswith("รวม"):
            if row[8].strip() and not row[7].strip():
                for cell in row[8:]:
                    cell_str = cell.strip()
                    if len(cell_str) >= 6 and "/" in cell_str:
                        if cell_str not in pay_date_list:
                            pay_date_list.append(cell_str)
                        break

        # สรุปข้อมูลเมื่อตรวจพบแถวรวมลูกค้า
        if non_empty[0] == "รวมลูกค้า":
            try:
                name = " ".join(non_empty[1].split()) if len(non_empty) > 1 else ""
                code = non_empty[2] if len(non_empty) > 2 else "-"
                total_remain = to_float(non_empty[-1], 0.0)

                if sum_bill == 0 and total_remain > 0:
                    sum_bill = total_remain

                docs_str = ", ".join(doc_list)
                receipts_str = receipt_no_list[0] if receipt_no_list else ""
                sales_raw = salesperson_list[0] if salesperson_list else ""
                main_grade, sub_grade = get_grade_info(sales_raw)
                gender = extract_gender(name)
                dates_str = pay_date_list[0] if pay_date_list else (doc_date_list[0] if doc_date_list else "")

                results.append({
                    "รหัสนักเรียน": code,
                    "ชื่อ-นามสกุล": name,
                    "เพศ": gender,
                    "กลุ่มช่วงชั้น": main_grade,
                    "พนักงานขาย (ระดับชั้นย่อย)": sub_grade,
                    "เอกสารอ้างอิง": docs_str,
                    "วันที่จ่ายเงิน": dates_str,
                    "เลขที่ใบเสร็จ": receipts_str,
                    "ยอดค้างเดิม (บาท)": round(sum_bill, 2),
                    "ยอดที่จ่าย (บาท)": round(sum_paid, 2),
                    "ยอดคงเหลือล่าสุด (บาท)": round(total_remain, 2),
                    "รายการบิล": invoices_paid.copy(),
                    "อ้างอิงไฟล์": file.name,
                    "source": "express",
                })

                sum_bill = 0.0
                sum_paid = 0.0
                doc_list = []
                doc_date_list = []
                pay_date_list = []
                salesperson_list = []
                receipt_no_list = []
                invoices_paid = []
            except (ValueError, IndexError, TypeError):
                continue

    return results


# =========================================================
# Sidebar
# =========================================================
if "processed_data" not in st.session_state:
    st.session_state["processed_data"] = []

logo_path = "logo.png"
gsheet_url = "https://docs.google.com/spreadsheets/d/153j9DQjxc4ucll6myNsQNMN-rQuK9DxChft0Vh69LFU/edit?usp=sharing"

with st.sidebar:
    if os.path.exists(logo_path):
        logo_b64 = get_image_base64(logo_path)
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/png;base64,{logo_b64}' width='130'></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='text-align:center;'><h3><span style='color:#009460;'>Vieng</span> "
            "<span style='color:#ff6e8a;'>Center</span></h3></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("#### นำเข้าข้อมูลรับชำระ")
    use_gsheet = st.checkbox("ดึงข้อมูลจาก Google Form (โอนเงิน)", value=True)
    uploaded_files = st.file_uploader(
        "อัปโหลดรายงาน CSV (เงินสด/เช็ค)",
        type=["csv"],
        accept_multiple_files=True,
    )

# =========================================================
# ประมวลผลข้อมูล
# =========================================================
csv_data = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        csv_data.extend(process_csv(uploaded_file))

# สร้าง dictionary สำหรับจับคู่ชื่อจาก CSV
# หมายเหตุ: หากมีชื่อซ้ำกัน ระบบเดิมจะเก็บรายการล่าสุดของชื่อนั้นไว้
csv_dict = {}
for record in csv_data:
    normalized_name = clean_name_th(record.get("ชื่อ-นามสกุล", ""))
    if normalized_name:
        csv_dict[normalized_name] = record

all_data = []
if use_gsheet:
    gsheet_data = pull_google_sheet_data(gsheet_url)

    for online_record in gsheet_data:
        normalized_name = clean_name_th(online_record.get("ชื่อ-นามสกุล", ""))

        if normalized_name in csv_dict:
            csv_record = csv_dict[normalized_name]
            online_record["รหัสนักเรียน"] = csv_record.get("รหัสนักเรียน", "-")
            online_record["ยอดค้างเดิม (บาท)"] = to_float(csv_record.get("ยอดค้างเดิม (บาท)", 0))

            if online_record["เพศ"] == "ไม่ระบุ":
                online_record["เพศ"] = csv_record.get("เพศ", "ไม่ระบุ")
            if online_record["กลุ่มช่วงชั้น"] == "ไม่ระบุ":
                online_record["กลุ่มช่วงชั้น"] = csv_record.get("กลุ่มช่วงชั้น", "ไม่ระบุ")
            if online_record["พนักงานขาย (ระดับชั้นย่อย)"] == "ไม่ระบุ":
                online_record["พนักงานขาย (ระดับชั้นย่อย)"] = csv_record.get("พนักงานขาย (ระดับชั้นย่อย)", "ไม่ระบุ")

            # คงสูตรคำนวณเดิมไว้: ยอดค้างเดิม - ยอดที่จ่ายออนไลน์
            online_record["ยอดคงเหลือล่าสุด (บาท)"] = (
                online_record["ยอดค้างเดิม (บาท)"] - to_float(online_record["ยอดที่จ่าย (บาท)"])
            )

            if online_record.get("รายการบิล"):
                if csv_record.get("รายการบิล"):
                    online_record["รายการบิล"][0]["doc_no"] = csv_record["รายการบิล"][0].get("doc_no", "-")
                else:
                    online_record["รายการบิล"][0]["doc_no"] = csv_record.get("เอกสารอ้างอิง", "-")
                online_record["รายการบิล"][0]["remain"] = online_record["ยอดคงเหลือล่าสุด (บาท)"]

            del csv_dict[normalized_name]

        all_data.append(online_record)

all_data.extend(csv_dict.values())
st.session_state["processed_data"] = all_data

if all_data:
    st.sidebar.success(f"เชื่อมต่อข้อมูลสำเร็จ {len(all_data)} รายการ")
else:
    st.sidebar.warning("ยังไม่มีข้อมูล หรือไม่พบข้อมูลลูกหนี้")

# =========================================================
# Main area
# =========================================================
if os.path.exists(logo_path):
    logo_b64 = get_image_base64(logo_path)
    st.markdown(
        f"##### <img src='data:image/png;base64,{logo_b64}' width='24' "
        "style='vertical-align:middle;margin-right:8px;'> "
        "<span style='vertical-align:middle;'>Vieng Center &gt; ทะเบียนรับเงิน</span>",
        unsafe_allow_html=True,
    )
else:
    st.markdown("##### Vieng Center > ทะเบียนรับเงิน")

st.markdown("<br>", unsafe_allow_html=True)

if not st.session_state["processed_data"]:
    st.info("ไม่พบข้อมูล กรุณาตรวจสอบการเชื่อมต่อ Google Sheets หรืออัปโหลดไฟล์ CSV ที่เมนูด้านซ้าย")
else:
    df = pd.DataFrame(st.session_state["processed_data"])

    # รับประกันว่าคอลัมน์สำคัญมีอยู่ก่อนนำไปใช้งาน
    required_defaults = {
        "รหัสนักเรียน": "-",
        "ชื่อ-นามสกุล": "",
        "เพศ": "ไม่ระบุ",
        "กลุ่มช่วงชั้น": "ไม่ระบุ",
        "พนักงานขาย (ระดับชั้นย่อย)": "ไม่ระบุ",
        "เอกสารอ้างอิง": "-",
        "วันที่จ่ายเงิน": "",
        "เลขที่ใบเสร็จ": "",
        "ยอดค้างเดิม (บาท)": 0.0,
        "ยอดที่จ่าย (บาท)": 0.0,
        "ยอดคงเหลือล่าสุด (บาท)": 0.0,
        "รายการบิล": None,
        "อ้างอิงไฟล์": "",
        "source": "unknown",
    }
    for column, default in required_defaults.items():
        if column not in df.columns:
            df[column] = default

    for column in ["ยอดค้างเดิม (บาท)", "ยอดที่จ่าย (บาท)", "ยอดคงเหลือล่าสุด (บาท)"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    df_paid = df[df["ยอดที่จ่าย (บาท)"] > 0].copy()
    total_revenue = df_paid["ยอดที่จ่าย (บาท)"].sum()
    total_students_paid = len(df_paid)
    online_count = len(df_paid[df_paid["source"] == "online"])
    express_count = len(df_paid[df_paid["source"] == "express"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="kpi-card green"><div class="kpi-title">ยอดรับชำระรวมทั้งหมด</div>
            <div class="kpi-value">{total_revenue:,.2f} <span class="kpi-unit">บาท</span></div></div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="kpi-card yellow"><div class="kpi-title">นักเรียนที่ชำระแล้ว</div>
            <div class="kpi-value">{total_students_paid} <span class="kpi-unit">คน</span></div></div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="kpi-card pink"><div class="kpi-title">โอนผ่านออนไลน์ (Form)</div>
            <div class="kpi-value">{online_count} <span class="kpi-unit">รายการ</span></div></div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="kpi-card orange"><div class="kpi-title">เงินสด/เช็ค (Express)</div>
            <div class="kpi-value">{express_count} <span class="kpi-unit">รายการ</span></div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    tab_dashboard, tab_table = st.tabs(["ภาพรวม (Dashboard)", "ทะเบียนรับเงิน (ออกใบเสร็จ)"])

    # -----------------------------------------------------
    # TAB Dashboard
    # -----------------------------------------------------
    with tab_dashboard:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### คัดกรองข้อมูล")
        filter_col1, filter_col2 = st.columns(2)

        gender_list = sorted(df_paid["เพศ"].dropna().astype(str).unique().tolist())
        grade_list = sorted(df_paid["พนักงานขาย (ระดับชั้นย่อย)"].dropna().astype(str).unique().tolist())

        selected_gender = filter_col1.multiselect(
            "คัดกรองเพศ (เลือกได้หลายตัวเลือก):",
            options=gender_list,
            default=gender_list,
        )
        selected_grade = filter_col2.multiselect(
            "คัดกรองระดับชั้น (เลือกได้หลายตัวเลือก):",
            options=grade_list,
            default=grade_list,
        )

        df_filtered = df_paid[
            df_paid["เพศ"].isin(selected_gender)
            & df_paid["พนักงานขาย (ระดับชั้นย่อย)"].isin(selected_grade)
        ]

        st.divider()
        chart_col, table_col = st.columns([1.2, 1])

        with chart_col:
            st.markdown("##### กราฟสรุปยอดชำระเงิน")
            if not df_filtered.empty:
                filtered_grade = 0 < len(selected_grade) < len(grade_list)
                filtered_gender = 0 < len(selected_gender) < len(gender_list)

                if filtered_grade or filtered_gender:
                    summary = df_filtered.groupby("พนักงานขาย (ระดับชั้นย่อย)", dropna=False)["ยอดที่จ่าย (บาท)"].sum().reset_index()
                    st.bar_chart(summary.set_index("พนักงานขาย (ระดับชั้นย่อย)"), color="#ff6e8a")
                else:
                    summary = df_filtered.groupby("กลุ่มช่วงชั้น", dropna=False)["ยอดที่จ่าย (บาท)"].sum().reset_index()
                    st.bar_chart(summary.set_index("กลุ่มช่วงชั้น"), color="#009460")
            else:
                st.warning("ไม่มีข้อมูลกราฟตรงกับเงื่อนไขที่เลือก")

        with table_col:
            st.markdown("##### รายชื่อนักเรียน (ตามการกรอง)")
            if not df_filtered.empty:
                cols_to_show = ["ชื่อ-นามสกุล", "พนักงานขาย (ระดับชั้นย่อย)", "ยอดที่จ่าย (บาท)"]
                st.dataframe(
                    df_filtered[cols_to_show].style.format({"ยอดที่จ่าย (บาท)": "{:,.2f}"}),
                    use_container_width=True,
                    height=350,
                )
            else:
                st.warning("ไม่มีข้อมูลนักเรียนตรงกับเงื่อนไข")

    # -----------------------------------------------------
    # TAB ทะเบียนรับเงินและออกใบเสร็จ
    # -----------------------------------------------------
    with tab_table:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### คัดกรองข้อมูลสำหรับออกใบเสร็จ")
        filter2_col1, filter2_col2, filter2_col3 = st.columns(3)

        gender_list2 = sorted(df["เพศ"].dropna().astype(str).unique().tolist())
        grade_list2 = sorted(df["พนักงานขาย (ระดับชั้นย่อย)"].dropna().astype(str).unique().tolist())
        date_list2 = sorted(df["วันที่จ่ายเงิน"].dropna().astype(str).unique().tolist())

        selected_gender2 = filter2_col1.multiselect(
            "คัดกรองเพศ:", options=gender_list2, default=gender_list2, key="g2"
        )
        selected_grade2 = filter2_col2.multiselect(
            "คัดกรองระดับชั้น:", options=grade_list2, default=grade_list2, key="gr2"
        )
        selected_date2 = filter2_col3.multiselect(
            "คัดกรองวันที่จ่ายเงิน:", options=date_list2, default=date_list2, key="dt2"
        )

        df_filtered_table = df[
            df["เพศ"].isin(selected_gender2)
            & df["พนักงานขาย (ระดับชั้นย่อย)"].isin(selected_grade2)
            & df["วันที่จ่ายเงิน"].astype(str).isin(selected_date2)
        ].copy()

        df_paid_filtered = df_filtered_table[df_filtered_table["ยอดที่จ่าย (บาท)"] > 0].copy()

        display_cols = [
            "รหัสนักเรียน", "ชื่อ-นามสกุล", "พนักงานขาย (ระดับชั้นย่อย)",
            "วันที่จ่ายเงิน", "เลขที่ใบเสร็จ", "ยอดที่จ่าย (บาท)",
            "ยอดคงเหลือล่าสุด (บาท)",
        ]
        df_display = df_filtered_table[display_cols].copy()

        st.divider()
        act_col1, act_col2 = st.columns(2)

        with act_col1:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                df_display.to_excel(writer, index=False, sheet_name="รายงานรับชำระ")

            st.download_button(
                label="ดาวน์โหลดตารางรวม (Excel)",
                data=output_excel.getvalue(),
                file_name=f"รายงานค่าเทอม_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with act_col2:
            if not df_paid_filtered.empty:
                if not has_font:
                    st.warning("ไม่พบฟอนต์ THSarabunNew.ttf จึงยังไม่สร้าง PDF เพื่อป้องกันข้อความภาษาไทยผิดเพี้ยน")
                else:
                    pdf_packet = create_receipts_pdf(df_paid_filtered)
                    st.download_button(
                        label=f"ดาวน์โหลดใบเสร็จทั้งหมด ({len(df_paid_filtered)} ใบ)",
                        data=pdf_packet,
                        file_name=f"ใบเสร็จรับเงิน_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                    )
            else:
                st.info("ไม่มีข้อมูลผู้ชำระเงินตามเงื่อนไขที่เลือก")

        st.markdown("<br>", unsafe_allow_html=True)

        def highlight_paid(row):
            row_colors = [""] * len(row)
            if to_float(row.get("ยอดที่จ่าย (บาท)", 0)) > 0:
                paid_idx = df_display.columns.get_loc("ยอดที่จ่าย (บาท)")
                row_colors[paid_idx] = "background-color: #B8e7ca; color: #185f93; font-weight: bold;"
            return row_colors

        styled_df = df_display.style.apply(highlight_paid, axis=1).format({
            "ยอดที่จ่าย (บาท)": "{:,.2f}",
            "ยอดคงเหลือล่าสุด (บาท)": "{:,.2f}",
        })
        st.dataframe(styled_df, use_container_width=True, height=500)
