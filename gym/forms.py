from datetime import date
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Client, Trainer, Membership, MembershipType, Training, Review, Promocode


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(label="Имя", max_length=100)
    last_name = forms.CharField(label="Фамилия", max_length=100)
    patronymic = forms.CharField(label="Отчество", max_length=100, required=False)
    address = forms.CharField(label="Адрес", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=20)
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = [
            "username", "email", "password1", "password2",
            "first_name", "last_name", "patronymic",
            "address", "phone", "birth_date"
        ]

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise forms.ValidationError("Регистрация только для пользователей старше 18 лет.")
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        cleaned_phone = re.sub(r'[^\d]', '', phone)

        if len(cleaned_phone) == 12 and cleaned_phone.startswith('375'):
            operator_code = cleaned_phone[3:5]
            if operator_code in ('29', '33', '44', '25'):
                return f"+375 {operator_code} {cleaned_phone[5:]}"

        elif len(cleaned_phone) == 9:
            operator_code = cleaned_phone[:2]
            if operator_code in ('29', '33', '44', '25'):
                return f"{operator_code} {cleaned_phone[2:]}"

        raise ValidationError(
            "Введите номер в формате: +375 29 1234567 или 29 1234567. "
            "Допустимые коды операторов: 29, 33, 44, 25."
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
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
            'start_date': 'Дата начала'
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
                    code=code,
                    membership_type=membership_type,
                    is_active=True
                )
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
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['training'].queryset = Training.objects.filter(
            is_cancelled=False,
            date__gte=date.today()
        ).order_by('date', 'time')


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['trainer', 'rating', 'text']
        labels = {
            'trainer': 'Тренер (необязательно)',
            'rating': 'Оценка',
            'text': 'Текст отзыва'
        }
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} звезд") for i in range(1, 6)], attrs={'class': 'form-select'}),
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
            'is_active': 'Активен'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membership_type'].widget.attrs.update({'class': 'form-select'})


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['training_type', 'trainers', 'hall', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'training_type': 'Тип тренировки',
            'trainers': 'Тренеры',
            'hall': 'Зал',
            'date': 'Дата',
            'time': 'Время'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['training_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['trainers'].widget.attrs.update({'class': 'form-select', 'multiple': 'multiple'})
        self.fields['hall'].widget.attrs.update({'class': 'form-select'})
