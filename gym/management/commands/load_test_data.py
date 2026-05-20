from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from gym.models import (
    Article,
    Client,
    CompanyInfo,
    Equipment,
    FAQ,
    Hall,
    Membership,
    MembershipType,
    PersonalTraining,
    Promocode,
    Review,
    Trainer,
    Training,
    TrainingType,
    UserSessionLog,
    Vacancy,
)

RECORD_COUNT = 10

TRAINER_SPECIALIZATIONS = [
    'Силовые тренировки',
    'Йога и пилатес',
    'Кардио и функциональный тренинг',
    'Кроссфит',
    'Бокс',
    'Плавание',
    'Стретчинг',
    'TRX',
    'Питание и wellness',
    'Реабилитация',
]

MEMBERSHIP_NAMES = [
    'Базовый', 'Стандарт', 'Премиум', 'VIP', 'Студент',
    'Семейный', 'Утренний', 'Вечерний', 'Годовой', 'Пробный',
]

TRAINING_TYPE_NAMES = [
    'Силовая тренировка', 'Йога для начинающих', 'HIIT тренировка',
    'Пилатес', 'Кроссфит', 'Стретчинг', 'Бокс', 'Танцы',
    'Аквааэробика', 'TRX',
]

TRAINING_CATEGORIES = ['cardio', 'strength', 'yoga', 'group', 'functional']
DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']
EQUIPMENT_CONDITIONS = ['excellent', 'good', 'fair', 'needs_repair']


class Command(BaseCommand):
    help = 'Загрузка тестовых данных для FitLife Gym (по 10 записей в каждую таблицу)'

    def handle(self, *args, **kwargs):
        self.stdout.write(f'Загрузка тестовых данных ({RECORD_COUNT} записей на таблицу)...')

        admin_user = self._ensure_admin_user()
        self._load_company_info()
        trainers = self._load_trainers()
        membership_types = self._load_membership_types()
        training_types = self._load_training_types()
        halls = self._load_halls()
        self._load_equipment(halls)
        self._load_faq()
        clients = self._load_clients()
        promocodes = self._load_promocodes(membership_types, admin_user)
        self._load_memberships(clients, membership_types, promocodes)
        self._load_trainings(training_types, trainers, halls, clients)
        self._load_personal_trainings(clients, trainers, training_types)
        self._load_reviews(clients, trainers)
        self._load_articles(admin_user)
        self._load_vacancies()
        self._load_session_logs(admin_user, clients)

        self.stdout.write(self.style.SUCCESS(
            f'\n[SUCCESS] Загружено по {RECORD_COUNT} записей в каждую таблицу!'
        ))
        self._print_credentials()

    def _ensure_admin_user(self):
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@fitlifegym.by', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            user.set_password('admin')
            user.save()
        return user

    def _load_company_info(self):
        for i in range(RECORD_COUNT):
            suffix = i + 1
            CompanyInfo.objects.get_or_create(
                name=f'FitLife Gym — филиал {suffix}',
                defaults={
                    'history': f'История филиала №{suffix}. Современный фитнес-центр с 2015 года.',
                    'founding_year': 2015 + (i % 5),
                    'address': f'г. Минск, ул. Победителей, {100 + suffix}',
                    'phone': f'+375 29 {100 + suffix:03d}-45-67',
                    'email': f'branch{suffix}@fitlifegym.by',
                    'requisites': f'УНП: 12345678{suffix}\nР/с: BY12ALFA3012000000000000000{suffix}',
                },
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] CompanyInfo: {CompanyInfo.objects.count()}'))

    def _load_trainers(self):
        trainers = []
        for i in range(RECORD_COUNT):
            suffix = i + 1
            trainer, _ = Trainer.objects.get_or_create(
                email=f'trainer{suffix}@fitlifegym.by',
                defaults={
                    'first_name': ['Иван', 'Анна', 'Дмитрий', 'Елена', 'Сергей',
                                   'Ольга', 'Алексей', 'Мария', 'Павел', 'Наталья'][i],
                    'last_name': ['Петров', 'Сидорова', 'Козлов', 'Новикова', 'Морозов',
                                  'Лебедева', 'Соколов', 'Кузнецова', 'Попов', 'Волкова'][i],
                    'specialization': TRAINER_SPECIALIZATIONS[i],
                    'experience_years': 3 + i,
                    'phone': f'+375 29 {200 + suffix:03d}-11-11',
                    'bio': f'Тренер №{suffix}. {TRAINER_SPECIALIZATIONS[i]}.',
                    'birth_date': date(1985 + (i % 10), (i % 12) + 1, (i % 28) + 1),
                },
            )
            trainers.append(trainer)
        self.stdout.write(self.style.SUCCESS(f'[OK] Trainer: {len(trainers)}'))
        return trainers

    def _load_membership_types(self):
        types = []
        for i in range(RECORD_COUNT):
            mt, _ = MembershipType.objects.get_or_create(
                name=MEMBERSHIP_NAMES[i],
                defaults={
                    'duration_months': [1, 3, 6, 12, 1, 6, 3, 3, 12, 1][i],
                    'price': Decimal(str([50, 130, 240, 450, 35, 200, 90, 110, 400, 15][i])),
                    'description': f'Абонемент «{MEMBERSHIP_NAMES[i]}» — тестовое описание.',
                    'includes_trainer': i in (2, 3, 5, 8),
                    'individual_session_price': Decimal('25.00') + i * 5,
                },
            )
            types.append(mt)
        self.stdout.write(self.style.SUCCESS(f'[OK] MembershipType: {len(types)}'))
        return types

    def _load_training_types(self):
        types = []
        for i in range(RECORD_COUNT):
            tt, _ = TrainingType.objects.get_or_create(
                name=TRAINING_TYPE_NAMES[i],
                defaults={
                    'type': TRAINING_CATEGORIES[i % len(TRAINING_CATEGORIES)],
                    'description': f'Описание занятия «{TRAINING_TYPE_NAMES[i]}».',
                    'duration_minutes': [45, 60, 90, 55, 50, 45, 60, 55, 50, 50][i],
                    'max_participants': 8 + (i % 8),
                    'difficulty_level': DIFFICULTY_LEVELS[i % len(DIFFICULTY_LEVELS)],
                },
            )
            types.append(tt)
        self.stdout.write(self.style.SUCCESS(f'[OK] TrainingType: {len(types)}'))
        return types

    def _load_halls(self):
        halls = []
        hall_names = [
            'Тренажерный зал', 'Зал групповых занятий', 'Зал функционального тренинга',
            'Зал йоги', 'Зал бокса', 'Кардио-зона', 'Зал пилатеса', 'Бассейн',
            'Студия танцев', 'VIP-зал',
        ]
        for i in range(RECORD_COUNT):
            hall, _ = Hall.objects.get_or_create(
                name=hall_names[i],
                defaults={
                    'area': 100 + i * 25,
                    'capacity': 15 + i * 3,
                    'description': f'Описание зала «{hall_names[i]}».',
                },
            )
            halls.append(hall)
        self.stdout.write(self.style.SUCCESS(f'[OK] Hall: {len(halls)}'))
        return halls

    def _load_equipment(self, halls):
        equipment_names = [
            'Беговая дорожка', 'Силовая рама', 'Гантели', 'Велотренажер',
            'Эллиптический тренажер', 'Скамья для жима', 'Штанга олимпийская',
            'Коврик для йоги', 'Гири', 'Боксёрская груша',
        ]
        for i in range(RECORD_COUNT):
            Equipment.objects.get_or_create(
                name=equipment_names[i],
                defaults={
                    'description': f'Описание: {equipment_names[i]}.',
                    'quantity': 5 + i,
                    'condition': EQUIPMENT_CONDITIONS[i % len(EQUIPMENT_CONDITIONS)],
                    'purchase_date': date(2022, 1, 1) + timedelta(days=i * 30),
                    'hall': halls[i % len(halls)],
                },
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] Equipment: {Equipment.objects.count()}'))

    def _load_faq(self):
        questions = [
            'Какой абонемент выбрать новичку?',
            'Нужна ли справка от врача?',
            'Можно ли заморозить абонемент?',
            'Есть ли пробное занятие?',
            'Как записаться на групповое занятие?',
            'Работает ли зал в праздники?',
            'Есть ли парковка?',
            'Можно ли привести друга?',
            'Как отменить персональную тренировку?',
            'Предоставляете ли полотенца?',
        ]
        for i in range(RECORD_COUNT):
            FAQ.objects.get_or_create(
                question=questions[i],
                defaults={'answer': f'Ответ на вопрос: {questions[i]} (тестовые данные).'},
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] FAQ: {FAQ.objects.count()}'))

    def _load_clients(self):
        clients = []
        first_names = ['Алексей', 'Мария', 'Дмитрий', 'Елена', 'Андрей',
                       'Ольга', 'Игорь', 'Светлана', 'Николай', 'Татьяна']
        last_names = ['Иванов', 'Смирнова', 'Кузнецов', 'Волкова', 'Морозов',
                      'Новикова', 'Соколов', 'Лебедева', 'Козлов', 'Попова']
        patronymics = ['Сергеевич', 'Александровна', 'Владимирович', 'Игоревна', 'Петрович',
                       'Андреевна', 'Николаевич', 'Дмитриевна', 'Олегович', 'Викторовна']
        for i in range(RECORD_COUNT):
            suffix = i + 1
            username = f'client{suffix}'
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'client{suffix}@example.com'},
            )
            if user_created:
                user.set_password('client123')
                user.save()
            client, _ = Client.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': first_names[i],
                    'last_name': last_names[i],
                    'patronymic': patronymics[i],
                    'address': f'г. Минск, ул. Тестовая, {suffix}',
                    'phone': f'+375 29 {300 + suffix:03d}-44-44',
                    'birth_date': date(1987 + (i % 12), (i % 12) + 1, (i % 25) + 1),
                },
            )
            clients.append(client)
        self.stdout.write(self.style.SUCCESS(f'[OK] Client: {len(clients)}'))
        return clients

    def _load_promocodes(self, membership_types, admin_user):
        promocodes = []
        for i in range(RECORD_COUNT):
            code = f'PROMO{i + 1:02d}'
            promo, _ = Promocode.objects.get_or_create(
                code=code,
                defaults={
                    'discount_percent': 5 + i * 5,
                    'membership_type': membership_types[i % len(membership_types)] if i % 3 else None,
                    'created_by': admin_user,
                    'is_active': i < 8,
                    'valid_until': date.today() + timedelta(days=30 + i * 10),
                },
            )
            promocodes.append(promo)
        self.stdout.write(self.style.SUCCESS(f'[OK] Promocode: {len(promocodes)}'))
        return promocodes

    def _load_memberships(self, clients, membership_types, promocodes):
        for i in range(RECORD_COUNT):
            mt = membership_types[i % len(membership_types)]
            start = date.today() - timedelta(days=10 + i * 5)
            end = start + timedelta(days=mt.duration_months * 30)
            Membership.objects.get_or_create(
                client=clients[i],
                membership_type=mt,
                start_date=start,
                defaults={
                    'end_date': end,
                    'is_active': i < 8,
                    'price_paid': mt.price * Decimal('0.9'),
                    'promocode': promocodes[i] if i % 2 == 0 else None,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] Membership: {Membership.objects.count()}'))

    def _load_trainings(self, training_types, trainers, halls, clients):
        for i in range(RECORD_COUNT):
            training, created = Training.objects.get_or_create(
                training_type=training_types[i % len(training_types)],
                hall=halls[i % len(halls)],
                date=date.today() + timedelta(days=i + 1),
                time=time(9 + (i % 10), 0),
                defaults={'is_cancelled': i == 9},
            )
            if created:
                training.trainers.set([trainers[i % len(trainers)]])
                training.participants.set(clients[(i % 3):(i % 3) + 2] or clients[:1])
        self.stdout.write(self.style.SUCCESS(f'[OK] Training: {Training.objects.count()}'))

    def _load_personal_trainings(self, clients, trainers, training_types):
        for i in range(RECORD_COUNT):
            start = time(10 + (i % 6), 0)
            end = time(11 + (i % 6), 0)
            PersonalTraining.objects.get_or_create(
                client=clients[i],
                trainer=trainers[i % len(trainers)],
                date=date.today() + timedelta(days=i + 2),
                start_time=start,
                defaults={
                    'training_type': training_types[i % len(training_types)],
                    'end_time': end,
                    'price': Decimal('35.00') + i * 5,
                    'notes': f'Индивидуальное занятие №{i + 1}.',
                },
            )
        self.stdout.write(self.style.SUCCESS(
            f'[OK] PersonalTraining: {PersonalTraining.objects.count()}'
        ))

    def _load_reviews(self, clients, trainers):
        for i in range(RECORD_COUNT):
            Review.objects.get_or_create(
                client=clients[i],
                trainer=trainers[i % len(trainers)] if i % 4 else None,
                defaults={
                    'rating': (i % 5) + 1,
                    'text': f'Тестовый отзыв №{i + 1}. {"Отличный тренер!" if i % 4 else "Хороший зал."}',
                },
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] Review: {Review.objects.count()}'))

    def _load_articles(self, admin_user):
        for i in range(RECORD_COUNT):
            Article.objects.get_or_create(
                title=f'Новость FitLife №{i + 1}',
                defaults={
                    'short_description': f'Краткое описание новости №{i + 1}.',
                    'content': f'Полный текст новости №{i + 1}. Тестовые данные для демонстрации.',
                    'published_at': timezone.now() - timedelta(days=i),
                    'author': admin_user,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] Article: {Article.objects.count()}'))

    def _load_vacancies(self):
        titles = [
            'Тренер по фитнесу', 'Администратор', 'Менеджер по продажам',
            'Инструктор групповых программ', 'Уборщик', 'Массажист',
            'Тренер по йоге', 'Охранник', 'Бариста', 'Системный администратор',
        ]
        for i in range(RECORD_COUNT):
            Vacancy.objects.get_or_create(
                title=titles[i],
                defaults={
                    'description': f'Описание вакансии «{titles[i]}».',
                    'requirements': f'- Опыт от {1 + i % 3} лет\n- Ответственность\n- Коммуникабельность',
                    'salary': Decimal(str(500 + i * 50)),
                    'is_active': i < 7,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'[OK] Vacancy: {Vacancy.objects.count()}'))

    def _load_session_logs(self, admin_user, clients):
        users = [admin_user] + [c.user for c in clients[:RECORD_COUNT - 1]]
        for i in range(RECORD_COUNT):
            user = users[i % len(users)]
            login_time = timezone.now() - timedelta(hours=RECORD_COUNT - i)
            UserSessionLog.objects.get_or_create(
                user=user,
                session_key=f'test_session_{i + 1:02d}',
                login_time=login_time,
                defaults={
                    'logout_time': login_time + timedelta(minutes=30 + i * 5)
                    if i % 2 == 0 else None,
                },
            )
        self.stdout.write(self.style.SUCCESS(
            f'[OK] UserSessionLog: {UserSessionLog.objects.count()}'
        ))

    def _print_credentials(self):
        self.stdout.write(self.style.WARNING('\nДля входа в админ-панель:'))
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin')
        self.stdout.write(self.style.WARNING('\nДля входа как клиент:'))
        self.stdout.write('Username: client1 … client10')
        self.stdout.write('Password: client123')
