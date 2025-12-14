from django.contrib import admin
from .models import User, Post, Comment, Problem, Reply

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'phone']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'author__role', 'created_at']
    list_filter = ['created_at', 'author__role']
    search_fields = ['title', 'content', 'author__username']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['content', 'author', 'post', 'created_at']
    list_filter = ['created_at', 'author__role']
    search_fields = ['content', 'author__username', 'post__title']

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'farmer', 'created_at']
    list_filter = ['created_at', 'farmer__role']
    search_fields = ['title', 'description', 'farmer__username']

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['content', 'admin', 'problem', 'created_at']
    list_filter = ['created_at', 'admin__role']
    search_fields = ['content', 'admin__username', 'problem__title']
