# PDF Scraping AI Agent

A Python-based AI agent that scrapes data from PDFs, stores it in a vector database, and provides intelligent responses using AWS Bedrock Claude LLM.

## Features

- Extract text and metadata from PDF files
- Store extracted data in ChromaDB vector database
- Process and analyze data using AWS Bedrock Claude LLM
- Query the database with natural language questions
- LangGraph-based agent workflow

## Project Structure

```
.
├── main.py              # Main entry point
├── pdf_scraper.py       # PDF extraction functionality
├── database_manager.py  # ChromaDB integration
├── ai_agent.py          # AWS Bedrock and LangGraph integration
└── requirements.txt     # Project dependencies
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:

```bash
aws configure
```

## Usage

### Process a PDF file

```bash
python main.py process path/to/your/file.pdf
```

### Query the database

```bash
python main.py query "Your question about the PDF content"
```

## Database

The project uses ChromaDB as the vector database. All data is stored in the `./chroma_db` directory by default. The system uses the **all-MiniLM-L6-v2** embedding model (384 dimensions) for generating document embeddings.

## AWS Bedrock Integration

The AI agent uses AWS Bedrock Claude for processing and analyzing the scraped data. Make sure you have the necessary AWS permissions to access Bedrock services.

## Extending the Project

To add support for other data sources:
1. Create a new scraper class similar to `PDFScraper`
2. Implement the extraction logic
3. Update the main module to use the new scraper

## Future Improvements

- Add support for more document types (web pages, Word documents, etc.)
- Implement more advanced chunking strategies
- Add a web interface for easier interaction
- Implement document summarization
- Add support for image extraction and analysis