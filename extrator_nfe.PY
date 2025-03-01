import pdfplumber
import re
import tkinter as tk
from tkinter import filedialog, messagebox, font
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# === CONFIGURAÇÃO DO WEBDRIVER ===
CHROME_DRIVER_PATH = r"C:\chromedriver\chromedriver.exe"  # Edite com o caminho correto
DOWNLOAD_PATH = os.path.join(os.getcwd(), "XMLs_Download")  # Pasta para salvar os XMLs

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# === FUNÇÃO PARA EXTRAIR CHAVES DO PDF ===
def extrair_chaves(pdfs, palavra_chave):
    chaves = set()
    for pdf_arquivo in pdfs:
        with pdfplumber.open(pdf_arquivo) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_limpo = re.sub(r'\s+', '', texto)
                    padrao = rf"({palavra_chave}.*?)(\d{{44}})"
                    matches = re.findall(padrao, texto_limpo, re.IGNORECASE)
                    for match in matches:
                        chaves.add(match[1])
    return chaves

# === FUNÇÃO PARA SELECIONAR MULTIPLOS PDFs ===
def selecionar_arquivos():
    arquivos = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
    entrada_arquivos.delete(0, tk.END)
    entrada_arquivos.insert(0, ";".join(arquivos))

# === FUNÇÃO PARA BAIXAR O XML NO SITE ===
def baixar_xml(chave):
    print(f"🔍 Buscando XML para a chave: {chave}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": DOWNLOAD_PATH,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://consultardanfe.com/")
        time.sleep(2)

        campo_chave = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "keyValue"))
        )
        campo_chave.send_keys(chave)

        botao_consulta = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Buscar DANFE/XML')]"))
        )
        botao_consulta.click()

        try:
            botao_baixar = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download XML')]"))
            )
            botao_baixar.click()
            print(f"✅ XML da chave {chave} baixado!")
            time.sleep(3)
            renomear_arquivo(chave)
        except Exception as e:
            print(f"❌ Erro ao tentar baixar XML: {e}")
    finally:
        driver.quit()

# === FUNÇÃO PARA RENOMEAR O ARQUIVO PARA A CHAVE ===
def renomear_arquivo(chave):
    arquivos = os.listdir(DOWNLOAD_PATH)
    for arquivo in arquivos:
        caminho_antigo = os.path.join(DOWNLOAD_PATH, arquivo)
        caminho_novo = os.path.join(DOWNLOAD_PATH, f"{chave}.xml")
        if not arquivo.endswith(".xml") and "download" in arquivo.lower():
            os.rename(caminho_antigo, caminho_novo)
            print(f"📄 Arquivo renomeado: {chave}.xml")
            break

# === FUNÇÃO PARA PROCESSAR OS PDFs ===
def processar_pdfs():
    pdf_arquivos = entrada_arquivos.get().split(";")
    palavra_chave = entrada_palavra.get().strip()

    if not pdf_arquivos or not palavra_chave:
        messagebox.showerror("Erro", "Selecione um ou mais arquivos PDF e insira uma palavra-chave.")
        return

    chaves_encontradas = extrair_chaves(pdf_arquivos, palavra_chave)

    if chaves_encontradas:
        with open("resultado.txt", "w") as arquivo_txt:
            for chave in chaves_encontradas:
                arquivo_txt.write(chave + "\n")

        messagebox.showinfo("Sucesso", f"As chaves foram extraídas e os XMLs estão sendo baixados.\nTotal encontradas: {len(chaves_encontradas)}")

        for chave in chaves_encontradas:
            baixar_xml(chave)

        messagebox.showinfo("Finalizado", "Todos os XMLs foram baixados e renomeados com sucesso!")
    else:
        messagebox.showwarning("Aviso", "Nenhuma chave encontrada. Verifique os PDFs ou tente outra palavra-chave.")

# === INTERFACE GRÁFICA (TKINTER) ===
janela = tk.Tk()
janela.title("🔍 Extrator de Chaves NF-e")
janela.geometry("500x250")
janela.resizable(False, False)

fonte_titulo = font.Font(family="Helvetica", size=14, weight="bold")

label_titulo = tk.Label(janela, text="EXTRATOR DE CHAVES NF-e", font=fonte_titulo, fg="blue")
label_titulo.grid(row=0, column=0, columnspan=3, pady=10)

# Seletor de arquivos
entrada_arquivos = tk.Entry(janela, width=40)
entrada_arquivos.grid(row=1, column=1, padx=10, pady=5)
tk.Button(janela, text="📂 Procurar", command=selecionar_arquivos).grid(row=1, column=2, padx=10, pady=5)

# Entrada da palavra-chave
tk.Label(janela, text="Digite a palavra-chave:").grid(row=2, column=0, padx=10, pady=5)
entrada_palavra = tk.Entry(janela, width=40)
entrada_palavra.grid(row=2, column=1, padx=10, pady=5)

# Botão para extrair e baixar XMLs
tk.Button(janela, text="🔍 Extrair e Baixar XMLs", command=processar_pdfs, bg="green", fg="white").grid(row=3, column=1, pady=15)

label_credito = tk.Label(janela, text="Desenvolvido por Gabriel Nascimento", font=("Arial", 9, "italic"), fg="gray")
label_credito.grid(row=4, column=0, columnspan=3, pady=5)

janela.mainloop()
