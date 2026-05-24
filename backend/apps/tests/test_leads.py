import pytest

from rest_framework.test import APIClient

from apps.tests.factories import UserFactory, SearchFactory, LeadFactory


@pytest.mark.django_db
def test_user_can_list_own_leads():
    user = UserFactory()
    search = SearchFactory(user=user)
    LeadFactory(search=search)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/leads/")

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_user_cannot_see_other_user_leads():
    user_a = UserFactory()
    user_b = UserFactory()

    search_b = SearchFactory(user=user_b)
    LeadFactory(search=search_b)

    client = APIClient()
    client.force_authenticate(user=user_a)

    response = client.get("/api/leads/")

    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_user_can_update_own_lead_note():
    user = UserFactory()
    search = SearchFactory(user=user)
    lead = LeadFactory(search=search)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        f"/api/leads/{lead.id}/",
        {
            "notes": "Good lead",
            "is_favorite": True,
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["notes"] == "Good lead"
    assert response.data["is_favorite"] is True