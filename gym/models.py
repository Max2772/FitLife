from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class CompanyInfo(models.Model):
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    name = models.CharField(max_length=200, default='FitLife Gym')
    history = models.TextField()
    founding_year = models.PositiveIntegerField()
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    requisites = models.TextField(help_text="Реквизиты компании")

    def __str__(self):
        return f"{self.name} (с {self.founding_year} г.)"

    class Meta:
        verbose_name = "Информация о компании"
        verbose_name_plural = "Информация о компании"


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    specialization = models.CharField(max_length=100, verbose_name="Специализация")
    experience_years = models.PositiveIntegerField(verbose_name="Опыт работы (лет)")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    photo = models.ImageField(upload_to='trainer_photos/', blank=True, null=True, verbose_name="Фото")
    bio = models.TextField(verbose_name="Биография", blank=True)
    birth_date = models.DateField(verbose_name="Дата рождения")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.specialization})"

    class Meta:
        verbose_name = "Тренер"
        verbose_name_plural = "Тренеры"


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отчество")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    birth_date = models.DateField(verbose_name="Дата рождения")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class MembershipType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    duration_months = models.PositiveIntegerField(verbose_name="Длительность (месяцев)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(verbose_name="Описание")
    includes_trainer = models.BooleanField(default=False, verbose_name="Включает персонального тренера")

    def __str__(self):
        return f"{self.name} ({self.duration_months} мес.)"

    class Meta:
        verbose_name = "Тип абонемента"
        verbose_name_plural = "Типы абонементов"


class Membership(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    membership_type = models.ForeignKey(MembershipType, on_delete=models.CASCADE, verbose_name="Тип абонемента")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")

    def __str__(self):
        return f"Абонемент {self.client} - {self.membership_type}"

    class Meta:
        verbose_name = "Абонемент"
        verbose_name_plural = "Абонементы"


class TrainingType(models.Model):

    class TrainingCategory(models.TextChoices):
        CARDIO = 'cardio', 'Кардио'
        STRENGTH = 'strength', 'Силовая'
        YOGA = 'yoga', 'Йога'
        GROUP = 'group', 'Групповая'
        FUNCTIONAL = 'functional', 'Функциональная'

    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Начинающий'
        INTERMEDIATE = 'intermediate', 'Средний'
        ADVANCED = 'advanced', 'Продвинутый'


    name = models.CharField(max_length=100, verbose_name="Название")
    type = models.CharField(max_length=20, choices=TrainingCategory.choices, default='group', verbose_name="Тип")
    description = models.TextField(verbose_name="Описание")
    duration_minutes = models.PositiveIntegerField(verbose_name="Длительность (минут)")
    max_participants = models.PositiveIntegerField(verbose_name="Максимум участников")
    difficulty_level = models.CharField(max_length=50, choices=DifficultyLevel.choices, verbose_name="Уровень сложности")
    image = models.ImageField(upload_to='training_images/', blank=True, null=True, verbose_name="Изображение")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип тренировки"
        verbose_name_plural = "Типы тренировок"


class Hall(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    area = models.PositiveIntegerField(verbose_name="Площадь (кв.м)")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (человек)")
    description = models.TextField(verbose_name="Описание", blank=True)
    image = models.ImageField(upload_to='hall_images/', blank=True, null=True, verbose_name="Изображение")

    def __str__(self):
        return f"{self.name} ({self.capacity} чел.)"

    class Meta:
        verbose_name = "Зал"
        verbose_name_plural = "Залы"


class Training(models.Model):
    training_type = models.ForeignKey(TrainingType, on_delete=models.CASCADE, verbose_name="Тип тренировки")
    trainers = models.ManyToManyField(Trainer, related_name='trainings', verbose_name="Тренеры")
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Зал")
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(verbose_name="Время")
    participants = models.ManyToManyField(Client, blank=True, related_name='trainings', verbose_name="Участники")
    is_cancelled = models.BooleanField(default=False, verbose_name="Отменена")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.training_type} - {self.date} {self.time}"

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"
        ordering = ['date', 'time']


class Equipment(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    condition = models.CharField(max_length=50, choices=[
        ('excellent', 'Отличное'),
        ('good', 'Хорошее'),
        ('fair', 'Удовлетворительное'),
        ('needs_repair', 'Требует ремонта')
    ], verbose_name="Состояние")
    purchase_date = models.DateField(verbose_name="Дата покупки")
    hall = models.ForeignKey(Hall, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='equipment', verbose_name="Зал")
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True, verbose_name="Изображение")

    def __str__(self):
        return f"{self.name} ({self.quantity} шт.)"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"


class Review(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Тренер")
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Оценка")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Отзыв от {self.client} - {self.rating}/5"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']


class Promocode(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Код")
    discount_percent = models.PositiveSmallIntegerField(verbose_name="Скидка (%)")
    membership_type = models.ForeignKey(MembershipType, on_delete=models.CASCADE, null=True, blank=True,
                                       verbose_name="Тип абонемента")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Создал")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Действителен до")

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"


class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Вопрос-Ответ"
        verbose_name_plural = "Вопросы-Ответы"


class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    short_description = models.CharField(max_length=255, verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Содержание")
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name="Изображение")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="Дата публикации")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Автор")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-published_at']


class Vacancy(models.Model):
    title = models.CharField(max_length=200, verbose_name="Должность")
    description = models.TextField(verbose_name="Описание")
    requirements = models.TextField(verbose_name="Требования")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-created_at']


class UserSessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def duration_minutes(self):
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds() / 60
        return None

    def __str__(self):
        return f"{self.user.username} — {self.login_time.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Лог сессии"
        verbose_name_plural = "Логи сессий"
