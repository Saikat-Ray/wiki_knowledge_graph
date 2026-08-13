import streamlit as st
from LLM import get_entities, generate_response
from Neo4j import Neo4jHandler
import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Streamlit app title
st.title("Knowledge Graph-Powered Chat: Query Your Dataset")

# Initialize session state to store chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""

# Function to handle input submission
def handle_submit():
    user_input = st.session_state["user_input"]
    if user_input:
        # Step 1: Extract entities from the user query
        extracted_entities = get_entities(user_input)
        print("Entities in the query: ", extracted_entities)

        # Step 2: Retrieve associated relationships from the Neo4j knowledge graph
        neo4j_handler = Neo4jHandler(os.getenv("NEO4J_CONNECTION_URI"), "neo4j", os.getenv("NEO4J_PASSWORD"))
        related_relationships_tuple_list = neo4j_handler.get_entities_and_relationships(extracted_entities)
        neo4j_handler.close()
        print("Extracted context from the Knowledge Graph: ", related_relationships_tuple_list)

        # Step 3: Augment the query with knowledge graph context
        messages = [
            {"role": "system", "content": f"Use the following knowledge graph context (provided as relationship tuple list: (Entity 1, Relation, Entity 2)) to answer the user queries.\n{related_relationships_tuple_list}"},
            {"role": "user", "content": user_input},
        ]

        # Step 4: Get GPT-4 response using the augmented query
        bot_response = generate_response(messages)

        # Step 5: Insert the latest user message and bot response at the top of the session history
        st.session_state["messages"].insert(0, {"role": "assistant", "content": bot_response})
        st.session_state["messages"].insert(0, {"role": "user", "content": user_input})

        # Clear the input field in session state
        st.session_state["user_input"] = ""

# User input section
st.text_input("Ask a question related to your dataset:", value=st.session_state["user_input"], key="user_input", on_change=handle_submit)

# Function to display messages in colored boxes
def display_message(message, is_user):
    if is_user:
        st.markdown(f"""
        <div style="background-color:#DCF8C6;padding:10px;border-radius:10px;margin-bottom:10px;">
        {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color:#E6E6FA;padding:10px;border-radius:10px;margin-bottom:10px;">
        {message}
        </div>
        """, unsafe_allow_html=True)

# Display the conversation history
if st.session_state["messages"]:
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            display_message(msg["content"], is_user=True)
        elif msg["role"] == "assistant":
            display_message(msg["content"], is_user=False)
