import base64
import io
import json
import logging
import statistics as stats_module
from collections import Counter
from datetime import date, timedelta

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import requests

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import (
    RegisterForm, MembershipForm,
    TrainingBookingForm, ReviewForm, PromocodeForm, TrainingForm
)
from .models import (
    Client, Trainer, Membership, MembershipType, Training, TrainingType,
    Review, Equipment, FAQ, Article, Vacancy, CompanyInfo, UserSessionLog
)

logger = logging.getLogger('gym')



def main_view(request):
    latest_training = TrainingType.objects.order_by('-id').first()
    articles = Article.objects.order_by('-published_at')[:3]
    return render(request, 'gym/main.html', {
        'latest_training': latest_training,
        'articles': articles
    })


def about_company_view(request):
    company = CompanyInfo.objects.first()
    return render(request, 'gym/about_company.html', {'company': company})


def contacts_view(request):
    trainers = Trainer.objects.all()
    company = CompanyInfo.objects.first()
    return render(request, 'gym/contacts.html', {
        'trainers': trainers,
        'company': company
    })


def faq_view(request):
    faqs = FAQ.objects.order_by('-created_at')
    return render(request, 'gym/faq.html', {'faqs': faqs})


def news_view(request):
    articles = Article.objects.order_by('-published_at')
    return render(request, 'gym/news.html', {'articles': articles})


def news_detail_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'gym/news_detail.html', {'article': article})


def privacy_policy_view(request):
    return render(request, 'gym/privacy_policy.html')


def vacancies_view(request):
    vacancies = Vacancy.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'gym/vacancies.html', {'vacancies': vacancies})


def trainers_view(request):
    trainers = Trainer.objects.all()
    return render(
        request,
        'gym/trainers.html',
        {'trainers': trainers}
    )


def trainer_detail_view(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    reviews = Review.objects.filter(trainer=trainer).order_by('-created_at')
    return render(request, 'gym/trainer_detail.html', {
        'trainer': trainer,
        'reviews': reviews
    })


def trainings_view(request):
    difficulty = request.GET.get('difficulty', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '')

    training_types = TrainingType.objects.all()

    if difficulty:
        training_types = training_types.filter(difficulty_level=difficulty)

    if type_filter:
        training_types = training_types.filter(type=type_filter)

    if search_query:
        training_types = training_types.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    sort_options = {
        'name': 'name',
        'name_desc': '-name',
        'duration': 'duration_minutes',
        'duration_desc': '-duration_minutes',
        'participants': 'max_participants',
        'participants_desc': '-max_participants',
    }
    if sort_by in sort_options:
        training_types = training_types.order_by(sort_options[sort_by])

    logger.info("Trainings page accessed: query=%s, sort=%s", search_query, sort_by)

    return render(request, 'gym/trainings.html', {
        'trainings': training_types,
        'difficulty': difficulty,
        'type_filter': type_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'type_choices': TrainingType.TrainingCategory.choices,
        'difficulty_choices': TrainingType.DifficultyLevel.choices
    })


def training_detail_view(request, pk):
    training_type = get_object_or_404(TrainingType, pk=pk)
    upcoming_trainings = Training.objects.filter(
        training_type=training_type,
        is_cancelled=False,
        date__gte=date.today()
    ).order_by('date', 'time')[:5]

    return render(request, 'gym/training_detail.html', {
        'training_type': training_type,
        'upcoming_trainings': upcoming_trainings
    })


def memberships_view(request):
    membership_types = MembershipType.objects.all()
    return render(
        request,
        'gym/memberships.html',
        {'membership_types': membership_types}
    )


def equipment_view(request):
    equipment = Equipment.objects.all()
    return render(request, 'gym/equipment.html', {'equipment': equipment})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Client.objects.create(
                user=user,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                patronymic=form.cleaned_data.get("patronymic", ""),
                address=form.cleaned_data["address"],
                phone=form.cleaned_data["phone"],
                birth_date=form.cleaned_data["birth_date"]
            )
            login(request, user)
            return redirect("profile")
    else:
        form = RegisterForm()
    return render(request, "gym/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("main")
    else:
        form = AuthenticationForm()
    return render(request, "gym/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("main")


@login_required
def profile_view(request):
    try:
        client = Client.objects.get(user=request.user)
        memberships = Membership.objects.filter(client=client).order_by('-purchase_date')
        trainings = Training.objects.filter(participants=client, date__gte=date.today()).order_by('date', 'time')
        reviews = Review.objects.filter(client=client).order_by('-created_at')
    except Client.DoesNotExist:
        memberships = []
        trainings = []
        reviews = []

    return render(request, 'gym/profile.html', {
        'memberships': memberships,
        'trainings': trainings,
        'reviews': reviews
    })


@login_required
def buy_membership_view(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return HttpResponseForbidden("Вы не зарегистрированы как клиент.")

    membership_types = MembershipType.objects.all()

    if request.method == 'POST':
        form = MembershipForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.client = client

            start_date = form.cleaned_data['start_date']
            duration_months = membership.membership_type.duration_months
            membership.end_date = start_date + timedelta(days=duration_months * 30)

            promo_code = form.cleaned_data.get('promo_code')
            if promo_code:
                pass

            membership.save()
            return redirect('profile')
    else:
        form = MembershipForm()

    return render(
        request,
        'gym/buy_membership.html',
        {
            'form': form,
            'membership_types': membership_types
         }
    )


@login_required
def book_training_view(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return HttpResponseForbidden("Вы не зарегистрированы как клиент.")

    if request.method == 'POST':
        form = TrainingBookingForm(request.POST)
        if form.is_valid():
            training = form.cleaned_data['training']
            if training.participants.count() < training.training_type.max_participants:
                training.participants.add(client)
                return redirect('profile')
            else:
                form.add_error('training', 'Тренировка заполнена.')
    else:
        form = TrainingBookingForm()

    return render(request, 'gym/book_training.html', {'form': form})


@login_required
def add_review_view(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return HttpResponseForbidden("Вы не зарегистрированы как клиент.")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.client = client
            review.save()
            return redirect('reviews')
    else:
        form = ReviewForm()
    return render(request, 'gym/add_review.html', {'form': form})


def reviews_view(request):
    reviews = Review.objects.select_related('client', 'trainer').order_by('-created_at')
    return render(request, 'gym/reviews.html', {'reviews': reviews})


@staff_member_required
def add_promocode_view(request):
    if request.method == 'POST':
        form = PromocodeForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.created_by = request.user
            promo.save()
            return redirect('trainer_dashboard')
    else:
        form = PromocodeForm()
    return render(request, 'gym/add_promocode.html', {'form': form})


@staff_member_required
def add_training_view(request):
    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('trainer_dashboard')
    else:
        form = TrainingForm()
    return render(request, 'gym/add_training.html', {'form': form})


@login_required
def trainer_dashboard_view(request):
    try:
        trainer = Trainer.objects.get(user=request.user)
    except Trainer.DoesNotExist:
        return HttpResponseForbidden("Вы не являетесь тренером.")

    trainings = Training.objects.filter(trainers=trainer).order_by('-date', '-time')
    clients = Client.objects.filter(trainings__trainers=trainer).distinct()

    return render(request, 'gym/trainer_dashboard.html', {
        'trainer': trainer,
        'trainings': trainings,
        'clients': clients
    })


@staff_member_required
def statistics_view(request):
    logs = UserSessionLog.objects.exclude(logout_time__isnull=True)
    data = []

    for log in logs:
        duration = log.duration_minutes()
        if duration:
            data.append({'user': log.user.username, 'duration_minutes': duration})

    df = pd.DataFrame(data)
    if df.empty:
        average = 0
        median_val = 0
        mode_val = 0
    else:
        durations = df['duration_minutes'].tolist()
        average = stats_module.mean(durations)
        median_val = stats_module.median(durations)
        try:
            mode_val = stats_module.mode(durations)
        except stats_module.StatisticsError:
            mode_val = durations[0] if durations else 0

    # Membership price statistics
    membership_prices = list(
        Membership.objects.values_list('membership_type__price', flat=True)
    )
    if membership_prices:
        prices_float = [float(p) for p in membership_prices]
        price_mean = stats_module.mean(prices_float)
        price_median = stats_module.median(prices_float)
        try:
            price_mode = stats_module.mode(prices_float)
        except stats_module.StatisticsError:
            price_mode = prices_float[0]
    else:
        price_mean = price_median = price_mode = 0

    plt.figure(figsize=(10, 6))
    if not df.empty:
        plt.bar(df['user'], df['duration_minutes'], color='skyblue', label='Пользователь')
        plt.axhline(y=average, color='red', linestyle='--', label=f'Среднее: {average:.1f} мин')
        plt.axhline(y=median_val, color='green', linestyle='-.', label=f'Медиана: {median_val:.1f} мин')
        plt.axhline(y=mode_val, color='orange', linestyle=':', label=f'Мода: {mode_val:.1f} мин')
    plt.title('Время, проведённое пользователями на сайте')
    plt.ylabel('Минуты')
    plt.xlabel('Пользователи')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()

    logger.info("Statistics page accessed by user %s", request.user.username)

    return render(request, 'gym/statistics.html', {
        'chart_data': chart_data,
        'average': round(average, 2),
        'median_val': round(median_val, 2),
        'mode_val': round(mode_val, 2),
        'price_mean': round(price_mean, 2),
        'price_median': round(price_median, 2),
        'price_mode': round(price_mode, 2),
    })


@staff_member_required
def membership_distribution_chart(request):
    membership_stats = Membership.objects.values('membership_type__name').annotate(total=Count('id'))
    labels = [item['membership_type__name'] for item in membership_stats]
    values = [item['total'] for item in membership_stats]

    if labels and values:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        graphic = base64.b64encode(image_png).decode('utf-8')
    else:
        graphic = None

    return render(request, 'gym/membership_chart.html', {'chart': graphic})


@staff_member_required
def training_group_report(request):
    """Список клиентов, занимающихся в определенной группе (тренировке)"""
    training_id = request.GET.get('training_id')
    trainings = Training.objects.all().order_by('-date', '-time')

    selected_training = None
    participants = []

    if training_id:
        selected_training = get_object_or_404(Training, id=training_id)
        participants = selected_training.participants.all()

    return render(request, 'gym/reports/training_group.html', {
        'trainings': trainings,
        'selected_training': selected_training,
        'participants': participants
    })


@staff_member_required
def training_count_report(request):
    """Подсчет количества занятий, проведенных в каждой из групп за определенный период"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    training_stats = []

    if start_date and end_date:
        trainings = Training.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            is_cancelled=False
        ).values('training_type__name').annotate(
            count=Count('id'),
            total_participants=Count('participants')
        ).order_by('-count')

        training_stats = list(trainings)

    return render(request, 'gym/reports/training_count.html', {
        'training_stats': training_stats,
        'start_date': start_date,
        'end_date': end_date
    })


@staff_member_required
def client_cost_report(request):
    """Определение стоимости оказанных услуг каждому клиенту за весь период"""
    clients = Client.objects.all()
    client_costs = []

    for client in clients:
        # Стоимость абонементов
        memberships = Membership.objects.filter(client=client)
        membership_cost = sum([m.membership_type.price for m in memberships])

        # Количество тренировок
        training_count = client.trainings.filter(is_cancelled=False).count()

        client_costs.append({
            'client': client,
            'membership_cost': membership_cost,
            'training_count': training_count,
            'total_cost': membership_cost
        })

    # Сортировка по общей стоимости
    client_costs.sort(key=lambda x: x['total_cost'], reverse=True)

    return render(request, 'gym/reports/client_cost.html', {
        'client_costs': client_costs
    })


def weather_api_view(request):
    """Внешний API #1 — погода в Минске (wttr.in)"""
    try:
        resp = requests.get(
            'https://wttr.in/Minsk?format=j1',
            timeout=5,
            headers={'Accept-Language': 'ru'}
        )
        resp.raise_for_status()
        weather_data = resp.json()
        current = weather_data.get('current_condition', [{}])[0]
        result = {
            'temp_c': current.get('temp_C', 'N/A'),
            'feels_like': current.get('FeelsLikeC', 'N/A'),
            'humidity': current.get('humidity', 'N/A'),
            'description': current.get('lang_ru', [{}])[0].get('value', current.get('weatherDesc', [{}])[0].get('value', '')),
            'wind_speed': current.get('windspeedKmph', 'N/A'),
        }
        logger.info("Weather API called successfully")
        return JsonResponse({'status': 'ok', 'weather': result})
    except Exception as e:
        logger.error("Weather API error: %s", str(e))
        return JsonResponse({'status': 'error', 'message': str(e)}, status=502)


def quote_api_view(request):
    """Внешний API #2 — мотивационная цитата (zenquotes.io)"""
    try:
        resp = requests.get('https://zenquotes.io/api/random', timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data and len(data) > 0:
            result = {
                'quote': data[0].get('q', ''),
                'author': data[0].get('a', ''),
            }
        else:
            result = {'quote': 'Никогда не сдавайся!', 'author': 'FitLife Gym'}
        logger.info("Quote API called successfully")
        return JsonResponse({'status': 'ok', 'quote': result})
    except Exception as e:
        logger.error("Quote API error: %s", str(e))
        return JsonResponse({
            'status': 'ok',
            'quote': {'quote': 'Сила — в движении!', 'author': 'FitLife Gym'}
        })
