import os
from dataclasses import dataclass
import datetime

import streamlit as st
import psycopg2
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Prompt:
    title: str
    prompt: str
    is_favorite: bool
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

def setup_database():
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur

def prompt_form(prompt=None):
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key="prompt_form", clear_on_submit=True):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt_content:
                st.error('Please fill in both the title and prompt fields.')
                return
            return Prompt(title, prompt_content, is_favorite)

def delete_prompt(cur, con, prompt_id):
    cur.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
    con.commit()
    st.rerun()

def toggle_favorite(cur, con, prompt_id, is_favorite):
    print(f"UPDATE prompts SET is_favorite = %s WHERE id = %s", (not is_favorite, prompt_id) )
    cur.execute(f"UPDATE prompts SET is_favorite = %s WHERE id = %s", (not is_favorite, prompt_id))
    con.commit()
    st.rerun()
     
def update_prompt(cur, con, prompt_id, new_title, new_prompt):
    cur.execute("UPDATE prompts SET title = %s, prompt = %s WHERE id = %s", (new_title, new_prompt, prompt_id))
    con.commit()
    st.success("Prompt updated successfully!")

def display_prompts(cur, con):
    search_query = st.sidebar.text_input("Search prompts")
    sort_order = st.sidebar.selectbox("Sort by", ["Most recent", "Oldest", "Favorites"])
    
    query = "SELECT * FROM prompts"
    if search_query:
        query += f" WHERE title LIKE '%{search_query}%' OR prompt LIKE '%{search_query}%'"
    if sort_order == "Most recent":
        query += " ORDER BY created_at DESC" 
    elif sort_order == "Oldest": 
        query += " ORDER BY created_at"
    if sort_order == "Favorites":
        query += " ORDER BY is_favorite DESC, created_at DESC"

    cur.execute(query)
    prompts = cur.fetchall()
    # cur.execute(f"UPDATE prompts SET is_favorite = true WHERE id = 4")


    for p in prompts:
        with st.expander(f"{'⭐' if p[3] else ''} {p[1]} ", expanded=True):
            st.code(p[2])
            new_title = st.text_input("Title", value=p[1], key=f"title-{p[0]}")
            new_prompt = st.text_area("Prompt", value=p[2], key=f"prompt-{p[0]}")

            # Create a row of buttons
            col1, col2, col3, col4 = st.columns([2, 2, 8, 2])
            with col1:
                if st.button(":rainbow[Favorite]", key=f"fav-{p[0]}"):
                    print("favorite")
                    toggle_favorite(cur, con, p[0], p[3])
            with col2:
                if st.button("Update", key=f"update-{p[0]}"):
                    update_prompt(cur, con, p[0], new_title, new_prompt)
                    st.experimental_rerun()
            with col4:
                if st.button(":red[Delete]", key=f"delete-{p[0]}"):
                    delete_prompt(cur, con, p[0])


if __name__ == "__main__":
    st.title("Promptbase")
    st.subheader("A simple app to store and retrieve prompts")

    con, cur = setup_database()

    new_prompt = prompt_form()
    if new_prompt:
        try:
            cur.execute(
                "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite)
            )
            con.commit()
            st.success("Prompt added successfully!")
        except psycopg2 as e:
            st.error(f"Database error: {e}")

    display_prompts(cur, con)
    con.close()
