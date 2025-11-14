from django.contrib import admin
from .models import ExcelFile, ChatSession, ChatMessage


@admin.register(ExcelFile)
class ExcelFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'uploaded_at', 'file_size']
    list_filter = ['uploaded_at']
    search_fields = ['filename']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['excel_file', 'created_at', 'last_activity']
    list_filter = ['created_at', 'last_activity']
    readonly_fields = ['id', 'created_at', 'last_activity']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'created_at', 'content_preview']
    list_filter = ['role', 'created_at']
    readonly_fields = ['id', 'created_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
