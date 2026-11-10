@echo off
setlocal
cd /d D:\Projects\Project\finance_app
echo Running RAG Corpus Pipeline Ingestion...
python manage_rag.py ingest
echo.
echo Running Unit Tests...
python -m unittest tests/test_rag_ingestion.py
echo.
echo Generating Corpus Stats...
python manage_rag.py stats
echo.
pause

