# CyberAware 🛡️

Образовательная платформа по кибербезопасности с геймификацией: курсы, лекции, тесты, опыт (XP), уровни и система достижений.

![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-production-4169E1?logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-development-003B57?logo=sqlite&logoColor=white)
![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway&logoColor=white)

---

## 📖 О проекте

**CyberAware** — веб-платформа для обучения основам кибербезопасности. Пользователи проходят курсы, читают лекции, отвечают на тестовые вопросы и зарабатывают опыт. Прогресс подкрепляется системой из **29 достижений** в 6 категориях, уровнями и трекингом ежедневной активности (streaks).

### Курсы

| Курс | Описание |
|---|---|
| **Cyber Threat Intelligence** | Сбор и анализ threat intelligence, IOC/IOA, MITRE ATT&CK, профилирование злоумышленников |
| **Digital Forensics** | Криминалистика: цепочка custody, анализ дисков и файловых систем, память, логи |
| **White Hacker** | Этичный хакинг: разведка, OWASP Top 10, безопасная эксплуатация, отчётность |
| **AI Cyber Security** | ИИ в безопасности: детекция фишинга и вредоносов, SOAR, adversarial ML |

Каждый курс содержит 4 лекции с тестовыми вопросами (multiple choice).

## ✨ Возможности

- 📚 **Курсы и лекции** — структурированный контент по 4 направлениям кибербезопасности
- ✅ **Тесты** — вопросы с вариантами ответов к каждой лекции, учёт всех попыток
- 🎮 **Геймификация** — XP, уровни, 29 достижений в 6 категориях (обучение, тесты, тематика, активность, прогресс, социальные)
- 🔥 **Streak-система** — отслеживание ежедневной активности, достижения за серии дней (2/5/7/14 подряд)
- 👤 **Профиль** — прогресс по курсам, статистика, история достижений
- ⚙️ **Настройки** — тема (dark/light/system), акцентный цвет, размер шрифта, уведомления, приватность
- 🔐 **Безопасность аккаунта** — смена пароля, история входов (IP, устройство), завершение сессий на других устройствах, флаг 2FA
- 📤 **Экспорт данных** — выгрузка своих данных пользователем

## 🛠️ Технологии

- **Backend:** Python, Django 5.2
- **База данных:** SQLite (разработка) / PostgreSQL (продакшен, через `dj-database-url`)
- **Статика:** WhiteNoise
- **WSGI-сервер:** Gunicorn
- **Деплой:** Railway (`Procfile`, `railway.toml`)

## 📁 Структура проекта

```
CyberAware/
├── myworld/
│   └── cyberaware/                 # Django-проект
│       ├── manage.py
│       ├── cyberaware/             # Настройки, URLconf, WSGI/ASGI
│       │   ├── settings.py
│       │   ├── urls.py
│       │   └── wsgi.py
│       └── members/                # Основное приложение
│           ├── models.py           # Course, Lecture, Member, Quiz, Achievements, Settings
│           ├── views.py            # Все представления
│           ├── urls.py             # Маршруты
│           ├── templates/          # HTML-шаблоны
│           ├── static/images/      # Статика
│           ├── migrations/         # Миграции (включая сидинг курсов)
│           └── management/commands/# CLI-команды (тесты достижений, симуляция)
├── requirements.txt
├── Procfile                        # Команда запуска для Railway
├── railway.toml                    # Конфигурация Railway
├── .env.example                    # Пример переменных окружения
└── ACHIEVEMENTS_SYSTEM_EN.md       # Документация по системе достижений
```

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- pip

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/PlayErsGames666/CyberAware.git
cd CyberAware

# 2. Создать и активировать виртуальное окружение
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env: укажите свой DJANGO_SECRET_KEY

# 5. Применить миграции (курсы и лекции засидятся автоматически)
cd myworld/cyberaware
python manage.py migrate

# 6. Создать суперпользователя (опционально, для админки)
python manage.py createsuperuser

# 7. Запустить сервер
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ — и вы на главной странице. Админка: http://127.0.0.1:8000/admin/

### Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DJANGO_SECRET_KEY` | Секретный ключ Django | insecure-ключ для разработки |
| `DJANGO_DEBUG` | Режим отладки (`True`/`False`) | `True` |
| `DJANGO_ALLOWED_HOSTS` | Разрешённые хосты | `localhost,127.0.0.1` |
| `DATABASE_URL` | Строка подключения к PostgreSQL | не задано → SQLite |

## 🧪 Вспомогательные команды

В приложении есть management-команды для проверки и отладки:

```bash
python manage.py check_templates        # проверка шаблонов
python manage.py show_achievements      # список достижений в системе
python manage.py test_achievements      # тесты логики достижений
python manage.py simulate_user_journey  # симуляция пути пользователя
```

## 🏆 Система достижений

29 достижений в 6 категориях: обучение, тесты, тематические (кибербезопасность), активность (streaks), прогресс (уровни и XP) и др. Подробное описание архитектуры и полный список — в [ACHIEVEMENTS_SYSTEM_EN.md](ACHIEVEMENTS_SYSTEM_EN.md).

## 🌐 Деплой (Railway)

Проект готов к деплою на Railway:

1. `Procfile` запускает Gunicorn: `web: cd myworld/cyberaware && gunicorn cyberaware.wsgi:application`
2. Подключите PostgreSQL-плагин — `DATABASE_URL` подхватится автоматически через `dj-database-url`
3. Задайте `DJANGO_SECRET_KEY` и `DJANGO_DEBUG=False` в переменных окружения сервиса
4. Статика раздаётся через WhiteNoise

## 🤝 Вклад

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/my-feature`
3. Закоммитьте изменения: `git commit -m "Add my feature"`
4. Запушьте: `git push origin feature/my-feature`
5. Откройте Pull Request

## 📄 Лицензия

Проект создан в образовательных целях.
