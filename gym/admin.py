from django.contrib import admin
from .models import (
    CompanyInfo, Trainer, Client, MembershipType, Membership,
    TrainingType, Training, Hall, Equipment, Review, Promocode,
    FAQ, Article, Vacancy, UserSessionLog
)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'founding_year', 'phone', 'email']


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'specialization', 'experience_years', 'phone']
    list_filter = ['specialization']
    search_fields = ['last_name', 'first_name', 'email']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'registration_date']
    list_filter = ['registration_date']
    search_fields = ['last_name', 'first_name', 'phone']


@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_months', 'price', 'includes_trainer']
    list_filter = ['includes_trainer']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['client', 'membership_type', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'membership_type']
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(TrainingType)
class TrainingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'max_participants', 'difficulty_level']
    list_filter = ['difficulty_level']


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'capacity']
    search_fields = ['name']


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['training_type', 'get_trainers', 'hall', 'date', 'time', 'is_cancelled']
    list_filter = ['is_cancelled', 'date', 'hall']
    filter_horizontal = ['trainers', 'participants']

    def get_trainers(self, obj):
        return ", ".join([str(trainer) for trainer in obj.trainers.all()])
    get_trainers.short_description = 'Тренеры'


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'condition', 'hall', 'purchase_date']
    list_filter = ['condition', 'hall']
    search_fields = ['name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['client', 'trainer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']


@admin.register(Promocode)
class PromocodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'membership_type', 'is_active', 'valid_until']
    list_filter = ['is_active', 'membership_type']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'published_at']
    list_filter = ['published_at']
    search_fields = ['title', 'content']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'salary', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']


@admin.register(UserSessionLog)
class UserSessionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time']
    list_filter = ['login_time']
