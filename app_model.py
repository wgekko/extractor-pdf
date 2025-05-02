import base64
import streamlit as st        
import os      
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import tempfile
import warnings
warnings.simplefilter("ignore", category=FutureWarning)



# --- CONFIG STREAMLIT ---
st.set_page_config(page_title="Asistente PDF con IA", page_icon=":material/file_open:", layout="wide")

# --- CSS PERSONALIZADO ---
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- FONDO LOCAL ---
def add_local_background_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_string}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_local_background_image("img/fondo.jpg")


# --- PARÁMETROS DE DIRECTORIOS ---
pdfs_directory = "pdfs/"
db_directory = 'vectordb'
os.makedirs(pdfs_directory, exist_ok=True)
os.makedirs(db_directory, exist_ok=True)

# --- MODELOS Y EMBEDDINGS ---
embeddings = OllamaEmbeddings(model="deepseek-r1:14b")
vector_store = Chroma(persist_directory=db_directory, embedding_function=embeddings)
model = OllamaLLM(model="deepseek-r1:14b")

# --- TEMPLATE DE PROMPT ---
template = """
Eres un asistente especializado en procesar y responder preguntas en español. Tu tarea: 
1 - Analizar el contexto proporcionado en español
2 - Entender la pregunta en español 
3 - Generar una respuesta clara y concisa en español

Si no encuentras la respuesta en el contexto, simplemente indica que no lo sabes.
Limita tu respuesta a tres oraciones máximo.

Pregunta : {question}
Contexto : {context}
Respuesta (en Español):
"""

# --- FUNCIONES CLAVE ---

def load_pdf(file_path):
    loader = PyMuPDFLoader(file_path)
    raw_documents = loader.load()
    return [Document(page_content=doc.page_content.strip()) for doc in raw_documents if doc.page_content.strip()]

def split_text(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunked_docs = []

    progress_bar = st.progress(0, text="Dividiendo documento... 0%")
    total = len(documents)
    for idx, doc in enumerate(documents):
        chunked = text_splitter.split_documents([doc])
        chunked_docs.extend(chunked)
        pct = int(((idx+1)/total)*100)
        progress_bar.progress((idx+1)/total, text=f"Dividiendo documento... {pct}%")
    progress_bar.empty()
    return chunked_docs

def index_docs(docs):
    if docs:
        vector_store.add_documents(docs)
        vector_store.persist()
    else:
        st.warning("No hay contenido válido para indexar.", icon="⚠️")

def retrieve_docs(query):
    return vector_store.similarity_search(query)

def answer_question(question, docs):
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return chain.invoke({"question": question, "context": context})

# --- INTERFAZ PRINCIPAL ---
with st.container(border=True):
    st.header("Asistente Inteligente de Documentos PDF")
    st.subheader("*Asistente analiza archivos PDF y responde preguntas específicas.*")

    uploaded_file = st.file_uploader(":orange[Sube un archivo PDF]", type="pdf")

    if uploaded_file:
        with st.spinner(":orange[Procesando archivo...]"):
            # Guardar archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=pdfs_directory) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name

            st.success(":orange[Archivo subido correctamente.]", icon=":material/check:")
            documents = load_pdf(temp_path)
            st.info(f":orange[Total de páginas cargadas: {len(documents)}]", icon=":material/description:")
            chunked_docs = split_text(documents)
            index_docs(chunked_docs)

        # Entrada de preguntas
        st.markdown("---")
        question = st.chat_input("Escribe tu pregunta sobre el documento")
        if question:
            st.chat_message("user").write(question)
            with st.spinner(":oarange[Buscando respuesta...]"):
                relevant_docs = retrieve_docs(question)
                response = answer_question(question, relevant_docs)
            st.chat_message("assistant").write(response)
