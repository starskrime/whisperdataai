from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.files.storage import default_storage
import os

from .models import ExcelFile, ChatSession, ChatMessage
from .utils import ExcelProcessor, AIAgent, validate_excel_file


def index(request):
    """Home page - upload Excel file"""
    recent_files = ExcelFile.objects.all()[:5]

    # Get recent chat sessions (limit to 10)
    recent_sessions = ChatSession.objects.select_related('excel_file').all()[:10]

    return render(request, 'chat/index.html', {
        'recent_files': recent_files,
        'recent_sessions': recent_sessions
    })


@require_http_methods(["POST"])
def upload_file(request):
    """Handle Excel file upload"""
    if 'file' not in request.FILES:
        messages.error(request, "No file uploaded")
        return redirect('index')

    uploaded_file = request.FILES['file']

    # Validate file
    is_valid, error_message = validate_excel_file(uploaded_file)
    if not is_valid:
        messages.error(request, error_message)
        return redirect('index')

    try:
        # Save file to database
        excel_file = ExcelFile.objects.create(
            file=uploaded_file,
            filename=uploaded_file.name,
            file_size=uploaded_file.size
        )

        # Process Excel file to get sheet names
        processor = ExcelProcessor(excel_file.file.path)
        excel_file.sheet_names = processor.get_sheet_names()
        excel_file.save()

        # Create a new chat session
        session = ChatSession.objects.create(excel_file=excel_file)

        messages.success(request, f"File '{uploaded_file.name}' uploaded successfully!")
        return redirect('chat_session', session_id=session.id)

    except Exception as e:
        messages.error(request, f"Error processing file: {str(e)}")
        return redirect('index')


def chat_session(request, session_id):
    """Chat interface for a specific session"""
    session = get_object_or_404(ChatSession, id=session_id)
    messages_list = session.messages.all()

    # Get Excel data preview
    try:
        processor = ExcelProcessor(session.excel_file.file.path)
        summary = processor.get_sheet_summary()
    except Exception as e:
        summary = None

    return render(request, 'chat/chat.html', {
        'session': session,
        'messages': messages_list,
        'excel_summary': summary
    })


@require_http_methods(["POST"])
def send_message(request, session_id):
    """Handle sending a message in chat"""
    session = get_object_or_404(ChatSession, id=session_id)
    user_message = request.POST.get('message', '').strip()

    if not user_message:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    try:
        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message
        )

        # Get Excel data
        processor = ExcelProcessor(session.excel_file.file.path)
        excel_data = processor.get_all_data_as_text()

        # Get conversation history (exclude the message we just added)
        all_messages = list(session.messages.all())
        previous_messages = all_messages[:-1] if len(all_messages) > 1 else []
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in previous_messages
        ]

        # Get AI response with tool calling support
        ai_agent = AIAgent(excel_processor=processor)
        ai_response = ai_agent.chat(user_message, excel_data, conversation_history)

        # Save AI response
        assistant_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response
        )

        return JsonResponse({
            'success': True,
            'user_message': {
                'id': str(session.messages.filter(role='user').last().id),
                'content': user_message,
                'created_at': session.messages.filter(role='user').last().created_at.isoformat()
            },
            'assistant_message': {
                'id': str(assistant_message.id),
                'content': ai_response,
                'created_at': assistant_message.created_at.isoformat()
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def view_data(request, session_id):
    """View Excel data in a table format"""
    session = get_object_or_404(ChatSession, id=session_id)

    try:
        processor = ExcelProcessor(session.excel_file.file.path)
        sheet_name = request.GET.get('sheet', processor.get_sheet_names()[0])

        df = processor.read_sheet(sheet_name, max_rows=100)

        # Convert to HTML table
        table_html = df.to_html(classes='table table-striped table-bordered', index=False)

        return render(request, 'chat/view_data.html', {
            'session': session,
            'table_html': table_html,
            'sheet_name': sheet_name,
            'sheet_names': processor.get_sheet_names(),
            'total_rows': len(df)
        })

    except Exception as e:
        messages.error(request, f"Error loading data: {str(e)}")
        return redirect('chat_session', session_id=session_id)


def new_chat(request):
    """Start a new chat with the same file"""
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        excel_file = get_object_or_404(ExcelFile, id=file_id)

        # Create new session
        session = ChatSession.objects.create(excel_file=excel_file)

        return redirect('chat_session', session_id=session.id)

    return redirect('index')


@require_http_methods(["POST"])
def delete_chat(request, session_id):
    """Delete a chat session"""
    session = get_object_or_404(ChatSession, id=session_id)
    session.delete()
    messages.success(request, "Chat deleted successfully!")
    return redirect('index')
