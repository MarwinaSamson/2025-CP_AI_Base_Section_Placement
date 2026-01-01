from django.contrib import admin
from .models import UserProfile, Position, Department, Program, Teacher, Subject, Section

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


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'position', 'department', 'email', 'is_adviser', 'created_at']
    list_filter = ['is_adviser', 'department', 'position']
    search_fields = ['first_name', 'middle_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['position', 'department']

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'program', 'is_active', 'updated_at']
    list_filter = ['program', 'is_active']
    search_fields = ['code', 'name', 'description']
    autocomplete_fields = ['program']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'program', 'adviser', 'building', 'room', 'max_students', 'current_students']
    list_filter = ['program', 'building']
    search_fields = ['name', 'program__code', 'adviser__last_name', 'adviser__first_name']
    autocomplete_fields = ['program', 'adviser']
    readonly_fields = ['created_at', 'updated_at']