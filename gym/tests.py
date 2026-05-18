from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client as TestClient
from django.urls import reverse, resolve

from .models import (
    CompanyInfo, Trainer, Client, MembershipType, Membership,
    TrainingType, Training, Hall, Equipment, Review, Promocode,
    FAQ, Article, Vacancy, UserSessionLog
)
from .forms import RegisterForm, ReviewForm, MembershipForm


# ── Helpers ──────────────────────────────────────────────────────
class BaseTestCase(TestCase):
    """Shared setup: user, staff, trainer, client, etc."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser', password='Test1234!', email='test@test.com'
        )
        cls.staff_user = User.objects.create_user(
            username='staffuser', password='Staff1234!', is_staff=True
        )
        cls.trainer_user = User.objects.create_user(
            username='traineruser', password='Trainer1234!', is_staff=True
        )
        cls.company = CompanyInfo.objects.create(
            name='FitLife', history='Test history', founding_year=2020,
            address='Минск', phone='+375291234567', email='info@test.com',
            requisites='УНП 123'
        )
        cls.trainer = Trainer.objects.create(
            user=cls.trainer_user, first_name='Иван', last_name='Петров',
            specialization='Силовые', experience_years=5,
            phone='+375291111111', email='trainer@test.com',
            birth_date=date(1990, 1, 1)
        )
        cls.client_obj = Client.objects.create(
            user=cls.user, first_name='Тест', last_name='Клиент',
            address='ул. Тестовая', phone='+375291234567',
            birth_date=date(2000, 1, 1)
        )
        cls.membership_type = MembershipType.objects.create(
            name='Стандарт', duration_months=1, price=Decimal('100.00'),
            description='Стандартный абонемент', includes_trainer=False
        )
        cls.training_type = TrainingType.objects.create(
            name='Кардио Базовая', type='cardio', description='Описание кардио',
            duration_minutes=60, max_participants=20,
            difficulty_level='beginner'
        )
        cls.hall = Hall.objects.create(
            name='Зал 1', area=200, capacity=30, description='Основной зал'
        )
        cls.training = Training.objects.create(
            training_type=cls.training_type, hall=cls.hall,
            date=date.today() + timedelta(days=1), time='10:00'
        )
        cls.training.trainers.add(cls.trainer)
        cls.faq = FAQ.objects.create(question='Тест?', answer='Ответ')
        cls.article = Article.objects.create(
            title='Тестовая статья', short_description='Краткое',
            content='Содержание статьи', author=cls.staff_user
        )
        cls.vacancy = Vacancy.objects.create(
            title='Тренер', description='Описание',
            requirements='Требования', salary=Decimal('2000.00')
        )
        cls.equipment = Equipment.objects.create(
            name='Беговая дорожка', description='Описание', quantity=5,
            condition='excellent', purchase_date=date(2024, 1, 1), hall=cls.hall
        )
        cls.review = Review.objects.create(
            client=cls.client_obj, trainer=cls.trainer,
            rating=5, text='Отличный тренер!'
        )
        cls.promocode = Promocode.objects.create(
            code='TEST10', discount_percent=10,
            membership_type=cls.membership_type,
            created_by=cls.staff_user, is_active=True,
            valid_until=date.today() + timedelta(days=30)
        )


# ── Model Tests ──────────────────────────────────────────────────
class ModelStrTests(BaseTestCase):
    def test_company_str(self):
        self.assertIn('FitLife', str(self.company))

    def test_trainer_str(self):
        self.assertIn('Петров', str(self.trainer))

    def test_client_str(self):
        self.assertIn('Клиент', str(self.client_obj))

    def test_membership_type_str(self):
        self.assertIn('Стандарт', str(self.membership_type))

    def test_training_type_str(self):
        self.assertEqual(str(self.training_type), 'Кардио Базовая')

    def test_hall_str(self):
        self.assertIn('Зал 1', str(self.hall))

    def test_training_str(self):
        self.assertIn('Кардио Базовая', str(self.training))

    def test_equipment_str(self):
        self.assertIn('Беговая дорожка', str(self.equipment))

    def test_review_str(self):
        self.assertIn('5/5', str(self.review))

    def test_promocode_str(self):
        self.assertIn('TEST10', str(self.promocode))

    def test_faq_str(self):
        self.assertEqual(str(self.faq), 'Тест?')

    def test_article_str(self):
        self.assertEqual(str(self.article), 'Тестовая статья')

    def test_vacancy_str(self):
        self.assertEqual(str(self.vacancy), 'Тренер')

    def test_membership_str(self):
        m = Membership.objects.create(
            client=self.client_obj, membership_type=self.membership_type,
            start_date=date.today(), end_date=date.today() + timedelta(days=30)
        )
        self.assertIn('Абонемент', str(m))


class UserSessionLogTest(BaseTestCase):
    def test_duration_without_logout(self):
        log = UserSessionLog.objects.create(user=self.user, session_key='abc')
        self.assertIsNone(log.duration_minutes())

    def test_duration_with_logout(self):
        from django.utils import timezone as tz
        log = UserSessionLog.objects.create(user=self.user, session_key='abc')
        log.logout_time = log.login_time + timedelta(minutes=30)
        log.save()
        self.assertAlmostEqual(log.duration_minutes(), 30, places=0)

    def test_str(self):
        log = UserSessionLog.objects.create(user=self.user, session_key='abc')
        self.assertIn('testuser', str(log))


# ── Public Page Tests ────────────────────────────────────────────
class PublicPageTests(BaseTestCase):
    def test_main_page(self):
        resp = self.client.get(reverse('main'))
        self.assertEqual(resp.status_code, 200)

    def test_about_page(self):
        resp = self.client.get(reverse('about_company'))
        self.assertEqual(resp.status_code, 200)

    def test_contacts_page(self):
        resp = self.client.get(reverse('contacts'))
        self.assertEqual(resp.status_code, 200)

    def test_faq_page(self):
        resp = self.client.get(reverse('faq'))
        self.assertEqual(resp.status_code, 200)

    def test_news_page(self):
        resp = self.client.get(reverse('news'))
        self.assertEqual(resp.status_code, 200)

    def test_news_detail(self):
        resp = self.client.get(reverse('news_detail', args=[self.article.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_privacy_page(self):
        resp = self.client.get(reverse('privacy_policy'))
        self.assertEqual(resp.status_code, 200)

    def test_vacancies_page(self):
        resp = self.client.get(reverse('vacancies'))
        self.assertEqual(resp.status_code, 200)

    def test_trainers_page(self):
        resp = self.client.get(reverse('trainers'))
        self.assertEqual(resp.status_code, 200)

    def test_trainer_detail(self):
        resp = self.client.get(reverse('trainer_detail', args=[self.trainer.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_trainings_page(self):
        resp = self.client.get(reverse('trainings'))
        self.assertEqual(resp.status_code, 200)

    def test_trainings_filter(self):
        resp = self.client.get(reverse('trainings'), {'difficulty': 'beginner', 'type': 'cardio'})
        self.assertEqual(resp.status_code, 200)

    def test_trainings_search(self):
        resp = self.client.get(reverse('trainings'), {'q': 'Кардио'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Кардио Базовая')

    def test_trainings_sort(self):
        resp = self.client.get(reverse('trainings'), {'sort': 'name'})
        self.assertEqual(resp.status_code, 200)

    def test_training_detail(self):
        resp = self.client.get(reverse('training_detail', args=[self.training_type.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_memberships_page(self):
        resp = self.client.get(reverse('memberships'))
        self.assertEqual(resp.status_code, 200)

    def test_equipment_page(self):
        resp = self.client.get(reverse('equipment'))
        self.assertEqual(resp.status_code, 200)

    def test_reviews_page(self):
        resp = self.client.get(reverse('reviews'))
        self.assertEqual(resp.status_code, 200)


# ── Auth Tests ───────────────────────────────────────────────────
class AuthTests(BaseTestCase):
    def test_login_page(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_register_page(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)

    def test_login_success(self):
        resp = self.client.post(reverse('login'), {
            'username': 'testuser', 'password': 'Test1234!'
        })
        self.assertEqual(resp.status_code, 302)

    def test_logout(self):
        self.client.login(username='testuser', password='Test1234!')
        resp = self.client.get(reverse('logout'))
        self.assertEqual(resp.status_code, 302)

    def test_register_success(self):
        resp = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'address': 'ул. Новая',
            'phone': '+375291234567',
            'birth_date': '2000-01-01',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())


# ── Authenticated User Tests ─────────────────────────────────────
class AuthenticatedUserTests(BaseTestCase):
    def setUp(self):
        self.client.login(username='testuser', password='Test1234!')

    def test_profile_page(self):
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)

    def test_buy_membership_page(self):
        resp = self.client.get(reverse('buy_membership'))
        self.assertEqual(resp.status_code, 200)

    def test_buy_membership_post(self):
        resp = self.client.post(reverse('buy_membership'), {
            'membership_type': self.membership_type.pk,
            'start_date': date.today().isoformat(),
        })
        self.assertEqual(resp.status_code, 302)

    def test_book_training_page(self):
        resp = self.client.get(reverse('book_training'))
        self.assertEqual(resp.status_code, 200)

    def test_book_training_post(self):
        resp = self.client.post(reverse('book_training'), {
            'training': self.training.pk,
        })
        self.assertEqual(resp.status_code, 302)

    def test_add_review_page(self):
        resp = self.client.get(reverse('add_review'))
        self.assertEqual(resp.status_code, 200)

    def test_add_review_post(self):
        resp = self.client.post(reverse('add_review'), {
            'trainer': self.trainer.pk,
            'rating': 4,
            'text': 'Хороший тренер',
        })
        self.assertEqual(resp.status_code, 302)


# ── Staff Tests ──────────────────────────────────────────────────
class StaffViewTests(BaseTestCase):
    def setUp(self):
        self.client.login(username='traineruser', password='Trainer1234!')

    def test_trainer_dashboard(self):
        resp = self.client.get(reverse('trainer_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_statistics_page(self):
        resp = self.client.get(reverse('statistics'))
        self.assertEqual(resp.status_code, 200)

    def test_membership_chart(self):
        resp = self.client.get(reverse('membership_chart'))
        self.assertEqual(resp.status_code, 200)

    def test_training_group_report(self):
        resp = self.client.get(reverse('training_group_report'))
        self.assertEqual(resp.status_code, 200)

    def test_training_group_report_with_id(self):
        resp = self.client.get(reverse('training_group_report'), {'training_id': self.training.pk})
        self.assertEqual(resp.status_code, 200)

    def test_training_count_report(self):
        resp = self.client.get(reverse('training_count_report'), {
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': (date.today() + timedelta(days=30)).isoformat(),
        })
        self.assertEqual(resp.status_code, 200)

    def test_client_cost_report(self):
        resp = self.client.get(reverse('client_cost_report'))
        self.assertEqual(resp.status_code, 200)

    def test_add_promocode_page(self):
        resp = self.client.get(reverse('add_promocode'))
        self.assertEqual(resp.status_code, 200)

    def test_add_training_page(self):
        resp = self.client.get(reverse('add_training'))
        self.assertEqual(resp.status_code, 200)


# ── Staff Required Redirect Tests ────────────────────────────────
class StaffRequiredTests(BaseTestCase):
    def test_statistics_requires_staff(self):
        self.client.login(username='testuser', password='Test1234!')
        resp = self.client.get(reverse('statistics'))
        self.assertEqual(resp.status_code, 302)

    def test_anon_cannot_access_statistics(self):
        resp = self.client.get(reverse('statistics'))
        self.assertEqual(resp.status_code, 302)


# ── API Tests ────────────────────────────────────────────────────
class APITests(BaseTestCase):
    def test_weather_api(self):
        resp = self.client.get(reverse('api_weather'))
        self.assertIn(resp.status_code, [200, 502])
        data = resp.json()
        self.assertIn('status', data)

    def test_quote_api(self):
        resp = self.client.get(reverse('api_quote'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('status', data)


# ── URL Resolution Tests ────────────────────────────────────────
class URLTests(TestCase):
    def test_main_url(self):
        url = reverse('main')
        self.assertEqual(url, '/')

    def test_news_detail_regex(self):
        url = reverse('news_detail', args=[1])
        self.assertEqual(url, '/news/1/')

    def test_trainer_detail_regex(self):
        url = reverse('trainer_detail', args=[1])
        self.assertEqual(url, '/trainers/1/')

    def test_api_weather_url(self):
        url = reverse('api_weather')
        self.assertEqual(url, '/api/weather/')

    def test_api_quote_url(self):
        url = reverse('api_quote')
        self.assertEqual(url, '/api/quote/')


# ── Form Tests ───────────────────────────────────────────────────
class RegisterFormTests(TestCase):
    def test_valid_phone(self):
        form_data = {
            'username': 'formtest',
            'email': 'form@test.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'Тест',
            'last_name': 'Формы',
            'address': 'ул. Тестовая',
            'phone': '+375291234567',
            'birth_date': '2000-01-01',
        }
        form = RegisterForm(data=form_data)
        if not form.is_valid():
            # Phone should be valid
            self.assertNotIn('phone', form.errors)

    def test_invalid_phone(self):
        form_data = {
            'username': 'formtest2',
            'email': 'form2@test.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'Тест',
            'last_name': 'Формы',
            'address': 'ул. Тестовая',
            'phone': '123456',
            'birth_date': '2000-01-01',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_underage_rejected(self):
        form_data = {
            'username': 'formtest3',
            'email': 'form3@test.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'Тест',
            'last_name': 'Формы',
            'address': 'ул. Тестовая',
            'phone': '+375291234567',
            'birth_date': date.today().isoformat(),
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)


class ReviewFormTests(BaseTestCase):
    def test_valid_review(self):
        form = ReviewForm(data={
            'rating': 5,
            'text': 'Отличный тренер!',
            'trainer': self.trainer.pk,
        })
        self.assertTrue(form.is_valid())

    def test_review_without_trainer(self):
        form = ReviewForm(data={
            'rating': 3,
            'text': 'Нормально',
        })
        self.assertTrue(form.is_valid())
