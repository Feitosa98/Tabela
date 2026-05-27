import fitz
import pytesseract
from PIL import Image
import io
import json
import re
from pathlib import Path

# Windows:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR / "entrada" / "tabela.pdf"
SAIDA_DIR = BASE_DIR / "saida"
SAIDA_DIR.mkdir(exist_ok=True)

JSON_FINAL = SAIDA_DIR / "tabela_emolumentos_completa.json"


def valor_decimal(txt):
    if not txt:
        return None

    txt = txt.replace("R$", "").strip()
    txt = txt.replace(".", "").replace(",", ".")

    try:
        return float(txt)
    except:
        return None


def detectar_especialidade(texto):
    t = texto.upper()

    if "REGISTRO DE IMÓVEIS" in t:
        return "Registro de Imóveis"
    if "PROTESTO" in t:
        return "Protesto de Títulos"
    if "TÍTULOS E DOCUMENTOS" in t:
        return "Registro de Títulos e Documentos"
    if "PESSOAS JURÍDICAS" in t:
        return "Registro Civil das Pessoas Jurídicas"
    if "PESSOAS NATURAIS" in t:
        return "Registro Civil das Pessoas Naturais"
    if "CONTRATOS MARÍTIMOS" in t:
        return "Registro de Contratos Marítimos"
    if "NOTAS" in t or "TABELIONATO DE NOTAS" in t:
        return "Notas"

    return "Não identificado"


def detectar_iss(texto):
    t = texto.upper()

    if "SEM ISS" in t or "SEM COBRANÇA DE ISS" in t:
        return {
            "cobra_iss": False,
            "aliquota_percentual": None,
            "descricao": "Sem cobrança de ISS"
        }

    match = re.search(r"ISS\s*(\d+(?:,\d+)?)\s*%", t)

    if match:
        aliquota = float(match.group(1).replace(",", "."))
        return {
            "cobra_iss": True,
            "aliquota_percentual": aliquota,
            "descricao": f"Com cobrança de {aliquota}% de ISS"
        }

    return {
        "cobra_iss": None,
        "aliquota_percentual": None,
        "descricao": "ISS não identificado"
    }


def detectar_desconto(texto):
    t = texto.upper()

    if "MINHA CASA" in t and "50%" in t:
        return {
            "percentual": 50,
            "descricao": "Desconto de 50% - Programa Minha Casa Minha Vida"
        }

    if "MINHA CASA" in t and "75%" in t:
        return {
            "percentual": 75,
            "descricao": "Desconto de 75% - Programa Minha Casa Minha Vida"
        }

    return None


def extrair_linhas_tabela(texto):
    atos = []
    padrao_moeda = r"(?:R\$)?\s?\d+(?:\.\d{3})*,\d{2}"

    for linha in texto.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        matches = list(re.finditer(padrao_moeda, linha))
        if len(matches) < 2:
            continue
            
        valores = [valor_decimal(m.group()) for m in matches]
        total = valores[-1]
        
        melhor_i = -1
        menor_erro = float('inf')
        
        # Testa os últimos N itens como colunas
        max_colunas = min(len(valores) - 1, 8)
        
        for i in range(len(valores) - 1, len(valores) - max_colunas - 2, -1):
            if i < 0: break
            soma = sum(valores[i:-1])
            erro = abs(soma - total)
            if erro < menor_erro:
                menor_erro = erro
                melhor_i = i

        # Se o erro for muito alto (> 20% do total + 10 reais de gordura), fallback seguro
        if total > 0 and menor_erro > (total * 0.2) + 10:
            melhor_i = max(0, len(valores) - 7)
            
        colunas = matches[melhor_i:]
        ato = linha[:matches[melhor_i].start()].strip()
        
        # Limpar sujeira do nome do ato
        ato = ato.replace('|', '').replace('[', '').replace(']', '').strip()
        ato = re.sub(r'\s+', ' ', ato) # Remove múltiplos espaços
        
        if len(colunas) >= 2 and len(ato) >= 2:
            numeros = [valor_decimal(m.group()) for m in colunas]

            atos.append({
                "tipo_ato": ato,
                "valores": {
                    "emolumento": numeros[0] if len(numeros) > 0 else None,
                    "iss": numeros[1] if len(numeros) > 1 else None,
                    "fig_rcpn": numeros[2] if len(numeros) > 2 else None,
                    "funjeam_extrajudicial": numeros[3] if len(numeros) > 3 else None,
                    "selo_controle_fiscalizacao": numeros[4] if len(numeros) > 4 else None,
                    "computacao": numeros[5] if len(numeros) > 5 else None,
                    "total": numeros[-1] if len(numeros) > 0 else None
                }
            })

    return atos


def processar_pdf(pdf_path=PDF_PATH, json_out=JSON_FINAL):
    doc = fitz.open(pdf_path)

    resultado = {
        "fonte": "Tabela de Emolumentos 2025 - Lei 7.500/2025 - TJAM",
        "arquivo_origem": Path(pdf_path).name,
        "total_paginas": len(doc),
        "versao_estrutura": "1.0",
        "cobrancas": []
    }

    for i, page in enumerate(doc):
        print(f"Processando página {i + 1}/{len(doc)}...")

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        import os
        tessdata_dir = BASE_DIR / "tessdata"
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)
        texto = pytesseract.image_to_string(img, lang="por")

        especialidade = detectar_especialidade(texto)
        iss = detectar_iss(texto)
        desconto = detectar_desconto(texto)
        atos = extrair_linhas_tabela(texto)

        resultado["cobrancas"].append({
            "pagina": i + 1,
            "especialidade": especialidade,
            "iss": iss,
            "beneficio_desconto": desconto,
            "tabelas": [
                {
                    "grupo": "Extração OCR automática",
                    "atos": atos
                }
            ]
        })

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nJSON gerado em: {json_out}")
    return json_out


if __name__ == "__main__":
    processar_pdf()
