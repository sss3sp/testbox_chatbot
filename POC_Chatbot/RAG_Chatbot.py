import pandas as pd
import os
import re
from typing import List, Dict
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA, LLMChain
from langchain.prompts import PromptTemplate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_excel_file(file_path: str) -> pd.DataFrame:
    print(f"Debug: Loading file from {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, sep='\t')
    else:
        raise ValueError("Unsupported file format. Please use .xlsx or .csv (tab-separated)")
    
    df = df.fillna('')
    print(f"Debug: Loaded dataframe with shape {df.shape}")
    return df


def preprocess_data(df: pd.DataFrame) -> List[Dict[str, str]]:
    print("Debug: Preprocessing data")
    parsed_data = []
    for _, row in df.iterrows():
        parsed_data.append({
            "title": row['title'],
            "text": row['text']
        })
    print(f"Debug: Preprocessed {len(parsed_data)} entries")
    return parsed_data


def create_documents(parsed_data: List[Dict[str, str]]) -> List[str]:
    print("Debug: Creating documents")
    documents = []
    for item in parsed_data:
        doc = f"Title: {item['title']}\nText: {item['text']}"
        documents.append(doc)
    print(f"Debug: Created {len(documents)} documents")
    return documents


def find_best_match(query: str, titles: List[str]) -> str:
    #print("Debug: Finding best match for query")
    vectorizer = TfidfVectorizer()
    title_vectors = vectorizer.fit_transform(titles)
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, title_vectors)
    best_match_index = similarities.argmax()
    #print(f"Debug: Best match index: {best_match_index}")
    return titles[best_match_index]





# Initialize language model and embeddings
content_llm = Ollama(model="mistral")
#embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings()

# Set the path to the Excel or CSV file directly (update the file path accordingly)
file_path = "testbox_faq_rag.xlsx"  # Replace this with the actual path to your file
df = load_excel_file(file_path)


# Load and preprocess the data
parsed_data = preprocess_data(df)
documents = create_documents(parsed_data)

# Split documents
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.create_documents(documents)

# Create vector store
print("Debug: Creating vector store")
# vectorstore = Chroma.from_documents(documents=texts, embedding=embeddings)
vectorstore = FAISS.from_documents(documents=texts, embedding=embeddings)

# Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

#retriever = vectorstore.as_retriever()


# Create prompt template
template = """Du bist ein Assistent für die Testbox-Hilfe. Beantworte die folgende Frage basierend auf dem gegebenen Kontext. Wenn die Frage nicht direkt mit dem Kontext zusammenhängt, entschuldige dich höflich und erkläre, dass du nur Fragen beantworten kannst, die sich auf den gegebenen Inhalt beziehen.

Kontext: {context}

Frage: {question}

Wichtige Anweisungen:
1. Gib die vollständige Antwort aus dem Text wieder, wenn sie verfügbar ist.
2. Wenn die Frage genau mit einem Titel im Datensatz übereinstimmt, gib den gesamten zugehörigen Text zurück.
3. Formuliere die Antwort so um, dass sie natürlich klingt und direkt auf die Frage antwortet.
4. Wenn mehrere relevante Informationen vorhanden sind, fasse sie zusammen und strukturiere die Antwort klar.
5. Füge keine Informationen hinzu, die nicht im Kontext enthalten sind.
6. Alaways Antwort auf Deutsch

Antwort:"""

PROMPT = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)


# Create QA chain
print("Debug: Creating QA chain")
qa_chain = RetrievalQA.from_chain_type(
    llm=content_llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)


# Function to handle user queries

def get_conversational_response(query: str) -> str:
    query_lower = query.lower()
    
    # Handle greetings and introductions
    if any(greeting in query_lower for greeting in ['hallo', 'hi', 'halo', 'hello', 'guten tag']):
        return "Hallo! Wie kann ich Ihnen heute helfen?"
    elif "ich bin" in query_lower or "mein name ist" in query_lower:
        name_match = re.search(r"ich bin ([\w\s]+)|mein name ist ([\w\s]+)", query_lower)
        if name_match:
            name = name_match.group(1) or name_match.group(2)
            name = name.strip().capitalize()
            return f"Hallo {name}! Ich bin Ihr Testbox Assistent. Wie kann ich Ihnen helfen?"
        else:
            return "Hallo! Ich bin Ihr Testbox Assistent. Wie kann ich Ihnen helfen?"
    
    # Handle other conversational queries
    elif any(thanks in query_lower for thanks in ['danke', 'vielen dank']):
        return "Gerne! Kann ich Ihnen noch bei etwas anderem behilflich sein?"
    elif any(farewell in query_lower for farewell in ['tschüss', 'auf wiedersehen', 'bye']):
        return "Auf Wiedersehen! Ich wünsche Ihnen einen schönen Tag!"
    elif "wer bist du" in query_lower:
        return "Ich bin Ihr Testbox Assistent. Wie kann ich Ihnen helfen?"
    elif "wie geht's" in query_lower:
        return "Mir geht's gut, danke! Wie kann ich Ihnen helfen?"
    elif "ich brauche hilfe" in query_lower or "ich habe eine frage" in query_lower:
        return "Ich helfe Ihnen gerne. Worum geht es in Ihrer Frage?"
    
    # Default response for unrecognized queries
    return None

def is_content_related_query(query: str, df: pd.DataFrame) -> bool:
    vectorizer = TfidfVectorizer()
    title_vectors = vectorizer.fit_transform(df['title'])
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, title_vectors)
    
    threshold = 0.1  # Adjust this value as needed
    return similarities.max() > threshold

def handle_query(query: str, df: pd.DataFrame, misunderstanding_count: dict) -> str:
    #print(f"Debug: Handling query: {query}")
    
    # First, check for conversational responses
    conversational_response = get_conversational_response(query)
    if conversational_response:
        misunderstanding_count['count'] = 0  # Reset the count on successful conversation
        return conversational_response
    
    # If not a conversational query, check if it's content-related
    if is_content_related_query(query, df):
        best_match = find_best_match(query, df['title'].tolist())
        #print(f"Debug: Best matching title: {best_match}")
        
        matched_text = df[df['title'] == best_match]['text'].iloc[0]
        
        result = qa_chain.invoke({"query": query, "context": matched_text})
        #print(f"Debug: QA chain result: {result['result']}")
        misunderstanding_count['count'] = 0  # Reset the count on successful query
        return result['result']
    else:
        # If we reach here, it means we didn't understand the query
        misunderstanding_count['count'] += 1
        if misunderstanding_count['count'] >= 2:
            return "Tut mir leid, ich konnte Ihnen nicht helfen. Sie können eine E-Mail an tests@testbox.de mit Ihren Fragen senden."
        else:
            return "Entschuldigung, ich habe Ihre Frage nicht ganz verstanden. Können Sie sie bitte umformulieren oder spezifizieren?"


# Main chat loop
print("Willkommen! Ich bin Ihr Assistent. Wie kann ich Ihnen helfen? (Zum Beenden 'quit' eingeben)")
misunderstanding_count = {'count': 0}
while True:
    user_input = input("Sie: ")
    if user_input.lower() == 'q':
        print("Assistent: Auf Wiedersehen! Ich wünsche Ihnen einen schönen Tag!")
        break
    response = handle_query(user_input, df, misunderstanding_count)
    print("Assistent:", response)
