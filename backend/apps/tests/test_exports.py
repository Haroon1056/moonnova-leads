import pytest

from rest_framework.test import APIClient

from apps.tests.factories import UserFactory, SearchFactory, LeadFactory
from apps.leads.models import ExportHistory


@pytest.mark.django_db
def test_export_creates_export_history():
    user = UserFactory()
    search = SearchFactory(user=user)
    LeadFactory(search=search)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/leads/export/")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"

    assert ExportHistory.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_export_history_list():
    user = UserFactory()
    search = SearchFactory(user=user)
    LeadFactory(search=search)

    client = APIClient()
    client.force_authenticate(user=user)

    client.get("/api/leads/export/")

    response = client.get("/api/leads/export-history/")

    assert response.status_code == 200
    assert len(response.data) >= 1