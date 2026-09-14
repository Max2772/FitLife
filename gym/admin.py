from django.contrib import admin

from .models import (
    CompanyInfo, Trainer, Client, MembershipType, Membership,
    TrainingType, Training, Hall, Equipment, Review, Promocode,
    FAQ, Article, Vacancy, UserSessionLog, PersonalTraining,
    Partner, CompanyMilestone, Certificate, Employee,
    Cart, CartItem, Order, OrderItem,
)


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ['membership_type', 'start_date', 'end_date', 'price_paid', 'is_active']


class PersonalTrainingInline(admin.TabularInline):
    model = PersonalTraining
    extra = 0
    fields = ['trainer', 'date', 'start_time', 'end_time', 'price']


class CompanyMilestoneInline(admin.TabularInline):
    model = CompanyMilestone
    extra = 1
    fields = ['year', 'title', 'description']


class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 0
    fields = ['title', 'number', 'issued_by', 'issue_date', 'valid_until']


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'founding_year', 'phone', 'email']
    inlines = [CompanyMilestoneInline, CertificateInline]


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'specialization', 'experience_years', 'phone']
    list_filter = ['specialization']
    search_fields = ['last_name', 'first_name', 'email']
    inlines = [PersonalTrainingInline]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'registration_date']
    list_filter = ['registration_date']
    search_fields = ['last_name', 'first_name', 'phone']
    inlines = [MembershipInline, PersonalTrainingInline]


@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_months', 'price', 'includes_trainer', 'individual_session_price']
    list_filter = ['includes_trainer']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['client', 'membership_type', 'start_date', 'end_date', 'price_paid', 'is_active']
    list_filter = ['is_active', 'membership_type']
    search_fields = ['client__last_name', 'client__first_name']


class EquipmentInline(admin.TabularInline):
    model = Equipment
    extra = 0
    fields = ['name', 'quantity', 'condition']


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'capacity']
    search_fields = ['name']
    inlines = [EquipmentInline]


@admin.register(TrainingType)
class TrainingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'duration_minutes', 'max_participants', 'difficulty_level']
    list_filter = ['difficulty_level', 'type']


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['training_type', 'get_trainers', 'hall', 'date', 'time', 'end_time', 'is_cancelled']
    list_filter = ['is_cancelled', 'date', 'hall']
    filter_horizontal = ['trainers', 'participants']

    def get_trainers(self, obj):
        return ", ".join(str(t) for t in obj.trainers.all())
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


@admin.register(PersonalTraining)
class PersonalTrainingAdmin(admin.ModelAdmin):
    list_display = ['client', 'trainer', 'date', 'start_time', 'end_time', 'price']
    list_filter = ['date', 'trainer']
    search_fields = ['client__last_name', 'trainer__last_name']


# ------------------------- ЛР1: партнёры, сотрудники, магазин -------------------------


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'website', 'since_year', 'is_active', 'sort_order']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['sort_order', 'is_active']


@admin.register(CompanyMilestone)
class CompanyMilestoneAdmin(admin.ModelAdmin):
    list_display = ['year', 'title', 'company']
    list_filter = ['year']
    search_fields = ['title', 'description']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['title', 'number', 'issued_by', 'issue_date', 'valid_until']
    search_fields = ['title', 'number', 'issued_by']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'position', 'phone', 'email', 'sort_order']
    search_fields = ['last_name', 'first_name', 'position', 'duties']
    list_editable = ['sort_order']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['membership_type', 'quantity', 'added_at']
    readonly_fields = ['added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user', 'total_quantity', 'total_price', 'updated_at']
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['title', 'membership_type', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['number', 'full_name', 'total', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['number', 'full_name', 'email', 'phone']
    inlines = [OrderItemInline]
