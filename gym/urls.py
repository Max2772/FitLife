from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.main_view, name='main'),
    path('about/', views.about_company_view, name='about_company'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('faq/', views.faq_view, name='faq'),
    path('news/', views.news_view, name='news'),
    # re_path с регулярным выражением для новости (требование — использовать re_path)
    re_path(r'^news/(?P<pk>[0-9]+)/$', views.news_detail_view, name='news_detail'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
    path('vacancies/', views.vacancies_view, name='vacancies'),

    path('trainers/', views.trainers_view, name='trainers'),
    re_path(r'^trainers/(?P<pk>[0-9]+)/$', views.trainer_detail_view, name='trainer_detail'),

    path('trainings/', views.trainings_view, name='trainings'),
    path('trainings/<int:pk>/', views.training_detail_view, name='training_detail'),

    path('memberships/', views.memberships_view, name='memberships'),
    path('equipment/', views.equipment_view, name='equipment'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile_view, name='profile'),
    path('buy-membership/', views.buy_membership_view, name='buy_membership'),
    path('book-training/', views.book_training_view, name='book_training'),

    path('reviews/', views.reviews_view, name='reviews'),
    path('add-review/', views.add_review_view, name='add_review'),

    path('trainer-dashboard/', views.trainer_dashboard_view, name='trainer_dashboard'),
    path('add-promocode/', views.add_promocode_view, name='add_promocode'),
    path('add-training/', views.add_training_view, name='add_training'),

    path('statistics/', views.statistics_view, name='statistics'),
    path('membership-chart/', views.membership_distribution_chart, name='membership_chart'),

    path('reports/training-group/', views.training_group_report, name='training_group_report'),
    path('reports/training-count/', views.training_count_report, name='training_count_report'),
    path('reports/client-cost/', views.client_cost_report, name='client_cost_report'),

    # Внешние API
    path('api/weather/', views.weather_api_view, name='api_weather'),
    path('api/quote/', views.quote_api_view, name='api_quote'),
]
