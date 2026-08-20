@echo off
title Inicializador do Dashboard de NFs
echo ===================================================
echo   Iniciando o Dashboard de Documentos Fiscais...
echo ===================================================
echo.

:: Navega ate a pasta do projeto
cd /d "C:\Users\Alza\Desktop\dashboard_nfs"

:: Verifica/Instala as dependencias
echo [1/3] Verificando e instalando dependencias necessarias...
python -m pip install pandas openpyxl streamlit plotly pyarrow openai --quiet

:: Executa o gerador de planilha (caso ela ainda nao exista)
echo.
echo [2/3] Gerando/Atualizando a planilha de dados...
python gerar_planilha.py

:: Inicia a aplicacao no Streamlit
echo.
echo [3/3] Iniciando o Streamlit e abrindo no navegador...
echo.
python -m streamlit run app.py

pause