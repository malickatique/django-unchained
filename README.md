# django-unchained
# Django Unchained — The Complete Playbook

> A concise, comprehensive reference for Django on macOS (Apple Silicon).
> Designed to be revisited — not read once and forgotten.

---

## Table of Contents

1. [Python & Environment Setup (macOS M-series)](#1-python--environment-setup-macos-m-series)
2. [Django Installation & Project Scaffold](#2-django-installation--project-scaffold)
3. [Project Structure — Modular Layout](#3-project-structure--modular-layout)
4. [Settings, Config & Environment Variables](#4-settings-config--environment-variables)
5. [Database — PostgreSQL, Models, Migrations, Seeds](#5-database--postgresql-models-migrations-seeds)
6. [ORM — Relations & Operations](#6-orm--relations--operations)
7. [Django REST Framework — APIs Done Right](#7-django-rest-framework--apis-done-right)
8. [Exception Handling](#8-exception-handling)
9. [Structured Logging](#9-structured-logging)
10. [Caching](#10-caching)
11. [Async & Queues — Celery + Kafka](#11-async--queues--celery--kafka)
12. [Testing](#12-testing)
13. [Security Checklist](#13-security-checklist)
14. [Deployment Notes](#14-deployment-notes)
15. [Quick Reference — Commands Cheatsheet](#15-quick-reference--commands-cheatsheet)

---

## 1. Python & Environment Setup (macOS M-series)

### Install Homebrew (if missing)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Install Python

```bash
brew install python@3.12          # or latest stable
python3 --version                 # verify
```

### Virtual Environments (use ONE of these)

**Option A — venv (built-in, recommended for beginners)**

```bash
python3 -m venv .venv
source .venv/bin/activate         # activate
deactivate                        # when done
```

**Option B — pyenv + pyenv-virtualenv (manage multiple Python versions)**

```bash
brew install pyenv pyenv-virtualenv

# Add to ~/.zshrc:
# eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"

pyenv install 3.12.7
pyenv virtualenv 3.12.7 django-unchained
pyenv activate django-unchained
```

### pip Essentials

```bash
pip install --upgrade pip
pip install <package>
pip freeze > requirements.txt     # snapshot dependencies
pip install -r requirements.txt   # restore from snapshot
```

### Python Quick Refresher (just enough for Django)

```python
# --- Data types ---
name: str = "django"
count: int = 42
prices: list[float] = [9.99, 19.99]
config: dict[str, str] = {"DEBUG": "True"}

# --- Functions ---
def greet(name: str) -> str:
    return f"Hello, {name}"

# --- Classes ---
class Animal:
    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        raise NotImplementedError

class Dog(Animal):
    def speak(self) -> str:
        return "Woof"

# --- List/Dict comprehensions ---
squares = [x**2 for x in range(10)]
evens = {k: v for k, v in config.items() if k.startswith("D")}

# --- Decorators ---
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("before")
        result = func(*args, **kwargs)
        print("after")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("hello")

# --- Context managers ---
with open("file.txt") as f:
    content = f.read()

# --- Unpacking ---
first, *rest = [1, 2, 3, 4]  # first=1, rest=[2,3,4]

# --- Walrus operator ---
if (n := len(prices)) > 1:
    print(f"Got {n} prices")
```

> **Full Python reference:** https://docs.python.org/3/tutorial/

---

## 2. Django Installation & Project Scaffold

### Install Django + DRF

```bash
pip install django djangorestframework
```

### Create Project

```bash
django-admin startproject config .
# The "." creates the project in the current directory (no nested folder)
```

This gives you:

```
.
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── manage.py
```

### Create an App

```bash
python manage.py startapp users
python manage.py startapp products
```

### Run Dev Server

```bash
python manage.py runserver              # http://127.0.0.1:8000
python manage.py runserver 0.0.0.0:8080 # custom host:port
```

### What is `manage.py`?

A thin wrapper around `django-admin` that sets `DJANGO_SETTINGS_MODULE` for you. Every management command goes through it:

```bash
python manage.py <command>
```

---

## 3. Project Structure — Modular Layout

The default flat layout doesn't scale. Use this structure:

```
django-unchained/
├── config/                     # Project-level config (renamed from project name)
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py         # imports from base + env-specific
│   │   ├── base.py             # shared settings
│   │   ├── development.py      # dev overrides
│   │   ├── production.py       # prod overrides
│   │   └── test.py             # test overrides
│   ├── urls.py                 # root URL conf — include app URLs here
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/                       # all Django apps live here
│   ├── __init__.py
│   ├── users/
│   │   ├── __init__.py
│   │   ├── apps.py             # app config (set name = "apps.users")
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py             # app-level routes
│   │   ├── permissions.py
│   │   ├── filters.py
│   │   ├── signals.py
│   │   ├── tasks.py            # celery/async tasks
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── test_serializers.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_users.py
│   │   └── migrations/
│   └── products/
│       └── ...                 # same structure
│
├── common/                     # shared utilities across apps
│   ├── __init__.py
│   ├── exceptions.py           # global exception handler
│   ├── pagination.py           # custom pagination
│   ├── permissions.py          # shared permissions
│   ├── middleware.py           # custom middleware
│   ├── mixins.py               # reusable model/view mixins
│   └── utils.py
│
├── .env                        # environment variables (git-ignored)
├── .env.example                # template for .env
├── requirements/
│   ├── base.txt
│   ├── development.txt         # -r base.txt + dev tools
│   └── production.txt          # -r base.txt + prod deps
├── manage.py
├── pytest.ini                  # or pyproject.toml
└── docker-compose.yml          # Postgres, Redis, Kafka
```

### Key Wiring

**`apps/users/apps.py`** — fix the app name when apps live under `apps/`:

```python
class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"         # must match the import path
```

**`config/settings/base.py`** — register apps:

```python
INSTALLED_APPS = [
    # Django built-in
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    # Local apps
    "apps.users",
    "apps.products",
]
```

**`config/urls.py`** — include app routes:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/products/", include("apps.products.urls")),
]
```

---

## 4. Settings, Config & Environment Variables

### Install django-environ

```bash
pip install django-environ
```

### `.env` file

```env
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/django_unchained
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### `config/settings/base.py`

```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),  # type, default
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Database
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### `config/settings/development.py`

```python
from .base import *  # noqa: F401,F403

DEBUG = True
```

### `config/settings/production.py`

```python
from .base import *  # noqa: F401,F403

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### `config/settings/__init__.py`

```python
import os

env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from .production import *  # noqa: F401,F403
elif env == "test":
    from .test import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
```

### Switching Environments

```bash
DJANGO_ENV=production python manage.py runserver
# or export it in your shell profile
```

---

## 5. Database — PostgreSQL, Models, Migrations, Seeds

### Install PostgreSQL

```bash
brew install postgresql@16
brew services start postgresql@16

# Create database
createdb django_unchained
```

### Install Python driver

```bash
pip install psycopg[binary]     # psycopg3 (recommended)
# or: pip install psycopg2-binary  # legacy
```

### Docker alternative (recommended)

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: django_unchained
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

```bash
docker-compose up -d db
```

### Models

```python
# apps/users/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model — always do this from day one."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email
```

```python
# apps/products/models.py
import uuid
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base — reuse in every model."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return self.name
```

**Register custom user model in settings:**

```python
# config/settings/base.py
AUTH_USER_MODEL = "users.User"
```

### Common Field Types

| Field | Use For |
|---|---|
| `CharField(max_length=N)` | Short text |
| `TextField()` | Long text |
| `IntegerField()` | Integers |
| `DecimalField(max_digits, decimal_places)` | Money/precision |
| `FloatField()` | Approximate decimals |
| `BooleanField()` | True/False |
| `DateTimeField()` | Timestamps |
| `DateField()` | Dates only |
| `UUIDField()` | UUIDs |
| `SlugField()` | URL-safe strings |
| `EmailField()` | Emails (validates) |
| `URLField()` | URLs |
| `FileField(upload_to=...)` | File uploads |
| `ImageField(upload_to=...)` | Image uploads |
| `JSONField()` | JSON data |
| `PositiveIntegerField()` | >= 0 integers |

### Common Field Options

| Option | Meaning |
|---|---|
| `null=True` | DB allows NULL |
| `blank=True` | Forms/serializers allow empty |
| `default=value` | Default value |
| `unique=True` | Unique constraint |
| `db_index=True` | Create DB index |
| `choices=[("A","Active")]` | Restrict to choices |
| `editable=False` | Exclude from forms |
| `help_text="..."` | Admin/doc hint |

### Migrations

```bash
python manage.py makemigrations              # generate migration files
python manage.py makemigrations users        # for specific app
python manage.py migrate                     # apply all pending
python manage.py showmigrations              # list status
python manage.py sqlmigrate users 0001       # show raw SQL
python manage.py migrate users 0003          # migrate to specific version
python manage.py migrate users zero          # rollback all for app
```

### Seed Data (Management Command)

```python
# apps/users/management/commands/seed_users.py
from django.core.management.base import BaseCommand
from apps.users.models import User


class Command(BaseCommand):
    help = "Seed the database with test users"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10)

    def handle(self, *args, **options):
        count = options["count"]
        users = [
            User(
                username=f"user_{i}",
                email=f"user_{i}@example.com",
            )
            for i in range(count)
        ]
        User.objects.bulk_create(users, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"Seeded {count} users"))
```

```bash
python manage.py seed_users --count 50
```

### Fixtures (alternative seeding)

```bash
python manage.py dumpdata users --indent 2 > fixtures/users.json
python manage.py loaddata fixtures/users.json
```

---

## 6. ORM — Relations & Operations

### Relationship Types

```python
# ForeignKey — Many-to-One
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

# ManyToManyField
class Product(models.Model):
    tags = models.ManyToManyField("Tag", related_name="products", blank=True)

# OneToOneField
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
```

**`on_delete` options:** `CASCADE`, `PROTECT`, `SET_NULL` (needs `null=True`), `SET_DEFAULT`, `DO_NOTHING`

### QuerySet Operations

```python
from apps.products.models import Product

# --- CREATE ---
p = Product.objects.create(name="Widget", price=9.99, category=cat)
p = Product(name="Widget", price=9.99)
p.save()
Product.objects.bulk_create([Product(...), Product(...)])

# --- READ ---
Product.objects.all()                          # all rows
Product.objects.get(id=uuid)                   # single (raises DoesNotExist / MultipleObjectsReturned)
Product.objects.filter(is_active=True)          # WHERE
Product.objects.exclude(stock=0)               # WHERE NOT
Product.objects.first()                        # first or None
Product.objects.last()
Product.objects.count()
Product.objects.exists()

# --- Lookups (double-underscore) ---
Product.objects.filter(name__icontains="widget")   # case-insensitive LIKE
Product.objects.filter(price__gte=10, price__lte=100)  # range
Product.objects.filter(price__in=[9.99, 19.99])
Product.objects.filter(category__name="Electronics")   # traverse FK
Product.objects.filter(created_at__year=2025)

# --- UPDATE ---
Product.objects.filter(is_active=False).update(stock=0)   # bulk
p.name = "New Name"
p.save(update_fields=["name"])   # efficient single-field update

# --- DELETE ---
p.delete()
Product.objects.filter(is_active=False).delete()

# --- ORDERING ---
Product.objects.order_by("price")       # ASC
Product.objects.order_by("-price")      # DESC
Product.objects.order_by("category__name", "-price")

# --- SLICING (LIMIT/OFFSET) ---
Product.objects.all()[:10]              # LIMIT 10
Product.objects.all()[10:20]            # OFFSET 10 LIMIT 10

# --- CHAINING ---
Product.objects.filter(is_active=True).exclude(stock=0).order_by("-price")[:5]

# --- AGGREGATION ---
from django.db.models import Avg, Count, Sum, Max, Min

Product.objects.aggregate(avg_price=Avg("price"))          # {"avg_price": 15.50}
Product.objects.aggregate(total=Sum("price"), count=Count("id"))

# --- ANNOTATION (per-row computed fields) ---
from django.db.models import F, Value
from django.db.models.functions import Concat

categories = Category.objects.annotate(product_count=Count("products"))
# each category now has category.product_count

products = Product.objects.annotate(discounted=F("price") * 0.9)

# --- Q OBJECTS (complex lookups: OR, AND, NOT) ---
from django.db.models import Q

Product.objects.filter(Q(name__icontains="widget") | Q(price__lt=5))
Product.objects.filter(~Q(is_active=True))    # NOT

# --- SELECT RELATED (FK — reduces queries via JOIN) ---
Product.objects.select_related("category", "created_by")

# --- PREFETCH RELATED (M2M / reverse FK — separate query) ---
Category.objects.prefetch_related("products")

# --- VALUES / VALUES_LIST (return dicts/tuples, not model instances) ---
Product.objects.values("name", "price")               # [{"name": ..., "price": ...}]
Product.objects.values_list("name", flat=True)         # ["Widget", "Gadget"]

# --- RAW SQL (escape hatch) ---
Product.objects.raw("SELECT * FROM products WHERE price > %s", [10])

# --- SUBQUERY ---
from django.db.models import Subquery, OuterRef

latest_product = Product.objects.filter(
    category=OuterRef("pk")
).order_by("-created_at")

Category.objects.annotate(
    latest_product_name=Subquery(latest_product.values("name")[:1])
)
```

### Common Lookup Reference

| Lookup | SQL Equivalent |
|---|---|
| `exact` / `iexact` | `= / ILIKE` |
| `contains` / `icontains` | `LIKE '%val%'` |
| `startswith` / `istartswith` | `LIKE 'val%'` |
| `gt`, `gte`, `lt`, `lte` | `>`, `>=`, `<`, `<=` |
| `in` | `IN (...)` |
| `range` | `BETWEEN` |
| `isnull` | `IS NULL` |
| `date`, `year`, `month`, `day` | extract from datetime |
| `regex` / `iregex` | `~ / ~*` |

> **Full ORM reference:** https://docs.djangoproject.com/en/5.1/ref/models/querysets/

---

## 7. Django REST Framework — APIs Done Right

### Install everything

```bash
pip install djangorestframework django-cors-headers django-filter django-ratelimit
```

### DRF Settings

```python
# config/settings/base.py

INSTALLED_APPS += [
    "rest_framework",
    "corsheaders",
    "django_filters",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",   # must be high up
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.RequestLoggingMiddleware",   # custom
]

# CORS
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
# or CORS_ALLOW_ALL_ORIGINS = True  (dev only!)

# DRF global config
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        # or "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",  # if using drf-spectacular
}
```

### Serializers

```python
# apps/products/serializers.py
from rest_framework import serializers
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price",
            "stock", "is_active", "category", "category_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
```

### Views (ViewSets)

```python
# apps/products/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Product
from .serializers import ProductSerializer
from .filters import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "created_by")
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Override for custom filtering logic."""
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Custom action: POST /api/v1/products/<id>/deactivate/"""
        product = self.get_object()
        product.is_active = False
        product.save(update_fields=["is_active"])
        return Response({"status": "deactivated"})
```

### Filters

```python
# apps/products/filters.py
import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__slug")

    class Meta:
        model = Product
        fields = ["is_active", "category"]
```

### URLs (Router)

```python
# apps/products/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register("", ProductViewSet, basename="products")

urlpatterns = router.urls
```

**This auto-generates:**
| Method | URL | Action |
|---|---|---|
| GET | `/api/v1/products/` | list |
| POST | `/api/v1/products/` | create |
| GET | `/api/v1/products/<id>/` | retrieve |
| PUT | `/api/v1/products/<id>/` | update |
| PATCH | `/api/v1/products/<id>/` | partial_update |
| DELETE | `/api/v1/products/<id>/` | destroy |
| POST | `/api/v1/products/<id>/deactivate/` | custom action |

### Consistent Response Contract

```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "data": data,
            "meta": {
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "total_count": self.page.paginator.count,
            },
        })
```

### Custom Middleware

```python
# common/middleware.py
import time
import logging

logger = logging.getLogger("django.request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start

        logger.info(
            "%s %s %s %.3fs",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration,
        )
        return response
```

### Permissions

```python
# apps/products/permissions.py
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.created_by == request.user
```

Use in views: `permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]`

### JWT Authentication (optional)

```bash
pip install djangorestframework-simplejwt
```

```python
# config/settings/base.py
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}
```

```python
# config/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns += [
    path("api/v1/auth/token/", TokenObtainPairView.as_view()),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view()),
]
```

### Security Headers

```python
# config/settings/base.py
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
```

> **Full DRF reference:** https://www.django-rest-framework.org/
> **django-filter reference:** https://django-filter.readthedocs.io/

---

## 8. Exception Handling

### DRF Custom Exception Handler

Register a central handler in settings to normalise all errors into a consistent
envelope. Every exception — DRF, Django, or unhandled — flows through one place.

```python
# config/settings/base.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "common.exceptions.handler.api_exception_handler",
}
```

```python
# common/exceptions/handler.py
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError

logger = logging.getLogger("common.exceptions.handler")


def api_exception_handler(exc, context):
    """Normalise all API errors into a consistent JSON envelope."""

    # Convert Django ValidationError → DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        from rest_framework.exceptions import ValidationError
        exc = ValidationError(
            detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )

    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "message": _extract_message(response.data),
            "errors": response.data,
        }
    else:
        # Unhandled exception — log with full traceback, return generic 500
        logger.exception("Unhandled exception", exc_info=exc)
        response = Response(
            {"success": False, "message": "An unexpected error occurred.", "errors": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _extract_message(data):
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            return str(detail)
    return "Request failed."
```

### Raising Errors in Services

Never construct error response dicts manually. Raise Python exceptions in services
and let the central handler normalise them:

```python
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

def get_user(user_id: str, requesting_user) -> User:
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFound("User not found.")

    if user != requesting_user:
        raise PermissionDenied("You cannot access another user's data.")

    return user
```

### Custom Domain Exceptions

For business-rule violations, define typed exceptions that carry an error code:

```python
# common/exceptions/base.py
from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "business_rule_violation"

    def __init__(self, message: str, error_code: str = None):
        self.detail = message
        self.error_code = error_code
        super().__init__(detail=message)


class NotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"
```

Usage in services:

```python
from common.exceptions.base import BusinessException

def submit_order(order_id: str, user) -> Order:
    order = get_object_or_404(Order, id=order_id, user=user)
    if order.status != "DRAFT":
        raise BusinessException(
            "Only draft orders can be submitted.",
            error_code="INVALID_STATE_TRANSITION",
        )
    ...
```

---

## 9. Structured Logging

This project uses a **structured JSON logging** system built entirely on Python's
standard `logging` module — no third-party libraries required. Every log entry is
a JSON object containing stable, searchable fields: timestamps, request IDs, user
context, event names, and sanitised payload metadata.

### Package Structure

```
common/logging/
├── __init__.py       # Public API: RequestContext, Events, LogCategory, sanitize_*
├── constants.py      # SERVICE_NAME, LogCategory, Events taxonomy, PII masking rules
├── context.py        # Thread-local RequestContext (binds per-request metadata)
├── filters.py        # RequestContextFilter — injects context into every LogRecord
├── formatters.py     # JsonFormatter (prod/files) + ConsoleFormatter (dev terminal)
├── middleware.py     # RequestLoggingMiddleware — access logs entry/exit point
└── sanitizers.py     # PII masking: sanitize_body, sanitize_headers, etc.

common/middleware.py  # AuditMiddleware — thread-local user for AuditModel

logs/                 # Rotating log files (dev only; production uses stdout)
├── access.log        # HTTP request/response lifecycle
├── app.log           # Application/domain business events + infra
├── security.log      # Auth, permissions, sensitive actions
└── error.log         # Unhandled exceptions, integration failures
```

---

### Request Lifecycle — How Logging Flows

```
HTTP Request arrives
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  RequestLoggingMiddleware.__call__()                 │
│                                                      │
│  1. Extract X-Request-Id header (or generate UUID)  │
│  2. Extract X-Correlation-Id header (or use req_id) │
│  3. RequestContext.bind(request_id, method, path,   │
│        client_ip, user_agent, ...)                  │
│  4. _enrich_auth_context() → adds auth_user_id      │
│  5. access_logger.info("http.request.received")     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  AuditMiddleware.__call__()                          │
│                                                      │
│  If DRF resolves auth in the view layer (after       │
│  Django auth middleware), this catches it:           │
│  - Sets thread_local.current_user_id (for AuditModel)│
│  - RequestContext.update(auth_user_id, ...)          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
        View → Serializer → Service
        (any logger.info/warning/error here automatically
         includes request_id, auth_user_id, etc. because
         RequestContextFilter injects them from thread-local)
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  RequestLoggingMiddleware (response phase)           │
│                                                      │
│  6. access_logger.info/warning/error(               │
│        "http.response.sent",                        │
│        status_code, duration_ms, outcome)           │
│  7. response["X-Request-Id"] = request_id           │
│  8. RequestContext.clear()   ← CRITICAL for WSGI    │
└─────────────────────────────────────────────────────┘
                   │
                   ▼
         HTTP Response sent

──────────────────────────────────────────────────────
Every logger.*(msg, extra={...}) call in steps 3-6:
  LogRecord created
       │
       ▼
  RequestContextFilter.filter(record)
  → reads RequestContext.as_dict()
  → injects request_id, auth_user_id, method, path, ...
  → into record.__dict__ (no manual passing needed)
       │
       ▼
  JsonFormatter.format(record)
  → merges base fields + injected context + extra={}
  → outputs single-line JSON
──────────────────────────────────────────────────────
```

---

### Configuration

#### `config/settings/base.py` — Core LOGGING dict

```python
from common.logging.constants import LogCategory

LOG_DIR = BASE_DIR / "logs"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "json": {
            "()": "common.logging.formatters.JsonFormatter",
            "environment": APP_ENVIRONMENT,   # from env("DJANGO_ENV")
            "version": APP_VERSION,           # from git SHA or env("APP_VERSION")
        },
        "console": {
            "()": "common.logging.formatters.ConsoleFormatter",
        },
    },

    "filters": {
        "request_context": {
            "()": "common.logging.filters.RequestContextFilter",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",           # coloured text in dev
            "filters": ["request_context"],
            "stream": "ext://sys.stdout",
        },
        "file_access": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "access.log"),
            "formatter": "json",
            "filters": ["request_context"],
            "maxBytes": 10 * 1024 * 1024,     # 10 MB per file
            "backupCount": 5,                  # 5 rotated backups kept
            "encoding": "utf-8",
        },
        # file_app, file_security, file_error follow the same pattern
    },

    "loggers": {
        LogCategory.ACCESS:   {"handlers": ["file_access", "console"], "level": "INFO",    "propagate": False},
        LogCategory.APP:      {"handlers": ["file_app",    "console"], "level": "INFO",    "propagate": False},
        LogCategory.SECURITY: {"handlers": ["file_security","console"], "level": "INFO",   "propagate": False},
        LogCategory.ERROR:    {"handlers": ["file_error",  "console"], "level": "ERROR",   "propagate": False},
        LogCategory.INFRA:    {"handlers": ["file_app",    "console"], "level": "INFO",    "propagate": False},
        "apps":               {"handlers": ["file_app",    "console"], "level": "INFO",    "propagate": False},
        "common.exceptions.handler": {"handlers": ["file_error", "console"], "level": "WARNING", "propagate": False},
        "django.request":     {"handlers": ["file_error",  "console"], "level": "ERROR",   "propagate": False},
        "django.security":    {"handlers": ["file_security","console"], "level": "WARNING","propagate": False},
        "django.db.backends": {"handlers": ["file_app"],               "level": "WARNING", "propagate": False},
    },

    "root": {"handlers": ["console"], "level": "WARNING"},
}
```

Logger keys use `LogCategory` constants — if you change the prefix in
`constants.py`, the LOGGING dict updates automatically with no extra edits.

#### `config/settings/development.py`

```python
import os
os.makedirs(LOG_DIR, exist_ok=True)      # ensure logs/ directory exists

if env.bool("LOG_SQL", default=False):   # opt-in SQL query logging
    LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"
    LOGGING["loggers"]["django.db.backends"]["handlers"] = ["file_app", "console"]
```

#### `config/settings/production.py`

```python
# Switch console to JSON (machine-readable for ELK/Datadog/CloudWatch)
LOGGING["handlers"]["console"]["formatter"] = "json"

# Remove file handlers — container stdout is the single log transport
_file_handlers = {"file_access", "file_app", "file_security", "file_error"}
for handler_name in _file_handlers:
    LOGGING["handlers"].pop(handler_name, None)

for logger_config in LOGGING["loggers"].values():
    logger_config["handlers"] = [
        h for h in logger_config.get("handlers", []) if h not in _file_handlers
    ] or ["console"]
```

#### `config/settings/test.py`

```python
# Suppress all output — keeps pytest output clean
LOGGING["handlers"] = {"console": {"class": "logging.NullHandler"}}
for logger_config in LOGGING["loggers"].values():
    logger_config["handlers"] = ["console"]
    logger_config["level"] = "CRITICAL"
LOGGING["root"]["level"] = "CRITICAL"
```

---

### Middleware Order

Both logging middlewares must be placed after `AuthenticationMiddleware`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',   # ← Django auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.logging.middleware.RequestLoggingMiddleware',        # ← access logs + context
    'common.middleware.AuditMiddleware',                         # ← created_by/updated_by
]
```

**Why this order matters:**
- `RequestLoggingMiddleware` calls `request.user` to enrich the log context — it needs `AuthenticationMiddleware` to have run first.
- `AuditMiddleware` sets `thread_local.current_user_id` used by `AuditModel.save()` — it needs `RequestLoggingMiddleware` to have already bound the `RequestContext`.

---

### Log Categories — When to Use Which

| Logger constant      | String value    | Use for                                             |
|----------------------|-----------------|-----------------------------------------------------|
| `LogCategory.ACCESS` | `app.access`    | HTTP lifecycle only (handled by middleware)         |
| `LogCategory.APP`    | `app.app`       | Business domain events — orders created, submitted |
| `LogCategory.SECURITY` | `app.security`| Auth events, permission checks, sensitive actions   |
| `LogCategory.ERROR`  | `app.error`     | Integration failures, unhandled exceptions          |
| `LogCategory.INFRA`  | `app.infra`     | External API calls, cache hits/misses, slow queries |
| `"apps"` (or `__name__`) | varies    | General app logging; routes to `app.log`           |

`LogCategory.ACCESS` is used exclusively by `RequestLoggingMiddleware` — don't
use it in services.

---

### How to Use in Your App

#### The standard pattern — services

```python
import logging
from common.logging import Events

logger = logging.getLogger(__name__)          # → routes to "apps" → app.log

def create_order(user, data: dict) -> Order:
    order = Order.objects.create(user=user, **data)

    logger.info(
        "Order created",
        extra={
            "event": Events.USER_CREATED,         # stable event name
            "entity_type": "order",               # what kind of thing
            "entity_id": str(order.id),           # its ID
        },
    )
    return order
```

#### Security events

```python
import logging
from common.logging import LogCategory, Events

security_logger = logging.getLogger(LogCategory.SECURITY)

def change_password(user, old_password, new_password):
    if not user.check_password(old_password):
        security_logger.warning(
            "Password change failed — wrong current password",
            extra={
                "event": Events.AUTH_FAILED,
                "entity_type": "user",
                "entity_id": str(user.id),
            },
        )
        raise ValidationError("Current password is incorrect.")

    user.set_password(new_password)
    user.save()

    security_logger.info(
        "Password changed successfully",
        extra={
            "event": Events.SENSITIVE_ACTION,
            "entity_type": "user",
            "entity_id": str(user.id),
            "action": "password_change",
        },
    )
```

#### Infrastructure / external calls

```python
import logging
from common.logging import LogCategory, Events

infra_logger = logging.getLogger(LogCategory.INFRA)

def send_email(to: str, subject: str, body: str):
    infra_logger.info(
        "Sending email",
        extra={"event": Events.EXTERNAL_REQUEST_SENT, "provider": "smtp", "recipient_domain": to.split("@")[-1]},
    )
    try:
        _smtp_send(to, subject, body)
    except TimeoutError:
        infra_logger.error(
            "Email send timed out",
            extra={"event": Events.EXTERNAL_TIMEOUT, "provider": "smtp"},
        )
        raise
```

#### Logging exceptions

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = call_payment_api(payload)
except Exception as exc:
    logger.exception(            # logs at ERROR + attaches full traceback
        "Payment API call failed",
        extra={"event": "error.integration", "provider": "stripe"},
    )
    raise
```

`logger.exception()` is equivalent to `logger.error(..., exc_info=True)` — always
use it inside `except` blocks so the traceback is captured.

#### Adding context from services (domain enrichment)

```python
from common.logging import RequestContext

def process_payment(order_id: str):
    # Adds order_id to ALL subsequent log entries in this request
    RequestContext.update(order_id=order_id)
    ...
```

#### Celery tasks (carry correlation IDs from HTTP)

```python
from common.logging import RequestContext

@app.task
def send_confirmation_email(order_id: str, correlation_id: str = None):
    RequestContext.bind(
        request_id=send_confirmation_email.request.id,
        correlation_id=correlation_id,   # pass from the HTTP request that triggered the task
    )
    ...
    RequestContext.clear()
```

#### Management commands

```python
import logging
from common.logging import RequestContext

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        RequestContext.bind(request_id="cmd-seed-users")   # optional but useful
        logger.info("Seeding users started")
        ...
        RequestContext.clear()
```

---

### Event Taxonomy

Always use `Events` constants — never invent free-text event strings. This keeps
event names stable, consistent, and searchable in log aggregators.

```python
from common.logging import Events

# HTTP lifecycle (used by middleware only)
Events.HTTP_REQUEST_RECEIVED        # "http.request.received"
Events.HTTP_RESPONSE_SENT           # "http.response.sent"

# Domain
Events.USER_CREATED                 # "domain.user.created"
Events.USER_UPDATED                 # "domain.user.updated"
Events.USER_DEACTIVATED             # "domain.user.deactivated"

# Security
Events.AUTH_SUCCEEDED               # "security.auth.succeeded"
Events.AUTH_FAILED                  # "security.auth.failed"
Events.PERMISSION_DENIED            # "security.permission.denied"
Events.SENSITIVE_ACTION             # "security.sensitive_action.performed"
Events.RATE_LIMIT_HIT               # "security.rate_limit.hit"
Events.TOKEN_EXPIRED                # "security.token.expired"

# Error
Events.ERROR_UNHANDLED              # "error.unhandled"
Events.ERROR_VALIDATION             # "error.validation"
Events.ERROR_BUSINESS_RULE          # "error.business_rule"
Events.ERROR_DATABASE               # "error.database"
Events.ERROR_INTEGRATION            # "error.integration"

# Infrastructure
Events.EXTERNAL_REQUEST_SENT        # "infra.external.request.sent"
Events.EXTERNAL_RESPONSE_RECEIVED   # "infra.external.response.received"
Events.EXTERNAL_TIMEOUT             # "infra.external.timeout"
Events.DB_SLOW_QUERY                # "infra.db.slow_query"
```

**Adding new events:** Add to `Events` in `common/logging/constants.py`.
**Never rename or delete** existing event names — downstream alerts and log queries
depend on them. Only add new names or leave old ones in place as deprecated.

---

### PII Masking

All request bodies, headers, and query params logged by `RequestLoggingMiddleware`
are automatically sanitised. The masking rules live in `constants.py`.

| Strategy           | Example fields                                   | Output            |
|--------------------|--------------------------------------------------|-------------------|
| Full mask `***`    | `password`, `token`, `otp`, `api_key`, `secret`  | `"***"`           |
| Partial `***XXXX`  | `passport_number`, `iban`, `card_number`, `ssn`  | `"***4321"`       |
| Email `x***@d.com` | `email`, `email_address`, `contact_email`        | `"j***@gmail.com"`|
| Phone `***XXXX`    | `phone`, `mobile`, `phone_number`                | `"***5678"`       |
| `[REDACTED]`       | `biometric_data`, `file_content`, `dob`          | `"[REDACTED]"`    |
| Header allowlist   | Only `content-type`, `user-agent`, `x-request-id`, etc. logged | others dropped |

Masking is applied recursively up to 5 levels deep in nested JSON.

**Manually sanitise payloads** you log yourself (e.g. webhook bodies, async job
payloads):

```python
from common.logging import sanitize_body, sanitize_headers

logger.info(
    "Webhook received",
    extra={"payload": sanitize_body(raw_webhook_data)},
)

logger.info(
    "Outbound API call",
    extra={"headers": sanitize_headers(request_headers)},
)
```

**Adding fields to the masking registry:** Edit the relevant frozenset in
`common/logging/constants.py`. Never add masking logic inline in services.

---

### Example Log Entries

**Development console (coloured text):**

```
[2026-04-07 10:23:01] INFO     app.access | http.request.received
  POST /api/v1/users/
  request_id=7d53de5e | method=POST | path=/api/v1/users/

[2026-04-07 10:23:01] INFO     app.access | http.response.sent
  POST /api/v1/users/ -> 201 (34.5ms)
  request_id=7d53de5e | status_code=201 | duration_ms=34.5 | outcome=success
```

**JSON (files in dev / stdout in production):**

```json
{
  "timestamp": "2026-04-07T10:23:01.123456+00:00",
  "level": "INFO",
  "logger": "app.access",
  "service": "my-project",
  "environment": "production",
  "version": "v1.4.2",
  "hostname": "web-1.internal",
  "pid": 12345,
  "message": "POST /api/v1/users/ -> 201 (34.5ms)",
  "event": "http.response.sent",
  "category": "access",
  "request_id": "7d53de5e-0f32-4dba-aa06-3919498f7165",
  "correlation_id": "7d53de5e-0f32-4dba-aa06-3919498f7165",
  "method": "POST",
  "path": "/api/v1/users/",
  "status_code": 201,
  "duration_ms": 34.5,
  "outcome": "success",
  "client_ip": "203.0.113.42",
  "auth_user_id": "0196a3bc-1234-7890-abcd-ef0123456789"
}
```

---

### Best Practices

**1. One logger per module, not one per class**

```python
# Good — standard Python convention
logger = logging.getLogger(__name__)

# Avoid — overly granular, no routing benefit
logger = logging.getLogger("apps.orders.services.OrderService")
```

**2. Always use `extra={}` for structured data — never interpolate into the message**

```python
# Good — structured, searchable in ELK/Datadog
logger.info("Order submitted", extra={"event": Events.USER_CREATED, "order_id": str(order.id)})

# Bad — unstructured, hard to query
logger.info(f"Order {order.id} submitted by user {user.id}")
```

**3. Choose the right level**

| Level | Use for |
|-------|---------|
| `DEBUG` | Verbose tracing — local development only, never in production |
| `INFO` | Normal business events — order created, user logged in |
| `WARNING` | Expected failures — auth rejected, validation failed, retrying |
| `ERROR` | Unexpected failures that need attention — integration timeout, 500 |
| `CRITICAL` | System is partially down — leave this for alerts |

**4. Use `logger.exception()` inside `except` blocks — never `logger.error()`**

```python
# Good — captures full traceback automatically
try:
    call_external_api()
except Exception:
    logger.exception("External API call failed")

# Bad — loses the traceback
except Exception as exc:
    logger.error(f"External API call failed: {exc}")
```

**5. Use `Events` constants, never free-text event strings**

Alerts, dashboards, and log queries depend on stable event names. Free-text breaks
them silently. Add new constants to `Events` class — don't create one-off strings.

**6. Never log raw request/response bodies — always sanitise first**

Middleware does this automatically for HTTP requests. For everything else (Celery
task args, webhook callbacks, external API responses), call `sanitize_body()` before
putting data into `extra={}`.

**7. `propagate: False` on all named loggers**

Without it, records travel up to the root logger and get double-logged. All named
loggers in the LOGGING config already set `"propagate": False`.

**8. Don't log inside tight loops — aggregate instead**

```python
# Bad — thousands of log entries
for item in large_queryset:
    logger.info("Processing item", extra={"item_id": item.id})

# Good — one summary entry
logger.info("Batch processed", extra={"count": len(items), "duration_ms": elapsed})
```

**9. Use `RequestContext.update()` to enrich all logs for a domain operation**

```python
# After this call, ALL subsequent logger.* calls in this request will include order_id
RequestContext.update(order_id=str(order.id))
```

This is far better than manually passing `order_id` in every `extra={}`.

**10. `RequestContext.clear()` is called automatically — don't call it manually**

`RequestLoggingMiddleware` handles cleanup after every response. Only call it
manually in Celery tasks and management commands, where no middleware runs.

---

### Customising When Cloning

| What to change | Where | How |
|----------------|-------|-----|
| Service name in logs | `.env` | `LOG_SERVICE_NAME=my-project` |
| Logger prefix (`app.`) | `common/logging/constants.py` | Change `"app."` in `LogCategory` |
| Domain event names | `common/logging/constants.py` | Add to `Events` class |
| Binary upload paths (no body logging) | `common/logging/constants.py` | Add to `NO_BODY_LOG_PATHS` |
| PII fields | `common/logging/constants.py` | Add to relevant masking frozenset |
| Log rotation size/count | `config/settings/base.py` | `maxBytes`, `backupCount` in handlers |

`SERVICE_NAME` is the only value that **does not require a code change** — set
`LOG_SERVICE_NAME` in `.env` or your container environment and it's picked up
automatically.

---

### `.env` variables for logging

```bash
LOG_SERVICE_NAME=my-project       # service name in JSON logs (default: django-unchained)
LOG_SQL=True                      # enable SQL query logging in dev (default: False)
APP_VERSION=v1.2.3                # version field in JSON logs (default: git SHA)
DJANGO_ENV=development            # environment field in JSON logs
```

For full audit logging of model field changes, use:
> **django-auditlog:** https://github.com/jazzband/django-auditlog
> **django-simple-history:** https://github.com/jazzband/django-simple-history

---

## 10. Caching

### Install Redis

```bash
brew install redis
brew services start redis
# or add to docker-compose.yml
```

### Configure Django Cache

```bash
pip install django-redis
```

```python
# config/settings/base.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,  # 5 minutes default
    }
}
```

### Usage

```python
from django.core.cache import cache

# Basic
cache.set("my_key", "my_value", timeout=60)   # 60 seconds
value = cache.get("my_key")                     # returns None if expired
cache.delete("my_key")

# get_or_set — compute only if missing
value = cache.get_or_set("expensive_key", lambda: compute_expensive(), timeout=300)

# Cache in views
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
def my_view(request):
    ...
```

### Per-View Caching in DRF

```python
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class ProductViewSet(viewsets.ModelViewSet):
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

### Cache Invalidation Pattern

```python
# apps/products/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    cache.delete(f"product_{instance.id}")
    cache.delete("product_list")
```

Register signals in `apps/products/apps.py`:

```python
class ProductsConfig(AppConfig):
    name = "apps.products"

    def ready(self):
        import apps.products.signals  # noqa: F401
```

---

## 11. Async & Queues — Celery + Kafka

### Celery Setup (standard async tasks)

```bash
pip install celery[redis]
```

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()    # auto-finds tasks.py in each app
```

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ["celery_app"]
```

```python
# config/settings/base.py
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
```

```python
# apps/products/tasks.py
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_product_notification(self, product_id: str):
    try:
        from apps.products.models import Product
        product = Product.objects.get(id=product_id)
        # ... send email/notification
        logger.info("Notification sent for product %s", product_id)
    except Exception as exc:
        logger.error("Task failed: %s", exc)
        self.retry(exc=exc)
```

```python
# Call from anywhere
from apps.products.tasks import send_product_notification

send_product_notification.delay(str(product.id))                    # fire and forget
send_product_notification.apply_async(args=[str(product.id)], countdown=30)  # delay 30s
```

### Run Celery Worker

```bash
celery -A config worker -l info
celery -A config beat -l info     # periodic tasks (add django-celery-beat)
```

### Kafka Integration (event streaming)

For Kafka-based event-driven patterns (e.g., microservice communication):

```bash
pip install confluent-kafka
```

```yaml
# docker-compose.yml — add Kafka
services:
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    ports:
      - "9092:9092"
```

```python
# common/kafka.py
from confluent_kafka import Producer, Consumer
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

KAFKA_CONFIG = {
    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
}


def publish_event(topic: str, key: str, data: dict):
    producer = Producer(KAFKA_CONFIG)
    producer.produce(
        topic,
        key=key.encode("utf-8"),
        value=json.dumps(data).encode("utf-8"),
        callback=_delivery_report,
    )
    producer.flush()


def _delivery_report(err, msg):
    if err:
        logger.error("Kafka delivery failed: %s", err)
    else:
        logger.info("Kafka message delivered to %s [%d]", msg.topic(), msg.partition())
```

```python
# Usage in views or signals
from common.kafka import publish_event

publish_event(
    topic="product-events",
    key=str(product.id),
    data={
        "event": "product.created",
        "product_id": str(product.id),
        "name": product.name,
    },
)
```

Kafka consumer (run as management command or separate service):

```python
# apps/products/management/commands/consume_events.py
from django.core.management.base import BaseCommand
from confluent_kafka import Consumer
from django.conf import settings
import json


class Command(BaseCommand):
    help = "Consume Kafka events"

    def handle(self, *args, **options):
        consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "django-unchained",
            "auto.offset.reset": "earliest",
        })
        consumer.subscribe(["product-events"])

        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    self.stderr.write(f"Error: {msg.error()}")
                    continue

                data = json.loads(msg.value().decode("utf-8"))
                self.stdout.write(f"Received: {data}")
                # Process event...
        finally:
            consumer.close()
```

```python
# config/settings/base.py
KAFKA_BOOTSTRAP_SERVERS = env("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092")
```

---

## 12. Testing

### Setup

```bash
pip install pytest pytest-django factory-boy faker
```

```ini
# pytest.ini (or in pyproject.toml)
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --reuse-db
```

### Model Factory

```python
# apps/products/tests/factories.py
import factory
from apps.products.models import Product, Category
from apps.users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker("word")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    stock = factory.Faker("random_int", min=0, max=100)
    category = factory.SubFactory(CategoryFactory)
    created_by = factory.SubFactory(UserFactory)
```

### Model Tests

```python
# apps/products/tests/test_models.py
import pytest
from .factories import ProductFactory


@pytest.mark.django_db
class TestProduct:
    def test_str(self):
        product = ProductFactory(name="Widget")
        assert str(product) == "Widget"

    def test_default_is_active(self):
        product = ProductFactory()
        assert product.is_active is True
```

### API Tests

```python
# apps/products/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from .factories import ProductFactory, UserFactory, CategoryFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestProductAPI:
    def test_list_products(self, authenticated_client):
        ProductFactory.create_batch(3)
        response = authenticated_client.get("/api/v1/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 3

    def test_create_product(self, authenticated_client):
        category = CategoryFactory()
        payload = {
            "name": "New Product",
            "price": "19.99",
            "stock": 10,
            "category_id": str(category.id),
        }
        response = authenticated_client.post("/api/v1/products/", payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_unauthenticated_access(self, api_client):
        response = api_client.get("/api/v1/products/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### Run Tests

```bash
pytest                              # all tests
pytest apps/products/               # one app
pytest -k "test_create"             # by name pattern
pytest --cov=apps --cov-report=html # with coverage
```

> **pytest-django docs:** https://pytest-django.readthedocs.io/
> **factory-boy docs:** https://factoryboy.readthedocs.io/

---

## 13. Security Checklist

```python
# config/settings/production.py — ensure these are set

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")       # never hardcode
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Misc
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

**Additional measures:**
- Always use `AUTH_USER_MODEL` (custom user) from day one
- Use `@permission_classes` on every view
- Validate and sanitize all inputs via serializers
- Use parameterized queries (ORM does this — avoid raw SQL)
- Rate-limit auth endpoints aggressively
- Keep `SECRET_KEY` and `DATABASE_URL` out of version control
- Run `python manage.py check --deploy` before deploying

> **Django security docs:** https://docs.djangoproject.com/en/5.1/topics/security/

---

## 14. Deployment Notes

### Checklist

```bash
python manage.py check --deploy        # catch common issues
python manage.py collectstatic         # gather static files
```

### Gunicorn (production WSGI server)

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### Environment Variable Management

In production, use your platform's secret manager instead of `.env` files:
- **AWS:** Secrets Manager / Parameter Store
- **GCP:** Secret Manager
- **Railway/Render/Fly:** Dashboard env vars

---

## 15. Quick Reference — Commands Cheatsheet

### Project & Apps

```bash
django-admin startproject config .        # new project
python manage.py startapp <name>          # new app
python manage.py runserver                # dev server (port 8000)
python manage.py shell                    # Django REPL
python manage.py dbshell                  # DB REPL
```

### Database & Migrations

```bash
python manage.py makemigrations           # create migrations
python manage.py migrate                  # apply migrations
python manage.py showmigrations           # list all
python manage.py sqlmigrate <app> <num>   # show SQL
python manage.py migrate <app> zero       # rollback app
python manage.py flush                    # wipe all data (keeps tables)
```

### Data

```bash
python manage.py createsuperuser          # admin user
python manage.py dumpdata <app> > f.json  # export
python manage.py loaddata f.json          # import
python manage.py seed_users --count 50    # custom command
```

### Testing & Quality

```bash
pytest                                    # run all tests
pytest --cov=apps                         # with coverage
python manage.py check                    # system check
python manage.py check --deploy           # production check
```

### Static & Production

```bash
python manage.py collectstatic            # gather static files
gunicorn config.wsgi:application -w 4     # production server
celery -A config worker -l info           # celery worker
celery -A config beat -l info             # celery scheduler
```

### Useful Django Shell Commands

```python
python manage.py shell
>>> from apps.users.models import User
>>> User.objects.count()
>>> User.objects.create_superuser("admin", "admin@x.com", "pass")
>>> from django.db import connection
>>> connection.queries  # see SQL queries (DEBUG=True)
```

---

## Key Links

| Topic | URL |
|---|---|
| Django docs | https://docs.djangoproject.com/en/5.1/ |
| DRF docs | https://www.django-rest-framework.org/ |
| Django packages | https://djangopackages.org/ |
| ORM lookups | https://docs.djangoproject.com/en/5.1/ref/models/querysets/ |
| Field reference | https://docs.djangoproject.com/en/5.1/ref/models/fields/ |
| Settings reference | https://docs.djangoproject.com/en/5.1/ref/settings/ |
| Security guide | https://docs.djangoproject.com/en/5.1/topics/security/ |
| Celery docs | https://docs.celeryq.dev/ |
| pytest-django | https://pytest-django.readthedocs.io/ |
| django-environ | https://django-environ.readthedocs.io/ |
| drf-spectacular (OpenAPI) | https://drf-spectacular.readthedocs.io/ |
| django-filter | https://django-filter.readthedocs.io/ |
| simplejwt | https://django-rest-framework-simplejwt.readthedocs.io/ |

---

*Built for django-unchained. Keep building.*
