import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import date

st.set_page_config(page_title="Tutoring Income Tracker", layout="wide")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("Tutoring Income Tracker")

with st.form("add_lesson"):
    student = st.text_input("Student name")
    lesson_date = st.date_input("Lesson date", date.today())
    rate = st.number_input("Amount owed ($)", min_value=0.0, step=5.0)
    submitted = st.form_submit_button("Add lesson")

    if submitted and student and rate > 0:
        supabase.table("lessons").insert({
            "student": student,
            "lesson_date": str(lesson_date),
            "rate": rate,
            "paid": False
        }).execute()
        st.success("Lesson added!")

data = supabase.table("lessons").select("*").order("lesson_date", desc=True).execute().data
df = pd.DataFrame(data)

if df.empty:
    st.info("No lessons added yet.")
    st.stop()

df["lesson_date"] = pd.to_datetime(df["lesson_date"])
df["status"] = df["paid"].apply(lambda x: "Paid" if x else "Unpaid")

st.subheader("Lessons")
for _, row in df.iterrows():
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
    c1.write(row["student"])
    c2.write(row["lesson_date"].date())
    c3.write(f"${row['rate']:.2f}")
    c4.write(row["status"])

    if not row["paid"]:
        if c5.button("Mark paid", key=row["id"]):
            supabase.table("lessons").update({"paid": True}).eq("id", row["id"]).execute()
            st.rerun()

st.subheader("Summary")
total_owed = df["rate"].sum()
total_paid = df[df["paid"] == True]["rate"].sum()
total_unpaid = df[df["paid"] == False]["rate"].sum()

st.metric("Total earned", f"${total_owed:.2f}")
st.metric("Paid", f"${total_paid:.2f}")
st.metric("Still owed", f"${total_unpaid:.2f}")

chart_df = df.groupby(["lesson_date", "status"])["rate"].sum().reset_index()
fig = px.bar(chart_df, x="lesson_date", y="rate", color="status", title="Tutoring money by date")
st.plotly_chart(fig, use_container_width=True)
