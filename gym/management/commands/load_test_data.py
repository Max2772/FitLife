from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gym.models import (
    CompanyInfo, Trainer, Client, MembershipType, Membership, TrainingType,
    Equipment, FAQ, Article, Vacancy, Hall, Training, Review, Promocode
)
from datetime import date, timedelta, time
from django.utils import timezone


class Command(BaseCommand):
    help = 'Загрузка тестовых данных для FitLife Gym'

    def handle(self, *args, **kwargs):
        self.stdout.write('Загрузка тестовых данных...')

        # Информация о компании
        if not CompanyInfo.objects.exists():
            CompanyInfo.objects.create(
                name='FitLife Gym',
                history='FitLife Gym - это современный фитнес-центр, основанный в 2015 году. '
                        'Мы предлагаем широкий спектр услуг для достижения ваших фитнес-целей.',
                founding_year=2015,
                address='г. Минск, ул. Победителей, 123',
                phone='+375 29 123-45-67',
                email='info@fitlifegym.by',
                requisites='УНП: 123456789\nР/с: BY12ALFA30120000000000000000\nБанк: ЗАО "Альфа-Банк"'
            )
            self.stdout.write(self.style.SUCCESS('[OK] Информация о компании создана'))

        # Тренеры
        if not Trainer.objects.exists():
            trainers_data = [
                {
                    'first_name': 'Иван',
                    'last_name': 'Петров',
                    'specialization': 'Силовые тренировки',
                    'experience_years': 8,
                    'phone': '+375 29 111-11-11',
                    'email': 'petrov@fitlifegym.by',
                    'bio': 'Мастер спорта по тяжелой атлетике. Специализируюсь на силовых тренировках и бодибилдинге.',
                    'birth_date': date(1990, 5, 15)
                },
                {
                    'first_name': 'Анна',
                    'last_name': 'Сидорова',
                    'specialization': 'Йога и пилатес',
                    'experience_years': 5,
                    'phone': '+375 29 222-22-22',
                    'email': 'sidorova@fitlifegym.by',
                    'bio': 'Сертифицированный инструктор по йоге и пилатесу. Помогу вам обрести гибкость и гармонию.',
                    'birth_date': date(1992, 8, 20)
                },
                {
                    'first_name': 'Дмитрий',
                    'last_name': 'Козлов',
                    'specialization': 'Кардио и функциональный тренинг',
                    'experience_years': 6,
                    'phone': '+375 29 333-33-33',
                    'email': 'kozlov@fitlifegym.by',
                    'bio': 'Специалист по кардио-тренировкам и функциональному тренингу. Помогу вам сжечь калории!',
                    'birth_date': date(1988, 3, 10)
                }
            ]
            for data in trainers_data:
                Trainer.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Тренеры созданы'))

        # Типы абонементов
        if not MembershipType.objects.exists():
            memberships_data = [
                {
                    'name': 'Базовый',
                    'duration_months': 1,
                    'price': 50.00,
                    'description': 'Доступ в тренажерный зал в любое время',
                    'includes_trainer': False
                },
                {
                    'name': 'Стандарт',
                    'duration_months': 3,
                    'price': 130.00,
                    'description': 'Доступ в тренажерный зал + групповые занятия',
                    'includes_trainer': False
                },
                {
                    'name': 'Премиум',
                    'duration_months': 6,
                    'price': 240.00,
                    'description': 'Полный доступ + 4 персональные тренировки в месяц',
                    'includes_trainer': True
                },
                {
                    'name': 'VIP',
                    'duration_months': 12,
                    'price': 450.00,
                    'description': 'Безлимитный доступ + персональный тренер + массаж',
                    'includes_trainer': True
                }
            ]
            for data in memberships_data:
                MembershipType.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Типы абонементов созданы'))

        # Типы тренировок
        if not TrainingType.objects.exists():
            trainings_data = [
                {
                    'name': 'Силовая тренировка',
                    'description': 'Тренировка с отягощениями для развития силы и мышечной массы',
                    'duration_minutes': 60,
                    'max_participants': 10,
                    'difficulty_level': 'intermediate'
                },
                {
                    'name': 'Йога для начинающих',
                    'description': 'Базовые асаны и дыхательные практики',
                    'duration_minutes': 90,
                    'max_participants': 15,
                    'difficulty_level': 'beginner'
                },
                {
                    'name': 'HIIT тренировка',
                    'description': 'Высокоинтенсивная интервальная тренировка для сжигания жира',
                    'duration_minutes': 45,
                    'max_participants': 12,
                    'difficulty_level': 'advanced'
                },
                {
                    'name': 'Пилатес',
                    'description': 'Упражнения для укрепления мышц кора и улучшения осанки',
                    'duration_minutes': 60,
                    'max_participants': 12,
                    'difficulty_level': 'beginner'
                },
                {
                    'name': 'Кроссфит',
                    'description': 'Функциональный тренинг высокой интенсивности',
                    'duration_minutes': 60,
                    'max_participants': 8,
                    'difficulty_level': 'advanced'
                }
            ]
            for data in trainings_data:
                TrainingType.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Типы тренировок созданы'))

        # Оборудование
        if not Equipment.objects.exists():
            equipment_data = [
                {
                    'name': 'Беговая дорожка',
                    'description': 'Профессиональная беговая дорожка с регулировкой наклона',
                    'quantity': 10,
                    'condition': 'excellent',
                    'purchase_date': date(2023, 1, 15)
                },
                {
                    'name': 'Силовая рама',
                    'description': 'Многофункциональная силовая рама для приседаний и жимов',
                    'quantity': 5,
                    'condition': 'good',
                    'purchase_date': date(2022, 6, 10)
                },
                {
                    'name': 'Гантели',
                    'description': 'Набор гантелей от 2 до 50 кг',
                    'quantity': 50,
                    'condition': 'excellent',
                    'purchase_date': date(2023, 3, 20)
                },
                {
                    'name': 'Велотренажер',
                    'description': 'Велотренажер с программами тренировок',
                    'quantity': 8,
                    'condition': 'good',
                    'purchase_date': date(2022, 9, 5)
                }
            ]
            for data in equipment_data:
                Equipment.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Оборудование создано'))

        # FAQ
        if not FAQ.objects.exists():
            faq_data = [
                {
                    'question': 'Какой абонемент выбрать новичку?',
                    'answer': 'Для начинающих рекомендуем абонемент "Базовый" на 1 месяц. '
                             'Это позволит вам попробовать тренажерный зал и понять, подходит ли он вам.'
                },
                {
                    'question': 'Нужна ли справка от врача?',
                    'answer': 'Справка от врача не обязательна, но мы рекомендуем проконсультироваться '
                             'с врачом перед началом интенсивных тренировок.'
                },
                {
                    'question': 'Можно ли заморозить абонемент?',
                    'answer': 'Да, вы можете заморозить абонемент на срок до 14 дней при наличии '
                             'уважительной причины (болезнь, командировка).'
                },
                {
                    'question': 'Есть ли пробное занятие?',
                    'answer': 'Да, мы предлагаем бесплатное пробное занятие для всех новых клиентов. '
                             'Запишитесь по телефону или через сайт.'
                }
            ]
            for data in faq_data:
                FAQ.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] FAQ создан'))

        # Статьи/Новости
        if not Article.objects.exists():
            admin_user = User.objects.filter(is_superuser=True).first()
            articles_data = [
                {
                    'title': 'Открытие нового зала для групповых занятий',
                    'short_description': 'Мы рады сообщить об открытии нового просторного зала для групповых тренировок',
                    'content': 'С 1 июня в FitLife Gym открывается новый зал площадью 200 кв.м для групповых занятий. '
                              'Здесь будут проходить занятия по йоге, пилатесу, HIIT и другим направлениям. '
                              'Зал оборудован современной звуковой системой и кондиционерами.',
                    'author': admin_user
                },
                {
                    'title': '5 советов для эффективной тренировки',
                    'short_description': 'Как сделать ваши тренировки максимально эффективными',
                    'content': '1. Разминка обязательна\n2. Следите за техникой выполнения\n'
                              '3. Пейте достаточно воды\n4. Не забывайте про отдых\n5. Правильное питание',
                    'author': admin_user
                },
                {
                    'title': 'Новые тренеры в нашей команде',
                    'short_description': 'Познакомьтесь с нашими новыми специалистами',
                    'content': 'Мы рады представить двух новых тренеров, которые присоединились к команде FitLife Gym. '
                              'Они помогут вам достичь ваших фитнес-целей!',
                    'author': admin_user
                }
            ]
            for data in articles_data:
                Article.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Статьи созданы'))

        # Вакансии
        if not Vacancy.objects.exists():
            vacancies_data = [
                {
                    'title': 'Тренер по фитнесу',
                    'description': 'Ищем опытного тренера для проведения групповых и персональных тренировок',
                    'requirements': '- Опыт работы от 2 лет\n- Сертификат тренера\n- Коммуникабельность',
                    'salary': 800.00,
                    'is_active': True
                },
                {
                    'title': 'Администратор',
                    'description': 'Требуется администратор на ресепшн',
                    'requirements': '- Опыт работы с клиентами\n- Знание ПК\n- Ответственность',
                    'salary': 600.00,
                    'is_active': True
                }
            ]
            for data in vacancies_data:
                Vacancy.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Вакансии созданы'))

        # Залы
        if not Hall.objects.exists():
            halls_data = [
                {
                    'name': 'Тренажерный зал',
                    'area': 300,
                    'capacity': 50,
                    'description': 'Просторный зал с современными тренажерами для силовых и кардио тренировок'
                },
                {
                    'name': 'Зал групповых занятий',
                    'area': 200,
                    'capacity': 30,
                    'description': 'Зал для йоги, пилатеса и других групповых программ'
                },
                {
                    'name': 'Зал функционального тренинга',
                    'area': 150,
                    'capacity': 20,
                    'description': 'Зал для кроссфита и HIIT тренировок'
                }
            ]
            for data in halls_data:
                Hall.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Залы созданы'))

        # Обновляем оборудование, привязывая к залам
        if Equipment.objects.exists() and Hall.objects.exists():
            gym_hall = Hall.objects.get(name='Тренажерный зал')
            group_hall = Hall.objects.get(name='Зал групповых занятий')
            functional_hall = Hall.objects.get(name='Зал функционального тренинга')

            Equipment.objects.filter(name='Беговая дорожка').update(hall=gym_hall)
            Equipment.objects.filter(name='Силовая рама').update(hall=gym_hall)
            Equipment.objects.filter(name='Гантели').update(hall=functional_hall)
            Equipment.objects.filter(name='Велотренажер').update(hall=gym_hall)
            self.stdout.write(self.style.SUCCESS('[OK] Оборудование привязано к залам'))

        # Клиенты
        if Client.objects.count() < 5:
            clients_data = [
                {
                    'username': 'client1',
                    'email': 'client1@example.com',
                    'first_name': 'Алексей',
                    'last_name': 'Иванов',
                    'patronymic': 'Сергеевич',
                    'address': 'г. Минск, ул. Ленина, 10',
                    'phone': '+375 29 444-44-44',
                    'birth_date': date(1995, 3, 15)
                },
                {
                    'username': 'client2',
                    'email': 'client2@example.com',
                    'first_name': 'Мария',
                    'last_name': 'Смирнова',
                    'patronymic': 'Александровна',
                    'address': 'г. Минск, пр. Независимости, 25',
                    'phone': '+375 29 555-55-55',
                    'birth_date': date(1998, 7, 22)
                },
                {
                    'username': 'client3',
                    'email': 'client3@example.com',
                    'first_name': 'Дмитрий',
                    'last_name': 'Кузнецов',
                    'patronymic': 'Владимирович',
                    'address': 'г. Минск, ул. Богдановича, 5',
                    'phone': '+375 29 666-66-66',
                    'birth_date': date(1990, 11, 8)
                },
                {
                    'username': 'client4',
                    'email': 'client4@example.com',
                    'first_name': 'Елена',
                    'last_name': 'Волкова',
                    'patronymic': 'Игоревна',
                    'address': 'г. Минск, ул. Притыцкого, 15',
                    'phone': '+375 29 777-77-77',
                    'birth_date': date(1993, 5, 30)
                },
                {
                    'username': 'client5',
                    'email': 'client5@example.com',
                    'first_name': 'Андрей',
                    'last_name': 'Морозов',
                    'patronymic': 'Петрович',
                    'address': 'г. Минск, ул. Тимирязева, 20',
                    'phone': '+375 29 888-88-88',
                    'birth_date': date(1987, 9, 12)
                }
            ]
            for data in clients_data:
                username = data['username']
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=data['email'],
                        password='client123'
                    )
                    Client.objects.create(
                        user=user,
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        patronymic=data['patronymic'],
                        address=data['address'],
                        phone=data['phone'],
                        birth_date=data['birth_date']
                    )
            self.stdout.write(self.style.SUCCESS('[OK] Клиенты созданы'))

        # Абонементы
        if not Membership.objects.exists() and Client.objects.exists() and MembershipType.objects.exists():
            clients = list(Client.objects.all())
            membership_types = list(MembershipType.objects.all())

            memberships_data = [
                {
                    'client': clients[0],
                    'membership_type': membership_types[2],  # Премиум
                    'start_date': date.today() - timedelta(days=30),
                    'end_date': date.today() + timedelta(days=150),
                    'is_active': True
                },
                {
                    'client': clients[1],
                    'membership_type': membership_types[1],  # Стандарт
                    'start_date': date.today() - timedelta(days=15),
                    'end_date': date.today() + timedelta(days=75),
                    'is_active': True
                },
                {
                    'client': clients[2],
                    'membership_type': membership_types[3],  # VIP
                    'start_date': date.today() - timedelta(days=60),
                    'end_date': date.today() + timedelta(days=305),
                    'is_active': True
                },
                {
                    'client': clients[3],
                    'membership_type': membership_types[0],  # Базовый
                    'start_date': date.today() - timedelta(days=5),
                    'end_date': date.today() + timedelta(days=25),
                    'is_active': True
                },
                {
                    'client': clients[4],
                    'membership_type': membership_types[1],  # Стандарт
                    'start_date': date.today() - timedelta(days=45),
                    'end_date': date.today() + timedelta(days=45),
                    'is_active': True
                }
            ]
            for data in memberships_data:
                Membership.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Абонементы созданы'))

        # Тренировки
        if not Training.objects.exists() and TrainingType.objects.exists() and Trainer.objects.exists() and Hall.objects.exists():
            training_types = list(TrainingType.objects.all())
            trainers = list(Trainer.objects.all())
            halls = list(Hall.objects.all())
            clients = list(Client.objects.all())

            trainings_data = [
                {
                    'training_type': training_types[0],  # Силовая
                    'trainers': [trainers[0]],
                    'hall': halls[0],
                    'date': date.today() + timedelta(days=1),
                    'time': time(10, 0),
                    'participants': [clients[0], clients[2]]
                },
                {
                    'training_type': training_types[1],  # Йога
                    'trainers': [trainers[1]],
                    'hall': halls[1],
                    'date': date.today() + timedelta(days=1),
                    'time': time(18, 0),
                    'participants': [clients[1], clients[3]]
                },
                {
                    'training_type': training_types[2],  # HIIT
                    'trainers': [trainers[2]],
                    'hall': halls[2],
                    'date': date.today() + timedelta(days=2),
                    'time': time(19, 0),
                    'participants': [clients[0], clients[4]]
                },
                {
                    'training_type': training_types[3],  # Пилатес
                    'trainers': [trainers[1]],
                    'hall': halls[1],
                    'date': date.today() + timedelta(days=3),
                    'time': time(17, 0),
                    'participants': [clients[1], clients[2], clients[3]]
                },
                {
                    'training_type': training_types[4],  # Кроссфит
                    'trainers': [trainers[0], trainers[2]],
                    'hall': halls[2],
                    'date': date.today() + timedelta(days=4),
                    'time': time(20, 0),
                    'participants': [clients[0], clients[2], clients[4]]
                }
            ]
            for data in trainings_data:
                trainers_list = data.pop('trainers')
                participants_list = data.pop('participants')
                training = Training.objects.create(**data)
                training.trainers.set(trainers_list)
                training.participants.set(participants_list)
            self.stdout.write(self.style.SUCCESS('[OK] Тренировки созданы'))

        # Отзывы
        if not Review.objects.exists() and Client.objects.exists() and Trainer.objects.exists():
            clients = list(Client.objects.all())
            trainers = list(Trainer.objects.all())

            reviews_data = [
                {
                    'client': clients[0],
                    'trainer': trainers[0],
                    'rating': 5,
                    'text': 'Отличный тренер! Помог составить программу тренировок и следит за техникой выполнения упражнений.'
                },
                {
                    'client': clients[1],
                    'trainer': trainers[1],
                    'rating': 5,
                    'text': 'Анна - замечательный инструктор по йоге. После занятий чувствую себя обновленной!'
                },
                {
                    'client': clients[2],
                    'trainer': None,
                    'rating': 4,
                    'text': 'Хороший зал, современное оборудование. Единственный минус - иногда много людей в вечернее время.'
                },
                {
                    'client': clients[3],
                    'trainer': trainers[1],
                    'rating': 5,
                    'text': 'Очень довольна занятиями пилатесом. Результаты видны уже через месяц!'
                },
                {
                    'client': clients[4],
                    'trainer': trainers[2],
                    'rating': 4,
                    'text': 'Интенсивные тренировки с Дмитрием дают отличный результат. Рекомендую!'
                }
            ]
            for data in reviews_data:
                Review.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Отзывы созданы'))

        # Промокоды
        if not Promocode.objects.exists() and MembershipType.objects.exists():
            admin_user = User.objects.filter(is_superuser=True).first()
            membership_types = list(MembershipType.objects.all())

            promocodes_data = [
                {
                    'code': 'WELCOME2024',
                    'discount_percent': 15,
                    'membership_type': membership_types[0],  # Базовый
                    'created_by': admin_user,
                    'is_active': True,
                    'valid_until': date.today() + timedelta(days=90)
                },
                {
                    'code': 'SUMMER30',
                    'discount_percent': 30,
                    'membership_type': membership_types[2],  # Премиум
                    'created_by': admin_user,
                    'is_active': True,
                    'valid_until': date.today() + timedelta(days=60)
                },
                {
                    'code': 'VIP50',
                    'discount_percent': 50,
                    'membership_type': membership_types[3],  # VIP
                    'created_by': admin_user,
                    'is_active': True,
                    'valid_until': date.today() + timedelta(days=30)
                },
                {
                    'code': 'NEWYEAR',
                    'discount_percent': 20,
                    'membership_type': None,  # Для всех типов
                    'created_by': admin_user,
                    'is_active': False,
                    'valid_until': date.today() - timedelta(days=30)
                }
            ]
            for data in promocodes_data:
                Promocode.objects.create(**data)
            self.stdout.write(self.style.SUCCESS('[OK] Промокоды созданы'))

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Все тестовые данные успешно загружены!'))
        self.stdout.write(self.style.WARNING('\nДля входа в админ-панель используйте:'))
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin (установите пароль командой: python manage.py changepassword admin)')
        self.stdout.write(self.style.WARNING('\nДля входа как клиент используйте:'))
        self.stdout.write('Username: client1, client2, client3, client4, client5')
        self.stdout.write('Password: client123')
