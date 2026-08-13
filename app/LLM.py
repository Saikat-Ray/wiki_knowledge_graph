from openai import OpenAI
import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_entities(query):
  messages = [
  {"role": "system", "content": """"
  You are an advanced language model skilled at extracting entities from text. I need you to identify and list all entities in the provided text.
  Format the output in such a way that it can be directly parsed into Python lists. 
  The format should include:
  
  1. A list of **Entities** in Python list format.
  2. All entities should be in lowercase and stripped of any leading or trailing whitespace.
  
  Here is the format to follow:
  
  Entities: ["entity 1", "entity 2", ..., "entity n"]
  
  Example Input:
  Extract entities from the following text:
  "Michael Jackson, born in Gary, Indiana, was a famous singer known as the King of Pop. He passed away in Los Angeles in 2009."
  
  Expected Output:
  
  Entities: ["michael jackson", "gary, indiana", "los angeles", "singer", "king of pop", "2009"]

  """},
    {"role": "user", "content": f"Extract entities and relationship tuples from the following text:\n\n{query}\n\n"}
  ]
  
  response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
  )
  response_content = response.choices[0].message.content
  return response_content

import ast

def parse_llm_response_content(content):
    # Split the output into entities and relationships sections
    entity_section = content.split("Entities:")[1].strip()

    # Use ast.literal_eval to safely evaluate the string into Python lists
    entities = ast.literal_eval(entity_section)
  
    return entities

def get_entities(query):
  content = extract_entities(query)
  entities = parse_llm_response_content(content)
  return entities

# Function to generate a response from GPT-4, incorporating the KG-augmented query
def generate_response(messages):
    try:
      response = client.chat.completions.create(
      model="gpt-4",
      messages=messages,
      )
      response_content = response.choices[0].message.content
      return response_content
    except Exception as e:
      return f"Error: {str(e)}"
