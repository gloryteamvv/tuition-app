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
