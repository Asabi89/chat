from django.contrib import admin
from .models import Conversation, Message, MessageRead, MessageReaction

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('id', 'sender', 'message_type', 'text', 'file', 'created_at', 'is_edited', 'edited_at')
    can_delete = False
    max_num = 10
    show_change_link = True

class MessageReadInline(admin.TabularInline):
    model = MessageRead
    extra = 0
    readonly_fields = ('user', 'read_at')
    can_delete = False
    max_num = 10

class MessageReactionInline(admin.TabularInline):
    model = MessageReaction
    extra = 0
    readonly_fields = ('user', 'reaction_type', 'created_at')
    can_delete = False
    max_num = 10

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_group_chat', 'group_name', 'created_at', 'updated_at', 'get_participants')
    list_filter = ('is_group_chat', 'created_at', 'updated_at')
    search_fields = ('group_name', 'participants__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    
    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()[:5]])
    get_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'message_type', 'short_text', 'created_at', 'is_edited')
    list_filter = ('message_type', 'created_at', 'is_edited')
    search_fields = ('text', 'sender__username', 'conversation__group_name')
    readonly_fields = ('id', 'created_at')
    inlines = [MessageReadInline, MessageReactionInline]
    
    def short_text(self, obj):
        if obj.text:
            return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
        return f"[{obj.get_message_type_display()}]"
    short_text.short_description = 'Message'

@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__username',)
    readonly_fields = ('id', 'read_at')

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('id', 'created_at')
