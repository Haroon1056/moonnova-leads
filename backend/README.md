leadgen_saas/
├── backend/
│   ├── config/              # Django project settings
│   ├── apps/
│   │   ├── accounts/        # Auth system
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   ├── managers.py
│   │   │   ├── tokens.py
│   │   │   ├── permissions.py
│   │   │   ├── services.py
│   │   │   └── utils.py
│   │   ├── leads/           # Leads & scraping
│   │   ├── searches/        # User searches
searches/
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   ├── services.py
│   │   │   ├── tasks.py
│   │   │   └── permissions.py
│   │   └── core/            # Shared utilities
│   ├── services/            # Business logic (IMPORTANT)
│   │   ├── scraper/
│   │   ├── parser/
│   │   ├── cleaner/
│   │   └── exporter/
│   ├── workers/             # Celery tasks
│   ├── requirements/
│   ├── manage.py
│   └── docker/
├── frontend/ (later)
└── docker-compose.yml


accounts/
├── models.py
├── views.py
├── serializers.py
├── urls.py
├── managers.py
├── tokens.py
├── permissions.py
├── services.py
└── utils.py