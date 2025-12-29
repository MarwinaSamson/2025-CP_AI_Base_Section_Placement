from django.contrib import admin
from .models import UserProfile, Position, Department, Program

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_user_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_user_count']
    
    def get_user_count(self, obj):
        return obj.get_user_count()
    get_user_count.short_description = 'Users Count'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_user_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_user_count']
    
    def get_user_count(self, obj):
        return obj.get_user_count()
    get_user_count.short_description = 'Users Count'

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'description', 'get_user_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_user_count']
    
    def get_user_count(self, obj):
        return obj.get_user_count()
    get_user_count.short_description = 'Users Count'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'program', 'position', 'department']
    list_filter = ['user_type', 'program', 'position', 'department']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']