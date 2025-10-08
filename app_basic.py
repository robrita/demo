import os
import json
import pathlib
import numpy as np
import chainlit as cl
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the current directory (using pathlib instead of __file__ which doesn't work in notebooks)
current_dir = str(pathlib.Path().absolute())
out_dir = os.path.join(current_dir, "notebooks/3-output")

gpt_model = "gpt-4.1-mini"
embedding_model = "text-embedding-3-small"

# Initialize Azure OpenAI Service client with key-based authentication    
client = AzureOpenAI(
    azure_endpoint=os.getenv("AOAI_ENDPOINT"),
    api_key=os.getenv("AOAI_API_KEY"),
    api_version="2025-01-01-preview",
)

# Get a list of all Markdown files in the md folder
vector_files = [f for f in os.listdir(out_dir) if f.lower().endswith('.json')]

#Prepare the chat prompt
system_retrieval = """
You are a helpful AI Assistant. Follow these rules exactly:

1. PURPOSE
   - Use the supplied DOCUMENT_CHUNK to answer user questions.
   - Allow simple greetings and light chitchat.
   - If the user's question is outside the scope of DOCUMENT_CHUNK, respond with a polite refusal.

2. INPUT FORMAT
   The model always receives two inputs in this order:
   a) DOCUMENT_CHUNK: A block of text containing the relevant information.
   b) USER_QUERY: The user's message or question.

3. BEHAVIOR
   a) Greetings & Chitchat
      - If USER_QUERY is a greeting (e.g. “hi”, “hello”, “good morning”) or simple chitchat (“how are you?”, “what's up?”), respond with a friendly greeting or brief chitchat. Do not reference DOCUMENT_CHUNK.
   b) On-Topic Questions
      - If USER_QUERY asks about a fact or detail that is directly supported by DOCUMENT_CHUNK, answer accurately using only information from DOCUMENT_CHUNK.
      - Cite the relevant passage or phrase when possible: “According to the document: ‹…›”.
   c) Off-Topic or Irrelevant Questions
      - If USER_QUERY cannot be answered from DOCUMENT_CHUNK, reply:
        “I'm sorry, but I don't have information on that. Please ask something related to the document.”
      - Do NOT attempt to hallucinate or introduce outside knowledge.

4. RESPONSE FORMAT
   - Keep answers concise (2-4 sentences).
   - Use neutral, professional tone.
   - If refusing, use exactly: “I'm sorry, but I don't have information on that. Please ask something related to the document.”

5. EXAMPLES

Example 1 - Greeting  
DOCUMENT_CHUNK: “...”  
USER_QUERY: “Hey there!”  
→ “Hello! How can I help you with the document today?”

Example 2 - On-Topic  
DOCUMENT_CHUNK: “The Eiffel Tower is 300 meters tall.”  
USER_QUERY: “How tall is the Eiffel Tower?”  
→ “According to the document, the Eiffel Tower is 300 meters tall.”

Example 3 - Off-Topic  
DOCUMENT_CHUNK: “...”  
USER_QUERY: “What's the weather today?”  
→ “I'm sorry, but I don't have information on that. Please ask something related to the document.”

<DOCUMENT_CHUNK>
{{DOCUMENT}}
</DOCUMENT_CHUNK>

# IMPORTANT: Use reason and think step-by-step before answering.
"""

user_retrieval = """
DOCUMENT_CHUNK: {{DOCUMENT}}

USER_QUERY: {{QUERY}}
"""

# - Return the last query and last intent with complete context in English language. without any additional information or context.
system_rewrite = """
You are an expert copywriter.
- Given the following chat history, precisely extract the last query made by the user.
- Return the last query in English language with full context from the chat history.
"""

user_rewrite = """
# Chat History:
{{user_input}}

# Last Query:
"""


# Function that rewrites the user input
def rewrite_query(user_input):
    # Create a new system prompt for each file by replacing the placeholder
    user_prompt = user_rewrite.replace("{{user_input}}", user_input)
    messages = [
        {"role": "system", "content": system_rewrite},
        {"role": "user", "content": user_prompt},
    ]

    # Generate the completion  
    completion = client.chat.completions.create(  
        model=gpt_model,
        messages=messages,
        temperature=1,
        top_p=1,
    )

    return completion.choices[0].message.content


def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity between two vectors.

    Args:
        vec1 (array-like): First vector.
        vec2 (array-like): Second vector.

    Returns:
        float: Cosine similarity score between -1 and 1.

    Raises:
        ValueError: If the vectors are not the same shape or if one vector is zero.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    if vec1.shape != vec2.shape:
        raise ValueError("Vectors must have the same dimensions.")
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        raise ValueError("One of the vectors is zero and cannot be normalized.")
    
    return np.dot(vec1, vec2) / (norm1 * norm2)


def vector_search(query):
    # Create the vector for the query
    query_vector = client.embeddings.create(
        input=query,
        model=embedding_model
    )
    results = {}

    # Search for the most relevant documents using the vector
    for vector_file in vector_files:
        # Create full path for input file
        vector_path = os.path.join(out_dir, vector_file)
        # print(f"Processing: {vector_path}")
        
        with open(vector_path, 'r', encoding='utf-8') as f:
            vectors = json.load(f)

        # Loop through the vectors and check for similarity
        for vector in vectors:
            # Check if the vector is similar to the query vector
            similarity = cosine_similarity(vector['vector'], query_vector.data[0].embedding)
            # print(f"Similarity: {similarity} / {vector['chunkId']}")
            
            # If the similarity is above a certain threshold, add it to the results
            if float(similarity) > 0.5:
                results[vector['contentId']] = f"{vector['topic']}\n{vector['content']}"

    return results


def chat_with_pdf(query, search):
    try:
        print(f"User Query: {query}")

        # Create a new system prompt for each file by replacing the placeholder
        # user_prompt = user_retrieval.replace("{{DOCUMENT}}", json.dumps(search)).replace("{{QUERY}}", query)
        system_prompt = system_retrieval.replace("{{DOCUMENT}}", json.dumps(search))

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        # Generate the completion  
        completion = client.chat.completions.create(  
            model=gpt_model,
            messages=messages,
            temperature=1,
            top_p=1,
            response_format={ "type": "text" },
        )

        response = completion.choices[0].message.content
        results = {
            "query": query,
            "response": response,
            "documents": search,
        }
        print(f"-----> Query: {query}")
        print(f"-----> Response: {response}")

        # Save the structured data to a JSON file
        output_path = os.path.join(current_dir, 'chat_response.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        print(f"Results saved to: {output_path}")

        return results

    except Exception as e:
        print(f"Error occurred: {e}")


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/bulb.webp",
            ),

        cl.Starter(
            label="Spot the errors",
            message="How can I avoid common mistakes when proofreading my work?",
            icon="/public/warning.webp",
            ),
        cl.Starter(
            label="Get more done",
            message="How can I improve my productivity during remote work?",
            icon="/public/rocket.png",
            ),
        cl.Starter(
            label="Boost your knowledge",
            message="Help me learn about [topic]",
            icon="/public/book.png",
            )
        ]


# Chainlit setup
@cl.on_chat_start
async def on_chat_start():
    """
    Initialize the chat session and send a welcome message.
    """
    try:
        cl.user_session.set("chat_history", [])

    except Exception as e:
        await cl.Message(content=f"An error occurred: {str(e)}", author="Error").send()


@cl.on_message
async def on_message(message: cl.Message):
    try:
        # Show thinking message to user
        msg = await cl.Message("thinking...", author="agent").send()

        # Get the user input and append it to the chat history
        cl.user_session.set("chat_history", cl.user_session.get("chat_history") + [message.content])
        chat_history = cl.user_session.get("chat_history")
        print(f"-----> Chat History: {chat_history}")

        # Rewrite the user query based on the chat history
        user_query = rewrite_query("\n\n".join(chat_history))
        print(f"-----> Rewrites: {user_query}")

        # Perform vector search to get relevant documents
        search = vector_search(user_query)

        # Pass the chat history to the chat_with_pdf function
        results = chat_with_pdf(user_query, search)
        response = results['response']
        
        msg.content = response
        await msg.update()
        # Limit the chat history to the last 10 messages
        cl.user_session.set("chat_history", chat_history[-10:])

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()

if __name__ == "__main__":
    # Chainlit will automatically run the application
    pass