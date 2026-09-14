"""Наполнение таблиц, добавленных в ЛР1 (СТРВП).

Заполняет: партнёров, историю компании, сертификаты, сотрудников,
изображения абонементов, промо-видео компании. Команда идемпотентна —
повторный запуск не создаёт дублей.

    python manage.py load_lab1_data
"""
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from gym.models import (
    Certificate,
    CompanyInfo,
    CompanyMilestone,
    Employee,
    MembershipType,
    Partner,
)

STATIC_DIR = Path(settings.BASE_DIR) / 'gym' / 'static' / 'gym'

PARTNERS = [
    ('NutriLab', 'Спортивное питание и нутрицевтика для клиентов клуба',
     'nutrition', 'https://www.myprotein.com/', 'nutrilab.svg', 2019, 10),
    ('SportLine', 'Экипировка, обувь и аксессуары со скидкой 15% по клубной карте',
     'equipment', 'https://www.decathlon.com/', 'sportmaster.svg', 2020, 20),
    ('AquaPro', 'Бассейн-партнёр: аквааэробика и восстановительное плавание',
     'equipment', 'https://www.speedo.com/', 'aquapro.svg', 2021, 30),
    ('MedCenter', 'Спортивная медицина, УЗИ-диагностика и массаж',
     'medicine', 'https://www.who.int/', 'medcenter.svg', 2018, 40),
    ('TechFit', 'Умные браслеты и интеграция тренировок с мобильным приложением',
     'tech', 'https://www.garmin.com/', 'techfit.svg', 2022, 50),
    ('EnergyBar', 'Фитнес-бар в холле клуба: смузи, протеиновые коктейли',
     'nutrition', 'https://www.clifbar.com/', 'energybar.svg', 2023, 60),
]

MILESTONES = [
    (2015, 'Открытие первого зала на 400 м²',
     'Клуб начинался с одного тренажёрного зала на улице Спортивной, 15 '
     'и команды из четырёх тренеров.'),
    (2017, 'Запуск групповых программ',
     'Появились направления йоги, пилатеса и функционального тренинга. '
     'Число постоянных клиентов превысило 500 человек.'),
    (2019, 'Реконструкция и второй этаж',
     'Площадь клуба выросла до 1200 м². Открылись студия единоборств '
     'и зона свободных весов с оборудованием Hammer Strength.'),
    (2021, 'Онлайн-расписание и личный кабинет',
     'Клиенты получили возможность записываться на тренировки через сайт '
     'и отслеживать срок действия абонемента.'),
    (2023, 'Сертификация услуг по СТБ 1352-2018',
     'Клуб прошёл добровольную сертификацию физкультурно-оздоровительных услуг '
     'и подтвердил квалификацию тренерского состава.'),
    (2025, 'Отделение восстановления',
     'Открылись кабинет спортивного массажа, криотерапия и зона стретчинга '
     'в партнёрстве с MedCenter.'),
]

CERTIFICATES = [
    ('Сертификат соответствия на физкультурно-оздоровительные услуги',
     'BY/112 04.07.021 01234',
     'РУП «Белорусский государственный институт стандартизации и сертификации» (БелГИСС)',
     date(2024, 3, 14), date(2027, 3, 13),
     'Услуги физкультурно-оздоровительные, оказываемые ООО «ФитЛайф Плюс», соответствуют '
     'требованиям СТБ 1352-2018 «Услуги физкультурно-оздоровительные. Общие требования». '
     'Область сертификации: групповые и персональные тренировки, услуги тренажёрного зала.'),
    ('Санитарно-гигиеническое заключение',
     '№ 07-14/2024-118',
     'Центр гигиены и эпидемиологии Первомайского района г. Минска',
     date(2024, 1, 22), date(2027, 1, 21),
     'Помещения клуба по адресу г. Минск, ул. Спортивная, 15 соответствуют требованиям '
     'санитарных норм и правил, предъявляемым к физкультурно-оздоровительным объектам.'),
]

EMPLOYEES = [
    ('Анна', 'Полякова', 'Управляющая клубом',
     'Отвечает за работу клуба в целом: расписание залов, качество обслуживания, '
     'разбор обращений клиентов, согласование корпоративных договоров.',
     '+375 29 123-45-01', 'a.polyakova@fitlifegym.by', 1, 'каб. 201', 'Пн–Пт 09:00–18:00'),
    ('Максим', 'Ковалёв', 'Старший тренер тренажёрного зала',
     'Составляет индивидуальные программы силовых тренировок, проводит вводный '
     'инструктаж и фитнес-тестирование, курирует работу тренеров зала.',
     '+375 29 123-45-02', 'm.kovalev@fitlifegym.by', 2, 'зал 1', 'Пн–Сб 07:00–15:00'),
    ('Ирина', 'Соколовская', 'Администратор ресепшена',
     'Оформляет и продлевает абонементы, консультирует по акциям и промокодам, '
     'ведёт запись на персональные тренировки и выдаёт клубные карты.',
     '+375 29 123-45-03', 'i.sokolovskaya@fitlifegym.by', 3, 'ресепшен', 'Пн–Вс 06:30–23:00'),
    ('Дмитрий', 'Вербицкий', 'Инструктор групповых программ',
     'Проводит занятия по функциональному тренингу, кроссфиту и TRX, '
     'формирует сетку групповых классов и обучает новичков технике упражнений.',
     '+375 29 123-45-04', 'd.verbitsky@fitlifegym.by', 4, 'зал 3', 'Вт–Сб 10:00–21:00'),
    ('Елена', 'Радевич', 'Врач спортивной медицины',
     'Проводит первичный медосмотр, оценивает допуск к нагрузкам, даёт рекомендации '
     'по восстановлению и работает с клиентами после травм.',
     '+375 29 123-45-05', 'e.radevich@fitlifegym.by', 5, 'каб. 105', 'Пн, Ср, Пт 10:00–17:00'),
    ('Олег', 'Лукашевич', 'Инженер по оборудованию',
     'Обслуживает тренажёры, ведёт журнал техосмотров, принимает заявки '
     'о неисправностях и контролирует безопасность инвентаря.',
     '+375 29 123-45-06', 'o.lukashevich@fitlifegym.by', 6, 'тех. зона', 'Пн–Пт 08:00–17:00'),
]


class Command(BaseCommand):
    help = "Загружает данные ЛР1: партнёры, история, сертификаты, сотрудники, медиа"

    @transaction.atomic
    def handle(self, *args, **options):
        company = self._ensure_company()
        self._load_partners()
        self._load_milestones(company)
        self._load_certificates(company)
        self._load_employees()
        self._decorate_memberships()
        self.stdout.write(self.style.SUCCESS("Данные ЛР1 загружены."))

    # ------------------------------------------------------------------ utils
    def _attach(self, obj, field_name, relative_path, save_name=None):
        """Копирует файл из static/gym/... в MEDIA_ROOT и привязывает к полю."""
        if getattr(obj, field_name):
            return
        source = STATIC_DIR / relative_path
        if not source.exists():
            self.stdout.write(self.style.WARNING(f"  нет файла {source}"))
            return
        with source.open('rb') as fh:
            getattr(obj, field_name).save(save_name or source.name, File(fh), save=True)

    # ------------------------------------------------------------------ data
    def _ensure_company(self):
        # load_test_data создаёт 10 тестовых "филиалов" для прошлой лабы.
        # Нам нужна одна конкретная запись с историей, видео и реквизитами,
        # поэтому ищем по имени, а не берём первую попавшуюся из базы.
        company = CompanyInfo.objects.filter(name='FitLife Gym').first()
        if company is None:
            company = CompanyInfo.objects.create(
                name='FitLife Gym',
                founding_year=2015,
                history=(
                    'FitLife Gym — минский фитнес-клуб полного цикла. Мы начинали в 2015 году '
                    'с одного зала и четырёх тренеров, а сегодня это 1200 м² площадей, '
                    'пять специализированных зон и более двух тысяч постоянных клиентов.'
                ),
                address='г. Минск, ул. Спортивная, 15',
                phone='+375 29 123-45-67',
                email='info@fitlifegym.by',
                requisites=(
                    'ООО «ФитЛайф Плюс»\n'
                    'УНП 191234567\n'
                    'Юридический адрес: 220030, г. Минск, ул. Спортивная, 15, пом. 3\n'
                    'р/с BY86 AKBB 3012 0000 0012 3456 7890 в ОАО «АСБ Беларусбанк»\n'
                    'БИК AKBBBY2X\n'
                    'Директор: Полякова Анна Сергеевна'
                ),
            )
            self.stdout.write("  создана запись CompanyInfo")
        if not company.slogan:
            company.slogan = 'Сила рождается в привычке'
            company.save(update_fields=['slogan'])
        self._attach(company, 'video', 'media/promo.mp4', 'fitlife-promo.mp4')
        self._attach(company, 'video_poster', 'media/promo-poster.jpg', 'fitlife-promo-poster.jpg')
        self._attach(company, 'logo', 'img/logo.svg', 'fitlife-logo.svg')
        return company

    def _load_partners(self):
        for name, desc, category, url, logo, since, order in PARTNERS:
            partner, created = Partner.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc, 'category': category, 'website': url,
                    'since_year': since, 'sort_order': order,
                },
            )
            self._attach(partner, 'logo', f'img/partners/{logo}')
            if created:
                self.stdout.write(f"  партнёр: {name}")

    def _load_milestones(self, company):
        for year, title, description in MILESTONES:
            CompanyMilestone.objects.get_or_create(
                company=company, year=year,
                defaults={'title': title, 'description': description},
            )
        self.stdout.write(f"  история компании: {company.milestones.count()} записей")

    def _load_certificates(self, company):
        for title, number, issued_by, issued, valid, description in CERTIFICATES:
            cert, _ = Certificate.objects.get_or_create(
                number=number,
                defaults={
                    'company': company, 'title': title, 'issued_by': issued_by,
                    'issue_date': issued, 'valid_until': valid, 'description': description,
                },
            )
            self._attach(cert, 'document', 'docs/fitlife-certificate.pdf')
        self.stdout.write(f"  сертификаты: {company.certificates.count()}")

    def _load_employees(self):
        for first, last, position, duties, phone, email, idx, office, hours in EMPLOYEES:
            employee, created = Employee.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first, 'last_name': last, 'position': position,
                    'duties': duties, 'phone': phone, 'office': office,
                    'work_hours': hours, 'sort_order': idx,
                },
            )
            self._attach(employee, 'photo', f'img/employees/employee-{idx}.jpg')
            if created:
                self.stdout.write(f"  сотрудник: {last} {first}")

    def _decorate_memberships(self):
        """Добавляет абонементам картинку для каталога (нейтральную, без
        текста — название абонемента показывается HTML-текстом, а не
        встроено в саму картинку, чтобы они не могли разойтись)."""
        for index, membership in enumerate(MembershipType.objects.order_by('id'), start=1):
            slot = (index - 1) % 4 + 1
            if not membership.short_description:
                membership.short_description = membership.description[:150]
                membership.save(update_fields=['short_description'])
            self._attach(
                membership, 'image', f'img/products/membership-{slot}.jpg',
                f'membership-{membership.pk}.jpg',
            )
        self.stdout.write(f"  абонементы оформлены: {MembershipType.objects.count()}")
