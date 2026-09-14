from datetime import date, datetime, timedelta
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import (
    Client, Trainer, Membership, MembershipType, Training,
    Review, Promocode, PersonalTraining,
)
from .utils import (
    calculate_age,
    format_belarus_phone,
    get_valid_promocode_for_membership,
    validate_minimum_age,
)


# ==========================================================================
# ЛР1: виджеты для input-типов, которых нет в стандартном наборе Django.
# Тип поля нужно задавать через input_type, а не через attrs={'type': ...},
# иначе в разметку попадут два атрибута type и документ не пройдёт валидацию.
# ==========================================================================


class TelInput(forms.TextInput):
    input_type = 'tel'


class DateInput(forms.DateInput):
    """<input type="date">. У стандартного forms.DateInput input_type = 'text'."""

    input_type = 'date'

    def __init__(self, attrs=None, date_format='%Y-%m-%d'):
        # format обязателен: без него Django печатает дату как 12.09.2026,
        # а input[type=date] принимает только ГГГГ-ММ-ДД.
        super().__init__(attrs=attrs, format=date_format)


class TimeInput(forms.TimeInput):
    """<input type="time">. У стандартного forms.TimeInput input_type = 'text'."""

    input_type = 'time'

    def __init__(self, attrs=None, time_format='%H:%M'):
        super().__init__(attrs=attrs, format=time_format)


class RangeInput(forms.NumberInput):
    input_type = 'range'


class ColorInput(forms.TextInput):
    input_type = 'color'



def get_ordered_trainers():
    return Trainer.objects.order_by('last_name', 'first_name')


def get_available_trainings_queryset(training_type_id=None):
    """Групповые занятия с свободными местами (не отменены, дата в будущем)."""
    qs = (
        Training.objects.filter(is_cancelled=False, date__gte=date.today())
        .select_related('training_type', 'hall')
        .prefetch_related('trainers', 'participants')
        .order_by('date', 'time')
    )
    if training_type_id:
        qs = qs.filter(training_type_id=training_type_id)
    available_ids = [
        t.pk for t in qs
        if t.participants.count() < t.training_type.max_participants
    ]
    return Training.objects.filter(pk__in=available_ids).select_related(
        'training_type', 'hall'
    ).prefetch_related('trainers', 'participants').order_by('date', 'time')


def format_training_session_label(training):
    taken = training.participants.count()
    total = training.training_type.max_participants
    trainers = ', '.join(tr.full_name for tr in training.trainers.all()[:2])
    hall = f', {training.hall.name}' if training.hall else ''
    trainer_part = f' — {trainers}' if trainers else ''
    return (
        f'{training.date:%d.%m.%Y} {training.time:%H:%M} — '
        f'{training.training_type}{trainer_part}{hall} '
        f'({taken}/{total} мест)'
    )


def setup_trainer_field(field, *, empty_label=None, required=None):
    """Единые настройки выпадающего списка тренеров из БД."""
    field.queryset = get_ordered_trainers()
    field.label_from_instance = lambda trainer: trainer.full_name
    if empty_label is not None:
        field.empty_label = empty_label
    if required is not None:
        field.required = required
    field.widget.attrs.setdefault('class', 'form-select')


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(label="Имя", max_length=100)
    last_name = forms.CharField(label="Фамилия", max_length=100)
    patronymic = forms.CharField(label="Отчество", max_length=100, required=False)
    address = forms.CharField(label="Адрес", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=25)
    birth_date = forms.DateField(label="Дата рождения", widget=DateInput())

    class Meta:
        model = User
        fields = [
            "username", "email", "password1", "password2",
            "first_name", "last_name", "patronymic",
            "address", "phone", "birth_date",
        ]

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        try:
            validate_minimum_age(birth_date, 18)
        except ValueError:
            raise forms.ValidationError("Регистрация только для пользователей старше 18 лет.")
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        try:
            return format_belarus_phone(phone)
        except ValueError as exc:
            raise ValidationError(str(exc))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off',
            })
        self.fields['birth_date'].widget.format = '%Y-%m-%d'
        self.fields['patronymic'].required = False


class MembershipForm(forms.ModelForm):
    promo_code_input = forms.CharField(label="Промокод", required=False, max_length=20)

    class Meta:
        model = Membership
        fields = ['membership_type', 'start_date']
        widgets = {
            'start_date': DateInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'membership_type': 'Тип абонемента',
            'start_date': 'Дата начала',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("promo_code_input")
        membership_type = cleaned_data.get("membership_type")
        promo, err = get_valid_promocode_for_membership(code, membership_type)
        if err:
            self.add_error("promo_code_input", err)
        elif promo:
            cleaned_data["promo_code"] = promo
        return cleaned_data


class TrainingBookingForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Training.objects.none(),
        required=False,
        label="Занятие из расписания",
        empty_label="— Выберите занятие —",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date = forms.DateField(
        label="Дата тренировки",
        required=False,
        widget=DateInput(attrs={'class': 'form-control'}),
    )
    time = forms.TimeField(
        label="Время начала",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    trainer = forms.ModelChoiceField(
        queryset=Trainer.objects.none(),
        required=False,
        label="Тренер",
    )
    participants = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        required=False,
        label="Количество участников",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    notes = forms.CharField(
        required=False,
        label="Комментарий",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
    agree = forms.BooleanField(
        required=True,
        label="Согласие с правилами",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, training_type_id=None, initial_training_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        session_qs = get_available_trainings_queryset(training_type_id)
        self.fields['session'].queryset = session_qs
        self.fields['session'].label_from_instance = format_training_session_label
        if initial_training_id and session_qs.filter(pk=initial_training_id).exists():
            self.fields['session'].initial = initial_training_id
        setup_trainer_field(
            self.fields['trainer'],
            empty_label='Без предпочтений',
            required=False,
        )
        self.fields['time'].widget = forms.Select(
            choices=[
                ('', 'Выберите время'),
                *((f'{h:02d}:00', f'{h:02d}:00') for h in range(6, 22)),
            ],
            attrs={'class': 'form-select'},
        )

    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date and booking_date < date.today():
            raise ValidationError('Дата не может быть в прошлом.')
        return booking_date

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        session = cleaned_data.get('session')
        client = getattr(self, 'client', None)

        if session:
            if client and session.participants.filter(pk=client.pk).exists():
                raise ValidationError('Вы уже записаны на это занятие.')
            if session.participants.count() >= session.training_type.max_participants:
                raise ValidationError('На выбранное занятие нет свободных мест.')
            cleaned_data['training'] = session
            cleaned_data['book_personal'] = False
            return cleaned_data

        booking_date = cleaned_data.get('date')
        booking_time = cleaned_data.get('time')
        trainer = cleaned_data.get('trainer')

        if not booking_date or not booking_time:
            raise ValidationError(
                'Выберите занятие из расписания или укажите дату и время для индивидуальной записи.'
            )

        trainings = Training.objects.filter(
            is_cancelled=False,
            date=booking_date,
            time=booking_time,
        ).select_related('training_type').prefetch_related('participants')
        if trainer:
            trainings = trainings.filter(trainers=trainer)

        for training in trainings:
            if client and training.participants.filter(pk=client.pk).exists():
                raise ValidationError('Вы уже записаны на эту тренировку.')
            if training.participants.count() < training.training_type.max_participants:
                cleaned_data['training'] = training
                cleaned_data['book_personal'] = False
                return cleaned_data

        if trainings.exists():
            raise ValidationError('На выбранное время все места заняты.')

        if trainer:
            if PersonalTraining.objects.filter(
                trainer=trainer, date=booking_date, start_time=booking_time,
            ).exists():
                raise ValidationError('У выбранного тренера это время уже занято.')
            cleaned_data['book_personal'] = True
            return cleaned_data

        raise ValidationError(
            'На выбранную дату и время нет групповых тренировок. '
            'Выберите тренера для записи на индивидуальное занятие.'
        )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['trainer', 'rating', 'text']
        labels = {
            'trainer': 'Тренер (необязательно)',
            'rating': 'Оценка',
            'text': 'Текст отзыва',
        }
        widgets = {
            'rating': forms.Select(
                choices=[(i, f"{i} звезд") for i in range(1, 6)],
                attrs={'class': 'form-select'},
            ),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setup_trainer_field(
            self.fields['trainer'],
            empty_label='Общий отзыв о зале',
            required=False,
        )


class PromocodeForm(forms.ModelForm):
    class Meta:
        model = Promocode
        fields = ['code', 'membership_type', 'discount_percent', 'valid_until', 'is_active']
        widgets = {
            'valid_until': DateInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'code': 'Код промокода',
            'membership_type': 'Тип абонемента',
            'discount_percent': 'Скидка (%)',
            'valid_until': 'Действителен до',
            'is_active': 'Активен',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['membership_type'].required = False
        self.fields['valid_until'].required = False

    def clean_discount_percent(self):
        value = self.cleaned_data['discount_percent']
        if value < 1 or value > 100:
            raise ValidationError('Скидка должна быть от 1 до 100%.')
        return value


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['training_type', 'trainers', 'hall', 'date', 'time', 'end_time']
        widgets = {
            'date': DateInput(attrs={'class': 'form-control'}),
            'time': TimeInput(attrs={'class': 'form-control'}),
            'end_time': TimeInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'training_type': 'Тип тренировки',
            'trainers': 'Тренеры',
            'hall': 'Зал',
            'date': 'Дата',
            'time': 'Время начала',
            'end_time': 'Время окончания',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['training_type'].widget.attrs.update({'class': 'form-select'})
        setup_trainer_field(self.fields['trainers'], required=True)
        self.fields['trainers'].widget.attrs.update({'multiple': 'multiple'})
        self.fields['hall'].widget.attrs.update({'class': 'form-select'})
        self.fields['end_time'].required = False


class PersonalTrainingForm(forms.ModelForm):
    class Meta:
        model = PersonalTraining
        fields = ['client', 'trainer', 'training_type', 'date', 'start_time', 'end_time', 'price', 'notes']
        widgets = {
            'date': DateInput(attrs={'class': 'form-control'}),
            'start_time': TimeInput(attrs={'class': 'form-control'}),
            'end_time': TimeInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, locked_trainer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].widget.attrs.update({'class': 'form-select'})
        setup_trainer_field(self.fields['trainer'], required=True)
        self.fields['training_type'].widget.attrs.update({'class': 'form-select'})
        if locked_trainer is not None:
            self.fields['trainer'].queryset = Trainer.objects.filter(pk=locked_trainer.pk)
            self.fields['trainer'].initial = locked_trainer.pk
            self.fields['trainer'].widget = forms.HiddenInput()


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = [
            'first_name', 'last_name', 'specialization', 'experience_years',
            'phone', 'email', 'bio', 'birth_date',
        ]
        widgets = {
            'birth_date': DateInput(attrs={'class': 'form-control'}),
        }

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        try:
            validate_minimum_age(birth_date, 18)
        except ValueError:
            raise forms.ValidationError("Тренеры должны быть старше 18 лет.")
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        try:
            return format_belarus_phone(phone)
        except ValueError as exc:
            raise ValidationError(str(exc))


# ==========================================================================
# ЛР1: оформление заказа и форма обратной связи
# ==========================================================================


class CheckoutForm(forms.Form):
    """
    Форма страницы оплаты. Демонстрирует разные типы элементов управления
    и двойную валидацию — атрибутами HTML и методами clean_*() на сервере.
    """

    PAYMENT_CHOICES = [
        ('card', 'Банковская карта'),
        ('erip', 'ЕРИП «Расчёт»'),
        ('cash', 'Наличными на ресепшене'),
    ]

    full_name = forms.CharField(
        label="ФИО плательщика", min_length=5, max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Иванов Иван Иванович',
            'autocomplete': 'name', 'minlength': 5, 'maxlength': 150, 'required': True,
        }),
    )
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'name@example.by',
            'autocomplete': 'email', 'required': True,
        }),
    )
    phone = forms.CharField(
        label="Контактный телефон", max_length=20,
        widget=TelInput(attrs={
            'class': 'form-control', 'placeholder': '+375 (29) 123-45-67',
            'pattern': r'^\+?375[\s\-()]*\d{2}[\s\-()]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}$',
            'autocomplete': 'tel', 'required': True,
        }),
    )
    start_date = forms.DateField(
        label="Желаемая дата начала действия",
        widget=DateInput(attrs={'class': 'form-control', 'required': True}),
        input_formats=['%Y-%m-%d'],
        initial=date.today,
    )
    payment_method = forms.ChoiceField(
        label="Способ оплаты", choices=PAYMENT_CHOICES, initial='card',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    card_number = forms.CharField(
        label="Номер карты", required=False, max_length=23,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': '4111 1111 1111 1111',
            'inputmode': 'numeric', 'autocomplete': 'cc-number', 'maxlength': 23,
        }),
    )
    promocode = forms.CharField(
        label="Промокод", required=False, max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'FITNESS10', 'maxlength': 20,
        }),
    )
    agree = forms.BooleanField(
        label="Согласен с условиями оферты и политикой конфиденциальности",
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        try:
            return format_belarus_phone(phone)
        except ValueError as exc:
            raise ValidationError(str(exc))

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date < date.today():
            raise ValidationError("Дата начала не может быть в прошлом.")
        if start_date > date.today() + timedelta(days=180):
            raise ValidationError("Абонемент можно активировать не позднее чем через 180 дней.")
        return start_date

    def clean_full_name(self):
        full_name = self.cleaned_data['full_name'].strip()
        if len(full_name.split()) < 2:
            raise ValidationError("Укажите фамилию и имя полностью.")
        return full_name

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('payment_method') == 'card':
            digits = ''.join(ch for ch in (cleaned.get('card_number') or '') if ch.isdigit())
            if not digits:
                self.add_error('card_number', "Для оплаты картой укажите номер карты.")
            elif len(digits) not in (16, 18, 19):
                self.add_error('card_number', "Номер карты должен содержать 16–19 цифр.")
        return cleaned


class FeedbackForm(forms.Form):
    """Форма обращения на странице «Контакты»."""

    TOPIC_CHOICES = [
        ('personal', 'Персональные занятия'),
        ('membership', 'Абонементы'),
        ('vacancy', 'Вакансия'),
        ('other', 'Другой вопрос'),
    ]
    CHANNEL_CHOICES = [
        ('email', 'Электронная почта'),
        ('phone', 'Телефонный звонок'),
    ]

    full_name = forms.CharField(
        label="Как к вам обращаться", max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
    )
    email = forms.EmailField(
        label="Email для ответа",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.by'}),
    )
    phone = forms.CharField(
        label="Телефон", required=False, max_length=20,
        widget=TelInput(attrs={'class': 'form-control', 'placeholder': '+375 (29) 123-45-67'}),
    )
    topic = forms.ChoiceField(
        label="Тема обращения", choices=TOPIC_CHOICES, initial='personal',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    channels = forms.MultipleChoiceField(
        label="Удобные способы связи", choices=CHANNEL_CHOICES,
        initial=['email'], required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    attachment = forms.FileField(
        label="Прикрепить файл", required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )
    message = forms.CharField(
        label="Сообщение", min_length=10, max_length=1000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
    )
    agree = forms.BooleanField(
        label="Даю согласие на обработку персональных данных",
    )

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            return ''
        try:
            return format_belarus_phone(phone)
        except ValueError as exc:
            raise ValidationError(str(exc))
