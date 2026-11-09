"""Offline regression tests: link verification and Chile-remote classification."""
import unittest
from unittest.mock import patch

from scripts import audit_links, sync_supabase


class LocatorTests(unittest.TestCase):
    def test_ashby(self):
        self.assertEqual(
            audit_links.locator("https://jobs.ashbyhq.com/kraken.com/75495bad-c200-46a3-8ecc-6e89efa88ad5"),
            ("ashby", "kraken.com", "75495bad-c200-46a3-8ecc-6e89efa88ad5"),
        )

    def test_ashby_encoded_board(self):
        self.assertEqual(
            audit_links.locator("https://jobs.ashbyhq.com/Scale%20Army%20Careers/a012"),
            ("ashby", "Scale Army Careers", "a012"),
        )

    def test_lever(self):
        self.assertEqual(
            audit_links.locator("https://jobs.lever.co/minders/1c6000c1-fe33-4ac8-b9ac-fb07c886f210"),
            ("lever", "minders", "1c6000c1-fe33-4ac8-b9ac-fb07c886f210"),
        )

    def test_greenhouse(self):
        self.assertEqual(
            audit_links.locator("https://job-boards.greenhouse.io/aircallioinc/jobs/4308976009"),
            ("greenhouse", "aircallioinc", "4308976009"),
        )

    def test_stripe_redirect(self):
        self.assertEqual(
            audit_links.locator("https://stripe.com/careers/listing/product-strategy-operations-apac/8081423?gh_jid=8081423"),
            ("greenhouse", "stripe", "8081423"),
        )


class AuditTests(unittest.TestCase):
    def test_closed_stays_closed_when_missing_first_time(self):
        with patch.object(audit_links, "request_json") as mock:
            audit_links.update({"id": "old", "metadata": {"availability_status": "closed"}}, False)
            self.assertEqual(mock.call_args[0][2]["metadata"]["availability_status"], "closed")

    def test_two_absences_close_posting(self):
        with patch.object(audit_links, "request_json") as mock:
            audit_links.update({"id": "old", "metadata": {"availability_status": "verified", "not_found_streak": 1}}, False)
            self.assertEqual(mock.call_args[0][2]["metadata"]["availability_status"], "closed")

    def test_found_restores_live_ats_posting(self):
        with patch.object(audit_links, "request_json") as mock:
            audit_links.update({"id": "old", "metadata": {"availability_status": "closed", "not_found_streak": 2}}, True)
            body = mock.call_args[0][2]
            self.assertEqual(body["metadata"]["availability_status"], "ats_listed")
            self.assertEqual(body["metadata"]["not_found_streak"], 0)


class GeoFilterTests(unittest.TestCase):
    base = {
        "id": "example", "url": "https://jobs.lever.co/test/one",
        "company": "Example", "title": "Strategy Lead",
        "description": "", "score": 70, "work_type": "remote",
    }

    def test_remote_usa_not_chile(self):
        self.assertIsNone(sync_supabase.normalize({**self.base, "location": "Remote - USA"}, "2026-11-09T00:00:00Z"))

    def test_remote_chile_explicit(self):
        value = sync_supabase.normalize({**self.base, "location": "Chile / Argentina"}, "2026-11-09T00:00:00Z")
        self.assertEqual(value["metadata"]["location_category"], "remote_chile")
        self.assertEqual(value["metadata"]["availability_status"], "ats_listed")

    def test_remote_latam_requires_country_confirmation(self):
        value = sync_supabase.normalize({**self.base, "location": "Latin America"}, "2026-11-09T00:00:00Z")
        self.assertEqual(value["metadata"]["location_category"], "unknown")
        self.assertEqual(value["metadata"]["geo_eligibility"], "needs_confirmation")


if __name__ == "__main__":
    unittest.main()
