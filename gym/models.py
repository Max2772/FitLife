~from datetime import datetime, timedelta
from decimal import Decimal

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
    slogan = models.CharField(max_length=200, blank=True, verbose_name="Слоган")
    video = models.FileField(
        upload_to='company_videos/', blank=True, null=True,
        verbose_name="Промо-видео", help_text="MP4-файл видеоэкскурсии по клубу"
    )
    video_poster = models.ImageField(
        upload_to='company_videos/', blank=True, null=True, verbose_name="Постер видео"
    )

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

    @property
    def full_name(self):
        name = f"{self.last_name} {self.first_name}".strip()
        if name:
            return name
        if self.user_id:
            user_name = self.user.get_full_name()
            return user_name.strip() or self.user.username
        return ""

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
    individual_session_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=30.00,
        verbose_name="Цена индивидуального занятия"
    )
    image = models.ImageField(
        upload_to='membership_images/', blank=True, null=True, verbose_name="Изображение"
    )
    short_description = models.CharField(
        max_length=255, blank=True, verbose_name="Краткое описание для каталога"
    )

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
    price_paid = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Оплаченная сумма"
    )
    promocode = models.ForeignKey(
        'Promocode', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Промокод"
    )

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
    time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания", null=True, blank=True)
    participants = models.ManyToManyField(Client, blank=True, related_name='trainings', verbose_name="Участники")
    is_cancelled = models.BooleanField(default=False, verbose_name="Отменена")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.end_time and self.time and self.training_type_id:
            start_time = self.time
            if isinstance(start_time, str):
                h, m = map(int, start_time.split(':')[:2])
                from datetime import time as dt_time
                start_time = dt_time(h, m)
            start_dt = datetime.combine(self.date, start_time)
            end_dt = start_dt + timedelta(minutes=self.training_type.duration_minutes)
            self.end_time = end_dt.time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.training_type} - {self.date} {self.time}"

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"
        ordering = ['date', 'time']


class PersonalTraining(models.Model):
    """Индивидуальное занятие между клиентом и инструктором."""
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='personal_trainings', verbose_name="Клиент"
    )
    trainer = models.ForeignKey(
        Trainer, on_delete=models.CASCADE, related_name='personal_trainings', verbose_name="Инструктор"
    )
    training_type = models.ForeignKey(
        TrainingType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Вид занятия"
    )
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} — {self.trainer} ({self.date})"

    class Meta:
        verbose_name = "Индивидуальное занятие"
        verbose_name_plural = "Индивидуальные занятия"
        ordering = ['-date', '-start_time']


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
        if not self.logout_time:
            return None
        minutes = (self.logout_time - self.login_time).total_seconds() / 60
        if minutes < 0:
            return None
        return minutes

    def __str__(self):
        return f"{self.user.username} — {self.login_time.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Лог сессии"
        verbose_name_plural = "Логи сессий"


# ============================================================================
# ЛР1 (СТРВП): партнёры, история компании, сертификаты, сотрудники,
#              корзина заказа и оплата абонементов.
# ============================================================================


class Partner(models.Model):
    """Компания-партнёр клуба. Выводится блоком логотипов на главной странице."""

    class PartnerCategory(models.TextChoices):
        NUTRITION = 'nutrition', 'Спортивное питание'
        EQUIPMENT = 'equipment', 'Экипировка и инвентарь'
        MEDICINE = 'medicine', 'Медицина и восстановление'
        TECH = 'tech', 'Технологии и сервисы'

    name = models.CharField(max_length=120, verbose_name="Название")
    description = models.CharField(max_length=255, verbose_name="Краткое описание")
    category = models.CharField(
        max_length=20, choices=PartnerCategory.choices,
        default=PartnerCategory.NUTRITION, verbose_name="Категория"
    )
    website = models.URLField(verbose_name="Сайт компании")
    logo = models.ImageField(upload_to='partner_logos/', blank=True, null=True, verbose_name="Логотип")
    since_year = models.PositiveIntegerField(verbose_name="Сотрудничаем с")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок вывода")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Партнёр"
        verbose_name_plural = "Партнёры"
        ordering = ['sort_order', 'name']


class CompanyMilestone(models.Model):
    """Одно событие в истории компании — для таймлайна «история по годам»."""

    company = models.ForeignKey(
        CompanyInfo, on_delete=models.CASCADE, related_name='milestones', verbose_name="Компания"
    )
    year = models.PositiveIntegerField(verbose_name="Год")
    title = models.CharField(max_length=200, verbose_name="Событие")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return f"{self.year} — {self.title}"

    class Meta:
        verbose_name = "Событие истории"
        verbose_name_plural = "История компании"
        ordering = ['year']


class Certificate(models.Model):
    """Сертификат/лицензия компании (по условию — текстом, без оформления стилями)."""

    company = models.ForeignKey(
        CompanyInfo, on_delete=models.CASCADE, related_name='certificates', verbose_name="Компания"
    )
    title = models.CharField(max_length=200, verbose_name="Наименование")
    number = models.CharField(max_length=100, verbose_name="Регистрационный номер")
    issued_by = models.CharField(max_length=255, verbose_name="Кем выдан")
    issue_date = models.DateField(verbose_name="Дата выдачи")
    valid_until = models.DateField(verbose_name="Действителен до")
    description = models.TextField(verbose_name="Содержание", blank=True)
    document = models.FileField(
        upload_to='certificates/', blank=True, null=True, verbose_name="Файл документа"
    )

    def __str__(self):
        return f"{self.title} № {self.number}"

    class Meta:
        verbose_name = "Сертификат"
        verbose_name_plural = "Сертификаты"
        ordering = ['-issue_date']


class Employee(models.Model):
    """Сотрудник клуба для страницы «Контакты»."""

    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    position = models.CharField(max_length=120, verbose_name="Должность")
    duties = models.TextField(verbose_name="Выполняемые работы")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True, verbose_name="Фото")
    office = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")
    work_hours = models.CharField(max_length=100, default="Пн–Пт 09:00–18:00", verbose_name="Часы приёма")
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок вывода")

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}".strip()

    def __str__(self):
        return f"{self.full_name} — {self.position}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['sort_order', 'last_name']


class Cart(models.Model):
    """Корзина заказа. Привязана к пользователю либо к ключу анонимной сессии."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name='cart', verbose_name="Пользователь"
    )
    session_key = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="Ключ сессии")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.all()), Decimal('0.00'))

    def __str__(self):
        owner = self.user.username if self.user_id else f"сессия {self.session_key[:8]}"
        return f"Корзина ({owner})"

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class CartItem(models.Model):
    """Позиция корзины: тип абонемента и его количество."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Корзина")
    membership_type = models.ForeignKey(
        MembershipType, on_delete=models.CASCADE, verbose_name="Абонемент"
    )
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Количество")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлен")

    @property
    def subtotal(self):
        return self.membership_type.price * self.quantity

    def __str__(self):
        return f"{self.membership_type} × {self.quantity}"

    class Meta:
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"
        unique_together = ('cart', 'membership_type')
        ordering = ['added_at']


class Order(models.Model):
    """Оформленный и оплаченный заказ."""

    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Банковская карта'
        ERIP = 'erip', 'ЕРИП «Расчёт»'
        CASH = 'cash', 'Наличными на ресепшене'

    class Status(models.TextChoices):
        NEW = 'new', 'Ожидает оплаты'
        PAID = 'paid', 'Оплачен'
        CANCELLED = 'cancelled', 'Отменён'

    number = models.CharField(max_length=20, unique=True, verbose_name="Номер заказа")
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name="Пользователь"
    )
    full_name = models.CharField(max_length=150, verbose_name="ФИО плательщика")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices,
        default=PaymentMethod.CARD, verbose_name="Способ оплаты"
    )
    promocode = models.ForeignKey(
        Promocode, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Промокод"
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма без скидки")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Скидка")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого к оплате")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.NEW, verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата оформления")

    def __str__(self):
        return f"Заказ {self.number} на {self.total} BYN"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Позиция заказа — фиксирует цену на момент оплаты."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    membership_type = models.ForeignKey(
        MembershipType, on_delete=models.SET_NULL, null=True, verbose_name="Абонемент"
    )
    title = models.CharField(max_length=150, verbose_name="Наименование")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Количество")

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.title} × {self.quantity}"

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
