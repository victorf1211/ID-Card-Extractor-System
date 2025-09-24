import pandas as pd
import requests
import streamlit as st

st.title("ID Card Extractor")

front_image = st.file_uploader("上傳身分證正面", type=["jpg", "jpeg", "png"], key="front")
back_image = st.file_uploader("上傳身分證背面", type=["jpg", "jpeg", "png"], key="back")

front_fields = None
back_fields = None

if st.button("開始辨識"):
    if front_image is not None:
        files = {"file": front_image}
        data = {"side": "front"}
        response = requests.post(
            "http://localhost:8000/upload/", files=files, data=data, timeout=100
        )
        front_result = response.json()
        front_fields = front_result.get("fields", {})

    if back_image is not None:
        files = {"file": back_image}
        data = {"side": "back"}
        response = requests.post(
            "http://localhost:8000/upload/", files=files, data=data, timeout=100
        )
        back_result = response.json()
        back_fields = back_result.get("fields", {})

    if front_fields or back_fields:
        merged = {}
        if isinstance(front_fields, dict):
            merged.update(front_fields)
        if isinstance(back_fields, dict):
            merged.update(
                {k: v for k, v in back_fields.items() if v not in [None, "NULL", "null", ""]}
            )

        merged = {k: v for k, v in merged.items() if v not in [None, "NULL", "null", ""]}

        if merged:
            df = pd.DataFrame([merged])
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="下載CSV", data=csv_bytes, file_name="idcard.csv", mime="text/csv"
            )
        else:
            st.warning("沒有可合併的資料")
