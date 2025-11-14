import pandas as pd
import anthropic
from django.conf import settings
import json


class ExcelProcessor:
    """Utility class for processing Excel files"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.excel_file = pd.ExcelFile(file_path)

    def get_sheet_names(self):
        """Get all sheet names in the Excel file"""
        return self.excel_file.sheet_names

    def read_sheet(self, sheet_name=None, max_rows=None):
        """Read a specific sheet or the first sheet"""
        if sheet_name is None:
            sheet_name = self.excel_file.sheet_names[0]

        df = pd.read_excel(self.excel_file, sheet_name=sheet_name)

        if max_rows:
            df = df.head(max_rows)

        return df

    def get_sheet_summary(self, sheet_name=None):
        """Get a summary of the sheet data"""
        df = self.read_sheet(sheet_name)

        summary = {
            'sheet_name': sheet_name or self.excel_file.sheet_names[0],
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns),
            'data_types': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head(10).to_dict(orient='records')
        }

        return summary

    def get_data_summary_for_ai(self, sheet_name=None, max_sample_rows=50):
        """Get an intelligent summary of data optimized for AI token limits"""
        df = self.read_sheet(sheet_name)
        total_rows = len(df)

        summary_parts = []

        # Basic information
        summary_parts.append(f"Sheet: {sheet_name or self.excel_file.sheet_names[0]}")
        summary_parts.append(f"Total Rows: {total_rows:,}")
        summary_parts.append(f"Total Columns: {len(df.columns)}")
        summary_parts.append(f"\nColumns: {', '.join(df.columns)}")

        # Data types
        summary_parts.append(f"\nData Types:")
        for col, dtype in df.dtypes.items():
            summary_parts.append(f"  - {col}: {dtype}")

        # Statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"\nNumeric Column Statistics:")
            stats = df[numeric_cols].describe()
            summary_parts.append(stats.to_string())

        # Sample data (first and last rows)
        summary_parts.append(f"\nFirst {min(max_sample_rows // 2, total_rows)} rows:")
        summary_parts.append(df.head(max_sample_rows // 2).to_string(index=True))

        if total_rows > max_sample_rows:
            summary_parts.append(f"\nLast {min(max_sample_rows // 2, total_rows)} rows:")
            summary_parts.append(df.tail(max_sample_rows // 2).to_string(index=True))

        # Unique values for categorical columns (if not too many)
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            summary_parts.append(f"\nCategorical Columns Info:")
            for col in categorical_cols:
                unique_count = df[col].nunique()
                summary_parts.append(f"  - {col}: {unique_count} unique values")
                if unique_count <= 20:
                    summary_parts.append(f"    Values: {', '.join(map(str, df[col].unique()[:20]))}")

        # Missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            summary_parts.append(f"\nMissing Values:")
            for col, count in missing[missing > 0].items():
                summary_parts.append(f"  - {col}: {count} ({count/total_rows*100:.1f}%)")

        return "\n".join(summary_parts)

    def get_all_data_as_text(self, max_rows=1000):
        """Convert Excel data to text format for AI analysis"""
        text_parts = []

        for sheet_name in self.excel_file.sheet_names:
            df = self.read_sheet(sheet_name, max_rows=max_rows)
            total_rows_in_sheet = len(pd.read_excel(self.excel_file, sheet_name=sheet_name))

            # If file is large, use smart summary instead of full data
            if total_rows_in_sheet > 100:
                text_parts.append(f"\n=== Sheet: {sheet_name} ===")
                text_parts.append(self.get_data_summary_for_ai(sheet_name, max_sample_rows=50))
                text_parts.append(f"\n[Note: Showing summary and sample data. Full dataset has {total_rows_in_sheet:,} rows]")
            else:
                text_parts.append(f"\n=== Sheet: {sheet_name} ===")
                text_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
                text_parts.append(f"Column names: {', '.join(df.columns)}")
                text_parts.append("\nData:")
                text_parts.append(df.to_string(index=False))

        return "\n".join(text_parts)


class AIAgent:
    """Utility class for AI-powered chat using Claude API"""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment variables")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def create_system_prompt(self, excel_data):
        """Create a system prompt with Excel data context"""
        return f"""You are an AI assistant specialized in analyzing Excel data. The user has uploaded an Excel file, and you have access to its contents.

Here is the Excel data you're working with:

{excel_data}

Your role is to:
1. Answer questions about the data accurately
2. Provide summaries and insights when asked
3. Identify patterns, trends, and anomalies
4. Suggest improvements or highlight issues in the data
5. Perform calculations or analysis as requested

Important notes:
- For large files (>100 rows), you are provided with a statistical summary, sample data (first and last rows), and metadata instead of the complete dataset
- When answering questions about large files, base your insights on the summary statistics, patterns in sample data, and column information provided
- If a user asks for specific row data that isn't in the sample, explain that you have access to a summary and suggest what analysis you can perform with the available data
- Always base your responses on the actual data provided. If you're unsure about something, say so. Be concise but thorough in your explanations."""

    def chat(self, user_message, excel_data, conversation_history=None):
        """
        Send a message to Claude and get a response

        Args:
            user_message: The user's question/message
            excel_data: The Excel data as text
            conversation_history: List of previous messages [{'role': 'user', 'content': '...'}, ...]

        Returns:
            AI response text
        """
        system_prompt = self.create_system_prompt(excel_data)

        # Build messages list
        messages = []

        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    def analyze_excel(self, excel_processor):
        """Provide an initial analysis of the Excel file"""
        summary = excel_processor.get_sheet_summary()
        excel_data = excel_processor.get_all_data_as_text(max_rows=100)

        prompt = "Please provide a brief overview of this Excel file, including what type of data it contains, its structure, and any immediate observations or insights."

        return self.chat(prompt, excel_data)


def validate_excel_file(file):
    """
    Validate uploaded Excel file

    Returns:
        tuple: (is_valid, error_message)
    """
    # Check file size
    if file.size > settings.MAX_UPLOAD_SIZE:
        return False, f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / 1048576:.1f}MB"

    # Check file extension
    filename = file.name.lower()
    if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls']):
        return False, "Only .xlsx and .xls files are allowed"

    # Try to read the file
    try:
        pd.ExcelFile(file)
    except Exception as e:
        return False, f"Invalid Excel file: {str(e)}"

    return True, None
