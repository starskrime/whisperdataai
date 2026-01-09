# WhisperData

An AI-powered Excel data analysis application that lets you chat with your spreadsheets using natural language.

## What is WhisperData?

WhisperData is a Django web application that combines the power of Claude/OpenAI with Excel data analysis. Upload your Excel files and ask questions about your data in plain English - WhisperData will analyze your data and provide intelligent insights, summaries, and answers.

<img width="1650" height="1722" alt="image" src="https://github.com/user-attachments/assets/5bc0b345-a488-408f-9687-dd17302821f2" />


## Features

- **Upload Excel Files**: Support for .xlsx and .xls files
- **AI-Powered Chat**: Ask questions about your data in natural language
- **Smart Analysis**: Get insights, trends, and patterns from your data
- **Large File Support**: Intelligent summarization for large datasets
- **Chat History**: Access previous chat sessions
- **Data Viewer**: View your Excel data in a clean table format
- **Modern UI**: Clean and minimal design

## Prerequisites

- Python 3.12 or higher
- API key for your chosen AI provider:
  - **Anthropic** (Claude): [Get one here](https://console.anthropic.com/)
  - **OpenAI** (GPT-4): [Get one here](https://platform.openai.com/api-keys)

## Quick Start

### Option 1: Automated Setup (Recommended)

1. **Clone or download this project**

2. **Run the start script**
   ```bash
   ./start.sh
   ```

   The script will:
   - Create a virtual environment (if not exists)
   - Install all dependencies
   - Set up the database
   - Prompt for your API key
   - Start the development server

3. **Open your browser**

   Navigate to `http://127.0.0.1:8000`

### Option 2: Manual Setup

1. **Clone or download this project**

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure your AI provider and API key:
   ```bash
   # Choose your provider (anthropic or openai)
   AI_PROVIDER=anthropic

   # Add your API key
   ANTHROPIC_API_KEY=your-anthropic-key-here
   # OR
   OPENAI_API_KEY=your-openai-key-here
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Open your browser**

   Navigate to `http://127.0.0.1:8000`

## Usage

1. Upload an Excel file on the home page
2. Wait for the file to be processed
3. Start asking questions about your data
4. View your data in table format using the "View Data" button
5. Access previous chats from the "Recent Chats" section

## AI Provider Configuration

WhisperData supports two AI providers. You can switch between them anytime by editing your `.env` file:

### Anthropic (Claude Sonnet 4.5)
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### OpenAI (GPT-4)
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

After changing the provider, restart the server for changes to take effect.

## Technology Stack

- **Backend**: Django 5.0
- **AI**: Anthropic Claude API (claude-sonnet-4-5) or OpenAI GPT-4
- **Data Processing**: Pandas
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (default)

## Notes

- Maximum file size: 50MB
- For files with more than 100 rows, WhisperData uses intelligent summarization to stay within AI token limits
- All uploaded files are stored in the `media/excel_files/` directory
- Chat sessions are persistent and can be accessed anytime

## License

This project is for educational and personal use.

---

**WhisperData** - Making data analysis conversational
