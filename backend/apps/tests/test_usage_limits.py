import pytest

from apps.usage.services import (
    get_or_create_usage,
    check_can_create_search,
    record_search_created,
    check_can_save_lead,
    record_lead_saved,
)
from apps.tests.factories import UserFactory


@pytest.mark.django_db
def test_user_usage_created_for_user():
    user = UserFactory()

    usage = get_or_create_usage(user)

    assert usage.user == user
    assert usage.beta_access is True
    assert usage.max_searches_per_day > 0


@pytest.mark.django_db
def test_daily_search_limit_blocks_user():
    user = UserFactory()
    usage = get_or_create_usage(user)

    usage.max_searches_per_day = 1
    usage.save()

    first_check = check_can_create_search(user, requested_max_leads=10)
    assert first_check.allowed is True

    record_search_created(user)

    second_check = check_can_create_search(user, requested_max_leads=10)
    assert second_check.allowed is False


@pytest.mark.django_db
def test_lead_limit_blocks_user():
    user = UserFactory()
    usage = get_or_create_usage(user)

    usage.max_leads_per_day = 1
    usage.max_leads_per_month = 1
    usage.save()

    first_check = check_can_save_lead(user)
    assert first_check.allowed is True

    record_lead_saved(user)

    second_check = check_can_save_lead(user)
    assert second_check.allowed is False