import pytest

from rest_framework.test import APIClient

from apps.tests.factories import UserFactory, SearchFactory


@pytest.mark.django_db
def test_user_cannot_access_other_user_search_detail():
    user_a = UserFactory()
    user_b = UserFactory()

    search = SearchFactory(user=user_b)

    client = APIClient()
    client.force_authenticate(user=user_a)

    response = client.get(f"/api/searches/{search.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_can_access_own_search_detail():
    user = UserFactory()
    search = SearchFactory(user=user)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f"/api/searches/{search.id}/")

    assert response.status_code == 200