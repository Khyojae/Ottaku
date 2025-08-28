import streamlit as st

page_main = st.Page("app.py", title="Main Page", icon="👉")
p1 = st.Page("p1.py",title="Main Page",icon="🔧")


page=st.navigation([p1])
page.run()
