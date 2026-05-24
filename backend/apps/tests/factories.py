import factory

from django.contrib.auth import get_user_model

from apps.searches.models import Search
from apps.leads.models import Lead


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Sequence(lambda n: f"Test User {n}")
    is_active = True
    is_verified = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "TestPassword123!"
        self.set_password(password)

        if create:
            self.save()


class SearchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Search

    user = factory.SubFactory(UserFactory)
    keywords = ["plumber"]
    locations = ["Austin TX"]
    max_leads = 50
    scrape_mode = "safe"
    email_enrichment = True
    total_tasks = 1
    completed_tasks = 0
    failed_tasks = 0
    status = "pending"


class LeadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lead

    search = factory.SubFactory(SearchFactory)
    name = factory.Sequence(lambda n: f"Test Business {n}")
    keyword = "plumber"
    location = "Austin TX"
    phone = "1234567890"
    website = "https://example-business.com"
    has_website = True
    website_status = "working"
    status = "warm"