import base64
import io
import json
import logging
import statistics as stats_module
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import requests

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    RegisterForm, MembershipForm, TrainingBookingForm, ReviewForm,
    PromocodeForm, TrainingForm, PersonalTrainingForm, TrainerForm,
    get_ordered_trainers,
)
from .models import (
    Client, Trainer, Membership, MembershipType, Training, TrainingType,
    Review, Equipment, FAQ, Article, Vacancy, CompanyInfo, UserSessionLog,
    Hall, Promocode, PersonalTraining,
)
from .utils import (
    apply_promocode_discount,
    calculate_age,
    dual_datetime_display,
    get_valid_promocode_for_membership,
)

logger = logging.getLogger('gym')


def main_view(request):
    latest_article = Article.objects.order_by('-published_at').first()
    articles = Article.objects.order_by('-published_at')[:3]
    return render(request, 'gym/main.html', {
        'latest_article': latest_article,
        'articles': articles,
    })


def about_company_view(request):
    company = CompanyInfo.objects.first()
    years_on_market = date.today().year - company.founding_year if company else None
    return render(request, 'gym/about_company.html', {
        'company': company,
        'years_on_market': years_on_market,
    })


def contacts_view(request):
    trainers = get_ordered_trainers()
    company = CompanyInfo.objects.first()
    return render(request, 'gym/contacts.html', {
        'trainers': trainers,
        'company': company,
    })


def faq_view(request):
    faqs = FAQ.objects.order_by('-created_at')
    company = CompanyInfo.objects.first()
    return render(request, 'gym/faq.html', {'faqs': faqs, 'company': company})


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
    company = CompanyInfo.objects.first()
    return render(request, 'gym/vacancies.html', {
        'vacancies': vacancies,
        'company': company,
    })


def promocodes_view(request):
    today = date.today()
    active = Promocode.objects.filter(is_active=True).filter(
        Q(valid_until__isnull=True) | Q(valid_until__gte=today)
    ).select_related('membership_type')
    archived = Promocode.objects.filter(
        Q(is_active=False) | Q(valid_until__lt=today)
    ).select_related('membership_type')
    return render(request, 'gym/promocodes.html', {
        'active_promocodes': active,
        'archived_promocodes': archived,
    })


def halls_view(request):
    halls = Hall.objects.prefetch_related('equipment').all()
    return render(request, 'gym/halls.html', {'halls': halls})


def trainers_view(request):
    trainers = get_ordered_trainers()
    return render(request, 'gym/trainers.html', {'trainers': trainers})


def trainer_detail_view(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    review_base = Review.objects.filter(trainer=trainer)
    stats = review_base.aggregate(avg=Avg('rating'), cnt=Count('id'))
    rating_avg = stats['avg']
    reviews_count = stats['cnt']
    reviews = review_base.select_related('client').order_by('-created_at')
    training_type_ids = (
        Training.objects.filter(trainers=trainer)
        .values_list('training_type_id', flat=True)
        .distinct()
    )
    trainer_trainings = TrainingType.objects.filter(pk__in=list(training_type_ids)).order_by('name')
    return render(request, 'gym/trainer_detail.html', {
        'trainer': trainer,
        'reviews': reviews,
        'reviews_count': reviews_count,
        'trainer_trainings': trainer_trainings,
        'rating_avg': rating_avg,
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
        'difficulty_choices': TrainingType.DifficultyLevel.choices,
    })


def training_detail_view(request, pk):
    training_type = get_object_or_404(TrainingType, pk=pk)
    upcoming_trainings = (
        Training.objects.filter(
            training_type=training_type,
            is_cancelled=False,
            date__gte=date.today(),
        )
        .select_related('hall')
        .prefetch_related('trainers', 'participants')
        .order_by('date', 'time')[:10]
    )
    type_trainers = (
        Trainer.objects.filter(trainings__training_type=training_type)
        .distinct()
        .order_by('last_name', 'first_name')
    )
    trainer_ids = list(type_trainers.values_list('id', flat=True))
    reviews = (
        Review.objects.filter(trainer_id__in=trainer_ids)
        .select_related('client', 'trainer')
        .order_by('-created_at')[:10]
        if trainer_ids
        else Review.objects.none()
    )
    return render(request, 'gym/training_detail.html', {
        'training': training_type,
        'upcoming_trainings': upcoming_trainings,
        'type_trainers': type_trainers,
        'reviews': reviews,
    })


def memberships_view(request):
    membership_types = MembershipType.objects.all()
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        try:
            membership_types = membership_types.filter(price__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            membership_types = membership_types.filter(price__lte=Decimal(max_price))
        except Exception:
            pass
    return render(request, 'gym/memberships.html', {
        'membership_types': membership_types,
        'min_price': min_price,
        'max_price': max_price,
    })


def equipment_view(request):
    equipment = Equipment.objects.select_related('hall').all()
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
                birth_date=form.cleaned_data["birth_date"],
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
        memberships = Membership.objects.filter(client=client).select_related(
            'membership_type', 'promocode'
        ).order_by('-purchase_date')
        trainings = (
            Training.objects.filter(participants=client, date__gte=date.today())
            .select_related('training_type')
            .prefetch_related('trainers')
            .order_by('date', 'time')
        )
        reviews = Review.objects.filter(client=client).order_by('-created_at')
        personal_trainings = (
            PersonalTraining.objects.filter(client=client, date__gte=date.today())
            .select_related('trainer', 'training_type')
            .order_by('date', 'start_time')
        )
        promocodes = Promocode.objects.filter(is_active=True)[:5]
    except Client.DoesNotExist:
        client = None
        memberships = []
        trainings = []
        reviews = []
        personal_trainings = []
        promocodes = []

    return render(request, 'gym/profile.html', {
        'client': client,
        'memberships': memberships,
        'trainings': trainings,
        'reviews': reviews,
        'personal_trainings': personal_trainings,
        'promocodes': promocodes,
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

            base_price = membership.membership_type.price
            promo = form.cleaned_data.get('promo_code')
            membership.promocode = promo
            membership.price_paid = apply_promocode_discount(base_price, promo)
            membership.save()
            messages.success(request, f'Абонемент оформлен. Оплачено: {membership.price_paid} BYN.')
            return redirect('profile')
    else:
        form = MembershipForm()

    return render(request, 'gym/buy_membership.html', {
        'form': form,
        'membership_types': membership_types,
    })


@login_required
@require_POST
def validate_membership_promocode_view(request):
    """Проверка промокода для страницы покупки абонемента (AJAX)."""
    try:
        Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Вы не зарегистрированы как клиент.'}, status=403)

    code = request.POST.get('code', '')
    membership_type_id = request.POST.get('membership_type', '').strip()
    membership_type = None
    if membership_type_id:
        try:
            membership_type = MembershipType.objects.get(pk=int(membership_type_id))
        except (ValueError, MembershipType.DoesNotExist):
            return JsonResponse({'ok': False, 'error': 'Некорректный тип абонемента.'}, status=400)

    promo, err = get_valid_promocode_for_membership(code, membership_type)
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)

    if not code or not str(code).strip():
        return JsonResponse({
            'ok': True,
            'cleared': True,
            'discount_percent': 0,
            'price_final': None,
        })

    base_price = membership_type.price
    final = apply_promocode_discount(base_price, promo)
    return JsonResponse({
        'ok': True,
        'cleared': False,
        'discount_percent': promo.discount_percent,
        'price_final': str(final),
        'base_price': str(base_price),
    })


def _create_personal_training_from_booking(client, cleaned_data):
    """Создаёт индивидуальное занятие по данным формы записи."""
    booking_date = cleaned_data['date']
    start_time = cleaned_data['time']
    trainer = cleaned_data['trainer']
    notes = cleaned_data.get('notes', '')
    training_type = (
        TrainingType.objects.filter(training__trainers=trainer).distinct().first()
        or TrainingType.objects.first()
    )
    duration_minutes = training_type.duration_minutes if training_type else 60
    end_dt = datetime.combine(booking_date, start_time) + timedelta(minutes=duration_minutes)
    price = (
        MembershipType.objects.order_by('pk')
        .values_list('individual_session_price', flat=True)
        .first()
    ) or Decimal('30.00')
    return PersonalTraining.objects.create(
        client=client,
        trainer=trainer,
        training_type=training_type,
        date=booking_date,
        start_time=start_time,
        end_time=end_dt.time(),
        price=price,
        notes=notes,
    )


def _booking_form_kwargs_from_request(request):
    """Параметры GET для формы записи: type, training, trainer."""
    kwargs = {}
    training_type = None
    type_id = request.GET.get('type')
    if type_id:
        try:
            training_type = TrainingType.objects.get(pk=int(type_id))
            kwargs['training_type_id'] = training_type.pk
        except (TypeError, ValueError, TrainingType.DoesNotExist):
            training_type = None
    training_id = request.GET.get('training')
    if training_id:
        try:
            kwargs['initial_training_id'] = int(training_id)
            if training_type is None:
                slot = Training.objects.filter(pk=kwargs['initial_training_id']).first()
                if slot:
                    kwargs['training_type_id'] = slot.training_type_id
                    training_type = slot.training_type
        except (TypeError, ValueError):
            pass
    trainer_id = request.GET.get('trainer')
    trainer_initial = None
    if trainer_id:
        try:
            trainer_initial = int(trainer_id)
        except (TypeError, ValueError):
            pass
    return kwargs, training_type, trainer_initial


@login_required
def book_training_view(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return HttpResponseForbidden("Вы не зарегистрированы как клиент.")

    form_kwargs, training_type, trainer_initial = _booking_form_kwargs_from_request(request)

    if request.method == 'POST':
        form = TrainingBookingForm(request.POST, **form_kwargs)
        form.client = client
        if form.is_valid():
            if form.cleaned_data.get('book_personal'):
                _create_personal_training_from_booking(client, form.cleaned_data)
                messages.success(request, 'Вы записаны на индивидуальное занятие.')
            else:
                training = form.cleaned_data['training']
                training.participants.add(client)
                messages.success(
                    request,
                    f'Вы записаны на «{training.training_type}» '
                    f'({training.date:%d.%m.%Y} в {training.time:%H:%M}).',
                )
            return redirect('profile')
    else:
        form = TrainingBookingForm(**form_kwargs)
        if trainer_initial:
            form.fields['trainer'].initial = trainer_initial

    has_sessions = form.fields['session'].queryset.exists()
    trainer_value = form['trainer'].value() if form.is_bound else form.fields['trainer'].initial
    return render(request, 'gym/book_training.html', {
        'form': form,
        'trainers': get_ordered_trainers(),
        'today': date.today(),
        'selected_trainer_id': trainer_value,
        'training_type': training_type,
        'has_sessions': has_sessions,
    })


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
    today = date.today()
    if request.method == 'POST':
        form = PromocodeForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.created_by = request.user
            promo.save()
            return redirect('add_promocode')
    else:
        form = PromocodeForm()

    active_promocodes = Promocode.objects.filter(is_active=True).filter(
        Q(valid_until__isnull=True) | Q(valid_until__gte=today)
    )
    return render(request, 'gym/add_promocode.html', {
        'form': form,
        'active_promocodes': active_promocodes,
    })


@staff_member_required
def add_training_view(request):
    current_trainer_id = None
    try:
        current_trainer_id = Trainer.objects.get(user=request.user).pk
    except Trainer.DoesNotExist:
        pass

    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('trainer_dashboard')
    else:
        form = TrainingForm()
    return render(request, 'gym/add_training.html', {
        'form': form,
        'trainers': get_ordered_trainers(),
        'current_trainer_id': current_trainer_id,
    })


def _get_linked_trainer(user):
    try:
        return Trainer.objects.get(user=user)
    except Trainer.DoesNotExist:
        return None


def _is_gym_manager(user):
    """Администратор зала: superuser или staff без привязки к Trainer."""
    return user.is_superuser or (user.is_staff and _get_linked_trainer(user) is None)


def _personal_trainings_queryset_for_user(user):
    qs = PersonalTraining.objects.select_related('client', 'trainer', 'training_type')
    if _is_gym_manager(user):
        return qs.order_by('-date', '-start_time')
    trainer = _get_linked_trainer(user)
    if trainer:
        return qs.filter(trainer=trainer).order_by('-date', '-start_time')
    return qs.none()


def _get_personal_training_for_user(user, pk):
    session = get_object_or_404(PersonalTraining, pk=pk)
    if _is_gym_manager(user):
        return session
    trainer = _get_linked_trainer(user)
    if trainer and session.trainer_id == trainer.pk:
        return session
    return None


@login_required
def trainer_dashboard_view(request):
    try:
        trainer = Trainer.objects.get(user=request.user)
    except Trainer.DoesNotExist:
        if request.user.is_staff:
            return redirect('statistics')
        return HttpResponseForbidden("Вы не являетесь тренером.")

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    trainings = (
        Training.objects.filter(trainers=trainer, is_cancelled=False)
        .select_related('training_type', 'hall')
        .prefetch_related('participants')
        .order_by('date', 'time')
    )
    upcoming_trainings = trainings.filter(date__gte=today)[:10]
    personal_trainings = (
        PersonalTraining.objects.filter(trainer=trainer, date__gte=today)
        .select_related('client', 'training_type')
        .order_by('date', 'start_time')[:10]
    )
    clients_qs = Client.objects.filter(
        Q(trainings__trainers=trainer) | Q(personal_trainings__trainer=trainer)
    ).distinct()
    total_clients = clients_qs.count()
    clients_preview = list(clients_qs[:12])
    recent_reviews = (
        Review.objects.filter(trainer=trainer)
        .select_related('client')
        .order_by('-created_at')[:5]
    )
    avg_rating = (
        Review.objects.filter(trainer=trainer).aggregate(avg=Avg('rating'))['avg'] or 0
    )
    today_group_count = trainings.filter(date=today).count()
    today_personal_count = PersonalTraining.objects.filter(trainer=trainer, date=today).count()
    week_trainings_count = trainings.filter(
        date__gte=week_start, date__lte=week_end
    ).count()

    return render(request, 'gym/trainer_dashboard.html', {
        'trainer': trainer,
        'upcoming_trainings': upcoming_trainings,
        'personal_trainings': personal_trainings,
        'clients': clients_preview,
        'total_clients': total_clients,
        'more_clients_count': max(0, total_clients - len(clients_preview)),
        'recent_reviews': recent_reviews,
        'avg_rating': avg_rating,
        'today_sessions': today_group_count + today_personal_count,
        'week_trainings_count': week_trainings_count,
    })


@staff_member_required
def personal_training_list_view(request):
    sessions = _personal_trainings_queryset_for_user(request.user)
    return render(request, 'gym/personal_training_list.html', {
        'sessions': sessions,
        'is_gym_manager': _is_gym_manager(request.user),
        'linked_trainer': _get_linked_trainer(request.user),
    })


@staff_member_required
def personal_training_create_view(request):
    linked_trainer = _get_linked_trainer(request.user)
    lock_trainer = linked_trainer if not _is_gym_manager(request.user) else None

    if request.method == 'POST':
        form = PersonalTrainingForm(request.POST, locked_trainer=lock_trainer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Индивидуальное занятие создано.')
            return redirect('personal_training_list')
    else:
        form = PersonalTrainingForm(locked_trainer=lock_trainer)
    return render(request, 'gym/personal_training_form.html', {'form': form, 'title': 'Создать занятие'})


@staff_member_required
def personal_training_update_view(request, pk):
    session = _get_personal_training_for_user(request.user, pk)
    if session is None:
        return HttpResponseForbidden("Вы можете редактировать только свои занятия.")

    linked_trainer = _get_linked_trainer(request.user)
    lock_trainer = linked_trainer if not _is_gym_manager(request.user) else None

    if request.method == 'POST':
        form = PersonalTrainingForm(request.POST, instance=session, locked_trainer=lock_trainer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Занятие обновлено.')
            return redirect('personal_training_list')
    else:
        form = PersonalTrainingForm(instance=session, locked_trainer=lock_trainer)
    return render(request, 'gym/personal_training_form.html', {
        'form': form, 'title': 'Редактировать занятие', 'session': session,
    })


@staff_member_required
def personal_training_delete_view(request, pk):
    session = _get_personal_training_for_user(request.user, pk)
    if session is None:
        return HttpResponseForbidden("Вы можете удалять только свои занятия.")

    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Занятие удалено.')
        return redirect('personal_training_list')
    return render(request, 'gym/personal_training_confirm_delete.html', {'session': session})


@staff_member_required
def client_delete_view(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        user = client.user
        client.delete()
        user.delete()
        messages.success(request, 'Клиент удалён из базы.')
        return redirect('client_cost_report')
    return render(request, 'gym/client_confirm_delete.html', {'client': client})


@staff_member_required
def increase_individual_price_view(request):
    if not _is_gym_manager(request.user):
        return HttpResponseForbidden("Изменение цен доступно только администратору.")
    if request.method == 'POST':
        type_id = request.POST.get('membership_type_id')
        new_price = request.POST.get('new_price')
        if type_id and new_price:
            mt = get_object_or_404(MembershipType, pk=type_id)
            mt.individual_session_price = Decimal(new_price)
            mt.save()
            messages.success(request, f'Цена индивидуальных занятий для «{mt.name}» обновлена.')
        return redirect('increase_individual_price')
    membership_types = MembershipType.objects.all()
    return render(request, 'gym/increase_individual_price.html', {
        'membership_types': membership_types,
    })


def _build_session_chart(logs):
    data = []
    for log in logs:
        duration = log.duration_minutes()
        if duration:
            data.append({'user': log.user.username, 'duration_minutes': duration})

    df = pd.DataFrame(data)
    if df.empty:
        return None, 0, 0, 0

    durations = df['duration_minutes'].tolist()
    average = stats_module.mean(durations)
    median_val = stats_module.median(durations)
    try:
        mode_val = stats_module.mode(durations)
    except stats_module.StatisticsError:
        mode_val = durations[0]

    plt.figure(figsize=(10, 6))
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
    return chart_data, average, median_val, mode_val


@staff_member_required
def statistics_view(request):
    logs = UserSessionLog.objects.exclude(logout_time__isnull=True).select_related('user')
    chart_data, average, median_val, mode_val = _build_session_chart(logs)
    if chart_data is None:
        average = median_val = mode_val = 0
        chart_data = ''

    membership_prices = list(
        Membership.objects.values_list('price_paid', 'membership_type__price')
    )
    prices_float = [
        float(p[0] if p[0] is not None else p[1]) for p in membership_prices if p[1] is not None
    ]
    if prices_float:
        price_mean = stats_module.mean(prices_float)
        price_median = stats_module.median(prices_float)
        try:
            price_mode = stats_module.mode(prices_float)
        except stats_module.StatisticsError:
            price_mode = prices_float[0]
    else:
        price_mean = price_median = price_mode = 0

    today = date.today()
    month_start = today.replace(day=1)
    total_clients = Client.objects.count()
    new_clients_month = Client.objects.filter(registration_date__date__gte=month_start).count()
    active_memberships = Membership.objects.filter(is_active=True).count()
    trainings_month = Training.objects.filter(date__gte=month_start, is_cancelled=False).count()
    revenue_month = Membership.objects.filter(
        purchase_date__date__gte=month_start
    ).aggregate(total=Coalesce(Sum('price_paid'), Sum('membership_type__price')))['total'] or 0

    popular_trainings = list(
        TrainingType.objects.annotate(
            bookings_count=Count('training__participants', distinct=True),
        ).order_by('-bookings_count')[:5]
    )
    for item in popular_trainings:
        pt_revenue = PersonalTraining.objects.filter(training_type=item).aggregate(
            total=Coalesce(Sum('price'), Decimal('0'))
        )['total']
        item.revenue = pt_revenue or Decimal(item.bookings_count or 0) * Decimal('15')

    top_trainers = Trainer.objects.annotate(
        clients_count=Count('trainings__participants', distinct=True),
    ).order_by('-clients_count')[:5]
    for trainer in top_trainers:
        reviews = Review.objects.filter(trainer=trainer)
        trainer.rating = (
            stats_module.mean([r.rating for r in reviews]) if reviews.exists() else 0
        )

    attendance_by_weekday = [0] * 7
    for training in Training.objects.filter(is_cancelled=False):
        attendance_by_weekday[training.date.weekday()] += training.participants.count()
    attendance_data = json.dumps(attendance_by_weekday)

    membership_sales = list(
        MembershipType.objects.annotate(
            sold_count=Count('membership'),
            revenue=Coalesce(Sum('membership__price_paid'), Decimal('0')),
        ).order_by('-sold_count')
    )

    recent_reviews = Review.objects.select_related('client').order_by('-created_at')[:5]

    ages = [calculate_age(c.birth_date) for c in Client.objects.all() if c.birth_date]
    if ages:
        age_mean = round(stats_module.mean(ages), 1)
        age_median = round(stats_module.median(ages), 1)
    else:
        age_mean = age_median = 0

    clients_alphabetical = []
    total_sales_all = Decimal('0')
    for client in Client.objects.order_by('last_name', 'first_name'):
        memberships = Membership.objects.filter(client=client)
        total = sum(
            (m.price_paid or m.membership_type.price) for m in memberships
        )
        total_sales_all += total
        clients_alphabetical.append({'client': client, 'total_sales': total})

    type_popularity = TrainingType.objects.annotate(
        cnt=Count('training__participants', distinct=True)
    ).order_by('-cnt').first()
    type_profit = MembershipType.objects.annotate(
        rev=Coalesce(Sum('membership__price_paid'), Decimal('0'))
    ).order_by('-rev').first()

    logger.info("Statistics page accessed by user %s", request.user.username)

    return render(request, 'gym/statistics.html', {
        'chart_data': chart_data,
        'average': round(average, 2),
        'median_val': round(median_val, 2),
        'mode_val': round(mode_val, 2),
        'price_mean': round(price_mean, 2),
        'price_median': round(price_median, 2),
        'price_mode': round(price_mode, 2),
        'total_clients': total_clients,
        'new_clients_month': new_clients_month,
        'active_memberships': active_memberships,
        'trainings_month': trainings_month,
        'revenue_month': revenue_month,
        'popular_trainings': popular_trainings,
        'top_trainers': top_trainers,
        'attendance_data': attendance_data,
        'membership_sales': membership_sales,
        'recent_reviews': recent_reviews,
        'age_mean': age_mean,
        'age_median': age_median,
        'clients_alphabetical': clients_alphabetical,
        'total_sales_all': total_sales_all,
        'most_popular_type': type_popularity,
        'most_profitable_type': type_profit,
    })


@staff_member_required
def membership_distribution_chart(request):
    membership_stats = Membership.objects.values('membership_type__name').annotate(total=Count('id'))
    labels = [item['membership_type__name'] for item in membership_stats]
    values = [item['total'] for item in membership_stats]

    graphic = None
    if labels and values:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        plt.close()

    return render(request, 'gym/membership_chart.html', {'chart': graphic})


@staff_member_required
def training_group_report(request):
    training_id = request.GET.get('training_id')
    trainings = Training.objects.all().order_by('-date', '-time')
    selected_training = None
    participants = []
    if training_id:
        selected_training = get_object_or_404(Training, id=training_id)
        participants = selected_training.participants.all().order_by('last_name', 'first_name')
    return render(request, 'gym/reports/training_group.html', {
        'trainings': trainings,
        'selected_training': selected_training,
        'participants': participants,
    })


@staff_member_required
def training_count_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    training_stats = []
    if start_date and end_date:
        training_stats = list(
            Training.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_cancelled=False,
            ).values('training_type__name').annotate(
                count=Count('id'),
                total_participants=Count('participants'),
            ).order_by('-count')
        )
    return render(request, 'gym/reports/training_count.html', {
        'training_stats': training_stats,
        'start_date': start_date,
        'end_date': end_date,
    })


@staff_member_required
def client_cost_report(request):
    client_costs = []
    for client in Client.objects.all().order_by('last_name', 'first_name'):
        memberships = Membership.objects.filter(client=client)
        membership_cost = sum(
            (m.price_paid or m.membership_type.price) for m in memberships
        )
        personal_cost = PersonalTraining.objects.filter(client=client).aggregate(
            total=Coalesce(Sum('price'), Decimal('0'))
        )['total']
        training_count = client.trainings.filter(is_cancelled=False).count()
        client_costs.append({
            'client': client,
            'membership_cost': membership_cost,
            'personal_cost': personal_cost,
            'training_count': training_count,
            'total_cost': membership_cost + personal_cost,
        })
    client_costs.sort(key=lambda x: x['total_cost'], reverse=True)
    return render(request, 'gym/reports/client_cost.html', {'client_costs': client_costs})


@login_required
def weather_api_view(request):
    try:
        resp = requests.get(
            'https://wttr.in/Minsk?format=j1',
            timeout=5,
            headers={'Accept-Language': 'ru'},
        )
        resp.raise_for_status()
        weather_data = resp.json()
        current = weather_data.get('current_condition', [{}])[0]
        result = {
            'temp_c': current.get('temp_C', 'N/A'),
            'feels_like': current.get('FeelsLikeC', 'N/A'),
            'humidity': current.get('humidity', 'N/A'),
            'description': current.get('lang_ru', [{}])[0].get(
                'value', current.get('weatherDesc', [{}])[0].get('value', '')
            ),
            'wind_speed': current.get('windspeedKmph', 'N/A'),
        }
        logger.info("Weather API called by %s", request.user.username)
        return JsonResponse({'status': 'ok', 'weather': result})
    except Exception as e:
        logger.error("Weather API error: %s", str(e))
        return JsonResponse({'status': 'error', 'message': str(e)}, status=502)


@login_required
def quote_api_view(request):
    try:
        resp = requests.get('https://zenquotes.io/api/random', timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data:
            result = {'quote': data[0].get('q', ''), 'author': data[0].get('a', '')}
        else:
            result = {'quote': 'Никогда не сдавайся!', 'author': 'FitLife Gym'}
        logger.info("Quote API called by %s", request.user.username)
        return JsonResponse({'status': 'ok', 'quote': result})
    except Exception as e:
        logger.error("Quote API error: %s", str(e))
        return JsonResponse({
            'status': 'ok',
            'quote': {'quote': 'Сила — в движении!', 'author': 'FitLife Gym'},
        })
