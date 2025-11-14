# WhisperData

An AI-powered Excel data analysis application that lets you chat with your spreadsheets using natural language.

## What is WhisperData?

WhisperData is a Django web application that combines the power of Claude AI with Excel data analysis. Upload your Excel files and ask questions about your data in plain English - WhisperData will analyze your data and provide intelligent insights, summaries, and answers.

<img width="1650" height="1722" alt="image" src="https://github.com/user-attachments/assets/5bc0b345-a488-408f-9687-dd17302821f2" />


## Features

- **Upload Excel Files**: Support for .xlsx and .xls files
- **AI-Powered Chat**: Ask questions about your data in natural language
- **Smart Analysis**: Get insights, trends, and patterns from your data
- **Large File Support**: Intelligent summarization for large datasets
- **Chat History**: Access previous chat sessions
- **Data Viewer**: View your Excel data in a clean table format
- **Modern UI**: Claude-inspired clean and minimal design

## Prerequisites

- Python 3.12 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

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

4. **Set up your API key**
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
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

## Technology Stack

- **Backend**: Django 5.0
- **AI**: Anthropic Claude API (claude-sonnet-4-5)
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
