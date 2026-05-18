from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import (
    Client, Trainer, Membership, MembershipType, Training,
    Review, Promocode, PersonalTraining,
)
from .utils import calculate_age, format_belarus_phone, validate_minimum_age


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
        if code:
            try:
                promo = Promocode.objects.get(
                    code__iexact=code.strip(),
                    is_active=True,
                )
                if promo.membership_type and promo.membership_type != membership_type:
                    raise forms.ValidationError("Промокод не подходит к выбранному абонементу.")
                if promo.valid_until and promo.valid_until < date.today():
                    raise forms.ValidationError("Промокод истек.")
                cleaned_data["promo_code"] = promo
            except Promocode.DoesNotExist:
                raise forms.ValidationError("Неверный или неактивный промокод.")
        return cleaned_data


class TrainingBookingForm(forms.Form):
    training = forms.ModelChoiceField(
        queryset=Training.objects.filter(is_cancelled=False),
        label="Выберите тренировку",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['training'].queryset = Training.objects.filter(
            is_cancelled=False,
            date__gte=date.today(),
        ).order_by('date', 'time')


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
        self.fields['trainer'].widget.attrs.update({'class': 'form-select'})
        self.fields['trainer'].required = False


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
        self.fields['trainers'].widget.attrs.update({'class': 'form-select', 'multiple': 'multiple'})
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('client', 'trainer', 'training_type'):
            self.fields[name].widget.attrs.update({'class': 'form-select'})


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
