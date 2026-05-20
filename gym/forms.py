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
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))

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
        self.fields['birth_date'].widget.attrs.update({'type': 'date'})
        self.fields['patronymic'].required = False


class MembershipForm(forms.ModelForm):
    promo_code_input = forms.CharField(label="Промокод", required=False, max_length=20)

    class Meta:
        model = Membership
        fields = ['membership_type', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
            'valid_until': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['training_type', 'trainers', 'hall', 'date', 'time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
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
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
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
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
