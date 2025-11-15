import pandas as pd
import anthropic
import openai
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

    # Tool execution methods for AI to call
    def get_rows(self, start_row, end_row, sheet_name=None):
        """Get specific rows from the Excel file"""
        df = self.read_sheet(sheet_name)

        # Validate row range
        if start_row < 0 or end_row > len(df):
            return f"Error: Invalid row range. File has {len(df)} rows (0-indexed)."

        result = df.iloc[start_row:end_row].to_string(index=True)
        return f"Rows {start_row} to {end_row}:\n{result}"

    def filter_data(self, column, operator, value, sheet_name=None):
        """Filter rows by condition"""
        df = self.read_sheet(sheet_name)

        # Validate column exists
        if column not in df.columns:
            return f"Error: Column '{column}' not found. Available columns: {', '.join(df.columns)}"

        try:
            # Convert value to appropriate type
            if df[column].dtype in ['int64', 'float64']:
                value = float(value)

            # Apply filter
            if operator == '>':
                filtered = df[df[column] > value]
            elif operator == '<':
                filtered = df[df[column] < value]
            elif operator == '==':
                filtered = df[df[column] == value]
            elif operator == '!=':
                filtered = df[df[column] != value]
            elif operator == '>=':
                filtered = df[df[column] >= value]
            elif operator == '<=':
                filtered = df[df[column] <= value]
            elif operator == 'contains':
                filtered = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
            else:
                return f"Error: Unsupported operator '{operator}'. Use: >, <, ==, !=, >=, <=, contains"

            if len(filtered) == 0:
                return f"No rows match the condition: {column} {operator} {value}"

            # Limit results to prevent overwhelming the AI
            if len(filtered) > 100:
                result = filtered.head(100).to_string(index=True)
                return f"Found {len(filtered)} matching rows. Showing first 100:\n{result}"
            else:
                result = filtered.to_string(index=True)
                return f"Found {len(filtered)} matching rows:\n{result}"

        except Exception as e:
            return f"Error applying filter: {str(e)}"

    def calculate(self, operation, column, sheet_name=None):
        """Calculate sum, mean, median, count, min, max on a column"""
        df = self.read_sheet(sheet_name)

        # Validate column exists
        if column not in df.columns:
            return f"Error: Column '{column}' not found. Available columns: {', '.join(df.columns)}"

        try:
            col_data = df[column]

            # Remove NaN values for calculations
            col_data_clean = col_data.dropna()

            if operation == 'sum':
                result = col_data_clean.sum()
                return f"Sum of '{column}': {result:,.2f}"
            elif operation == 'mean' or operation == 'average':
                result = col_data_clean.mean()
                return f"Mean of '{column}': {result:,.2f}"
            elif operation == 'median':
                result = col_data_clean.median()
                return f"Median of '{column}': {result:,.2f}"
            elif operation == 'count':
                result = len(col_data_clean)
                return f"Count of '{column}' (non-null): {result:,}"
            elif operation == 'min':
                result = col_data_clean.min()
                return f"Minimum of '{column}': {result}"
            elif operation == 'max':
                result = col_data_clean.max()
                return f"Maximum of '{column}': {result}"
            elif operation == 'std':
                result = col_data_clean.std()
                return f"Standard deviation of '{column}': {result:,.2f}"
            else:
                return f"Error: Unsupported operation '{operation}'. Use: sum, mean, median, count, min, max, std"

        except Exception as e:
            return f"Error calculating {operation}: {str(e)}"

    def get_unique_values(self, column, sheet_name=None):
        """Get unique values in a column"""
        df = self.read_sheet(sheet_name)

        # Validate column exists
        if column not in df.columns:
            return f"Error: Column '{column}' not found. Available columns: {', '.join(df.columns)}"

        try:
            unique_vals = df[column].unique()
            unique_count = len(unique_vals)

            if unique_count > 50:
                sample = unique_vals[:50]
                return f"Column '{column}' has {unique_count} unique values. First 50: {', '.join(map(str, sample))}"
            else:
                return f"Column '{column}' has {unique_count} unique values: {', '.join(map(str, unique_vals))}"

        except Exception as e:
            return f"Error getting unique values: {str(e)}"


class AIAgent:
    """Utility class for AI-powered chat using Anthropic or OpenAI"""

    def __init__(self, provider=None, excel_processor=None):
        # Use provider from parameter or settings
        self.provider = (provider or settings.AI_PROVIDER).lower()
        self.excel_processor = excel_processor

        if self.provider == 'anthropic':
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not set in environment variables")
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = "claude-sonnet-4-5-20250929"
        elif self.provider == 'openai':
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in environment variables")
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4o"
        else:
            raise ValueError(f"Invalid AI provider: {self.provider}. Must be 'anthropic' or 'openai'")

    def get_tools(self):
        """Define tools available to the AI"""
        return [
            {
                "name": "get_rows",
                "description": "Get specific rows from the Excel file by row number range. Use this when you need to see exact data for specific rows.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_row": {
                            "type": "integer",
                            "description": "Starting row number (0-indexed)"
                        },
                        "end_row": {
                            "type": "integer",
                            "description": "Ending row number (0-indexed, exclusive)"
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "Sheet name (optional, uses first sheet if not specified)"
                        }
                    },
                    "required": ["start_row", "end_row"]
                }
            },
            {
                "name": "filter_data",
                "description": "Filter rows based on a condition. Use this to find rows that match specific criteria.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "column": {
                            "type": "string",
                            "description": "Column name to filter on"
                        },
                        "operator": {
                            "type": "string",
                            "enum": [">", "<", "==", "!=", ">=", "<=", "contains"],
                            "description": "Comparison operator"
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to compare against"
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "Sheet name (optional)"
                        }
                    },
                    "required": ["column", "operator", "value"]
                }
            },
            {
                "name": "calculate",
                "description": "Perform calculations on a column (sum, mean, median, count, min, max, std). Use this for accurate numerical analysis.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["sum", "mean", "median", "count", "min", "max", "std", "average"],
                            "description": "Calculation to perform"
                        },
                        "column": {
                            "type": "string",
                            "description": "Column name to calculate on"
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "Sheet name (optional)"
                        }
                    },
                    "required": ["operation", "column"]
                }
            },
            {
                "name": "get_unique_values",
                "description": "Get all unique values in a column. Useful for understanding categorical data or finding distinct entries.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "column": {
                            "type": "string",
                            "description": "Column name"
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "Sheet name (optional)"
                        }
                    },
                    "required": ["column"]
                }
            }
        ]

    def execute_tool(self, tool_name, tool_input):
        """Execute a tool call on the Excel processor"""
        if not self.excel_processor:
            return "Error: No Excel file loaded"

        try:
            if tool_name == "get_rows":
                return self.excel_processor.get_rows(
                    tool_input.get("start_row"),
                    tool_input.get("end_row"),
                    tool_input.get("sheet_name")
                )
            elif tool_name == "filter_data":
                return self.excel_processor.filter_data(
                    tool_input.get("column"),
                    tool_input.get("operator"),
                    tool_input.get("value"),
                    tool_input.get("sheet_name")
                )
            elif tool_name == "calculate":
                return self.excel_processor.calculate(
                    tool_input.get("operation"),
                    tool_input.get("column"),
                    tool_input.get("sheet_name")
                )
            elif tool_name == "get_unique_values":
                return self.excel_processor.get_unique_values(
                    tool_input.get("column"),
                    tool_input.get("sheet_name")
                )
            else:
                return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

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

**Important - You have access to powerful tools:**
- For large files (>100 rows), you see a summary with sample data
- Use the `get_rows` tool to fetch specific rows you need to see
- Use the `filter_data` tool to find rows matching criteria (e.g., sales > 1000)
- Use the `calculate` tool for accurate sums, averages, and other calculations on columns
- Use the `get_unique_values` tool to see all distinct values in a column

**Best practices:**
- For numerical questions (sums, averages), ALWAYS use the `calculate` tool for accuracy
- If asked about specific rows not in the sample, use `get_rows` tool
- If asked to find entries matching criteria, use `filter_data` tool
- Always base responses on actual data, not assumptions
- Be concise but thorough in explanations"""

    def chat(self, user_message, excel_data, conversation_history=None):
        """
        Send a message to AI provider and get a response with tool calling support

        Args:
            user_message: The user's question/message
            excel_data: The Excel data as text
            conversation_history: List of previous messages

        Returns:
            AI response text
        """
        system_prompt = self.create_system_prompt(excel_data)
        messages = []

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            if self.provider == 'anthropic':
                return self._chat_anthropic(system_prompt, messages)
            elif self.provider == 'openai':
                return self._chat_openai(system_prompt, messages)

        except Exception as e:
            return f"Error communicating with {self.provider.title()} AI: {str(e)}"

    def _chat_anthropic(self, system_prompt, messages):
        """Handle Anthropic chat with tool calling"""
        tools = self.get_tools() if self.excel_processor else []

        # Initial API call
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            tools=tools if tools else None
        )

        # Process tool calls if any
        while response.stop_reason == "tool_use":
            # Extract tool use from response
            tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)

            if not tool_use_block:
                break

            # Execute the tool
            tool_result = self.execute_tool(tool_use_block.name, tool_use_block.input)

            # Add assistant message and tool result to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": tool_result
                }]
            })

            # Continue conversation with tool result
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=tools
            )

        # Extract final text response
        text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
        return '\n'.join(text_blocks) if text_blocks else "No response generated"

    def _chat_openai(self, system_prompt, messages):
        """Handle OpenAI chat with tool calling"""
        tools_definitions = self.get_tools() if self.excel_processor else []

        # Convert tool schema to OpenAI format
        openai_tools = []
        for tool in tools_definitions:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })

        # Add system message
        openai_messages = [{"role": "system", "content": system_prompt}] + messages

        # Initial API call
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=openai_messages,
            tools=openai_tools if openai_tools else None
        )

        # Process tool calls if any
        while response.choices[0].finish_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls

            if not tool_calls:
                break

            # Add assistant message with tool calls
            openai_messages.append(response.choices[0].message)

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = self.execute_tool(tool_name, tool_args)

                # Add tool result to messages
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

            # Continue conversation with tool results
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=openai_messages,
                tools=openai_tools
            )

        return response.choices[0].message.content

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
