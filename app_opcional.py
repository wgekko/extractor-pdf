import base64
import streamlit as st
import pdfplumber
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO
import pandas as pd
import warnings
warnings.simplefilter("ignore", category=FutureWarning)

# Estilo de página
st.set_page_config(page_title="Extractor PDF", page_icon=":material/picture_as_pdf:", layout="wide")

# Cargar estilos personalizados
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("assets/style.css")

# Imagen de fondo local
def add_local_background_image(image):
    with open(image, "rb") as image:
        encoded_string = base64.b64encode(image.read())
        st.markdown(
            f"""
            <style>
            .stApp{{
                background-image: url(data:files/{"jpg"};base64,{encoded_string.decode()});
            }}    
            </style>
            """,
            unsafe_allow_html=True
        )

add_local_background_image("img/fondo.jpg")

# Extraer texto con barra de progreso
def extract_text_from_pdf(pdf_file, progress_callback=None):
    text_data = []
    reader = PdfReader(pdf_file)
    total_pages = len(reader.pages)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            for line in text.split('\n'):
                cleaned = ' '.join(line.replace('\t', ' ').replace('\u200b', ' ').split())
                if cleaned:
                    text_data.append({'Texto': cleaned})
        if progress_callback:
            progress_callback((i + 1) / total_pages)
    return text_data

# Extraer tablas si existen
def extract_tables_from_pdf(pdf_file):
    tables = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables

# Generar archivo Word
def generate_word_with_tables(text_data, tables):
    doc = Document()
    
    # Configurar márgenes
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Fuente y estilo
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Georgia'
    font.size = Pt(12)

    # Agregar contenido
    doc.add_heading('Texto Extraído del PDF', level=1)
    for item in text_data:
        doc.add_paragraph(item['Texto'])

    if tables:
        doc.add_page_break()
        doc.add_heading('Tablas Extraídas', level=1)
        for table in tables:
            if not table: continue
            table_doc = doc.add_table(rows=1, cols=len(table[0]))
            hdr_cells = table_doc.rows[0].cells
            for i, header in enumerate(table[0]):
                hdr_cells[i].text = str(header)
            for row in table[1:]:
                row_cells = table_doc.add_row().cells
                for i, cell in enumerate(row):
                    row_cells[i].text = str(cell)

    word_file = BytesIO()
    doc.save(word_file)
    word_file.seek(0)
    return word_file

# Generar archivo Excel
def generate_excel(text_data):
    df = pd.DataFrame(text_data)
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)
    return excel_file

# Interfaz
st.write("---")
with st.container(border=True):    
    file_ = open("img/adobe-acrobat.gif", "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()

    st.markdown(
        f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">',
        unsafe_allow_html=True,
    )
    st.header("Convertir PDF a Word y Excel")

with st.container(border=True):
    st.image("img/archivo-pdf.png", width=50, output_format="auto")
    pdf_file = st.file_uploader(":orange[*Sube tu archivo PDF*]", type=["pdf"])

# Procesamiento del PDF
if pdf_file:
    st.subheader("Procesando archivo PDF...")
    progress_bar = st.progress(0)

    # Extraer texto con barra de progreso
    text_data = extract_text_from_pdf(pdf_file, progress_callback=progress_bar.progress)

    # Simular avance al 90% al terminar texto
    progress_bar.progress(0.9)

    # Extraer tablas (sin progreso por página, asumimos 10%)
    tables = extract_tables_from_pdf(pdf_file)

    # Finalizar barra
    progress_bar.progress(1.0)
    st.success("¡Archivo procesado exitosamente!", icon=":material/task:")

    st.subheader("Texto y Tablas Extraídas")    
    if text_data:
        st.subheader("*Vista previa del texto*")  
        st.text_area("", '\n'.join([item['Texto'] for item in text_data[:10]]), height=250, label_visibility="visible")

    # Botones de descarga
    col1, col2 = st.columns(2, vertical_alignment="center")
    with col1:
        st.image("img/doc.png", width=50, output_format="auto")
        if st.button("Generar y Descargar Word"):
            word_file = generate_word_with_tables(text_data, tables)
            
            st.download_button(
                label="Descargar Word",
                data=word_file,
                file_name="texto_extraido.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                icon=":material/download:"
            )
    
    with col2:
        st.image("img/sobresalir.png", width=50, output_format="auto")
        if st.button("Generar y Descargar Excel"):
            excel_file = generate_excel(text_data)
            
            st.download_button(
                label="Descargar Excel",
                data=excel_file,
                file_name="texto_extraido.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                icon=":material/download:"
            )

    
# --------------- footer -----------------------------
st.write("---")
with st.container():
  #st.write("---")
  st.write(":orange[&copy; - derechos reservados -  2025 -  Walter Gómez - FullStack Developer - Data Science - Business Intelligence]")
  #st.write("##")
  left, right = st.columns(2, gap='small', vertical_alignment="bottom")
  with left:
    #st.write('##')
    st.link_button("Mi LinkedIn", "https://www.linkedin.com/in/walter-gomez-fullstack-developer-datascience-businessintelligence-finanzas-python/")
  with right: 
     #st.write('##') 
    st.link_button("Mi Porfolio", "https://walter-portfolio-animado.netlify.app/")
    
