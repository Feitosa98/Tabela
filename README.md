# Extrator de Tabela de Emolumentos

Este projeto tem como objetivo extrair dados das tabelas de emolumentos em formato PDF (utilizando PyMuPDF e OCR via Tesseract), estruturar essas informações em formato JSON e disponibilizá-las para que sistemas terceiros possam baixá-las.

## Visão Geral do Fluxo

1. **Entrada:** Um documento de tabela de emolumentos (PDF) é colocado na pasta `entrada/`.
2. **Processamento:** O script `app.py` é executado para ler as páginas, aplicar OCR usando o Tesseract e processar/estruturar os dados (identificando atos, valores, ISS e afins).
3. **Saída:** O resultado é gravado em um arquivo `.json` estruturado dentro da pasta `saida/`.
4. **Disponibilização (Git):** Os arquivos JSON gerados são "commitados" e enviados para um repositório Git.
5. **Consumo no Caixa-Pro:** Sempre que uma nova tabela for gerada e publicada, o sistema Caixa-Pro poderá realizar o download automático ou manual (*pull*) das novas informações.
6. **Notificações:** Dentro do Caixa-Pro haverá uma área de notificações para alertar sobre atualizações do sistema e da tabela, possibilitando aos clientes escolherem o momento de efetuar as devidas atualizações.

## Estrutura do Projeto

```text
extrator-emolumentos/
├─ entrada/
│  └─ tabela.pdf
├─ saida/
│  └─ (arquivos JSON extraídos)
├─ app.py
├─ requirements.txt
└─ README.md
```

## Dependências

O projeto utiliza as seguintes bibliotecas Python:
- `pymupdf`
- `pillow`
- `pytesseract`
- `pandas`
- `openpyxl`

Também é necessário ter o [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado em seu sistema operacional e devidamente configurado no `PATH`, ou especificar manualmente seu caminho (ver dentro do arquivo `app.py` se estiver usando Windows).

## Como Executar

1. **Instale os pacotes Python:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Insira o PDF:**
   Certifique-se de salvar a sua tabela de emolumentos como `entrada/tabela.pdf`.

3. **Execute o script:**
   ```bash
   python app.py
   ```

4. Verifique a pasta `saida/` para encontrar os dados JSON resultantes.
