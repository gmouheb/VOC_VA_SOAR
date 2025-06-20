from django.contrib import admin
from .models import ChatConversation, ChatMessage

# Register your models here.
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'analyst', 'vulnerability', 'created_at', 'updated_at', 'message_count')
    list_filter = ('created_at', 'updated_at', 'analyst')
    search_fields = ('title', 'analyst__email', 'vulnerability__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Conversation Information', {
            'fields': ('title', 'analyst', 'vulnerability')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def message_count(self, obj):
        """Display the number of messages in the conversation"""
        return obj.messages.count()
    message_count.short_description = "Messages"

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('get_conversation_title', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at', 'conversation__analyst')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Message Information', {
            'fields': ('conversation', 'role', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def get_conversation_title(self, obj):
        """Display the title of the conversation"""
        return obj.conversation.title
    get_conversation_title.short_description = "Conversation"

    def content_preview(self, obj):
        """Display a preview of the message content"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"

admin.site.register(ChatConversation, ChatConversationAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
