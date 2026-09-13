import unittest

from app.schemas.application import (
    ApplicationCreate,
    ApplicationProviderName,
    ApplicationStatus,
    JobContext,
)
from app.services.applications.providers import (
    ApplicationProvider,
    DirectApplyProvider,
    ManualReviewProvider,
)
from app.services.applications.service import ApplicationService


def sample_payload() -> ApplicationCreate:
    return ApplicationCreate(
        candidate_id="cand_1",
        job_id="job_1",
        customized_cv_id="cv_custom_1",
        company="Empresa X",
        position="Backend Developer",
        job_url="https://example.com/jobs/1",
        match_percent=94,
        notes="No modificar el CV maestro.",
    )


class FailingProvider(ApplicationProvider):
    name = ApplicationProviderName.DIRECT_APPLY

    def can_handle(self, job: JobContext) -> bool:
        return True

    def submit(self, application):
        raise RuntimeError("Fallo controlado de prueba.")


class ApplicationEngineTests(unittest.TestCase):
    def test_create_application(self):
        service = ApplicationService()
        application = service.create(sample_payload())

        self.assertTrue(application.id)
        self.assertEqual(application.candidate_id, "cand_1")
        self.assertEqual(application.job_id, "job_1")
        self.assertEqual(application.customized_cv_id, "cv_custom_1")
        self.assertIsNone(application.submitted_at)

    def test_initial_status_is_cv_ready(self):
        service = ApplicationService()
        application = service.create(sample_payload())
        self.assertEqual(application.status, ApplicationStatus.CV_READY)

    def test_transition_ready_to_apply(self):
        service = ApplicationService()
        application = service.create(sample_payload())
        queued = service.enqueue(application.id)
        self.assertEqual(queued.status, ApplicationStatus.READY_TO_APPLY)

    def test_manual_review_provider_returns_review_required(self):
        service = ApplicationService()
        application = service.create(sample_payload())
        service.enqueue(application.id)
        processed = service.process(application.id)

        self.assertEqual(processed.status, ApplicationStatus.REVIEW_REQUIRED)
        self.assertEqual(
            processed.provider,
            ApplicationProviderName.MANUAL_REVIEW,
        )

        result = ManualReviewProvider().submit(processed)
        self.assertEqual(result.status, ApplicationStatus.REVIEW_REQUIRED)
        self.assertEqual(result.customized_cv_id, "cv_custom_1")
        self.assertEqual(
            result.notes,
            "No modificar el CV maestro.",
        )

        review = service.review(processed.id)
        self.assertIn("CV adaptado", review.message)
        self.assertEqual(review.company, "Empresa X")
        self.assertTrue(review.checklist)

    def test_provider_error_marks_application_failed(self):
        service = ApplicationService(
            providers=[FailingProvider(), ManualReviewProvider()]
        )
        application = service.create(sample_payload())
        service.enqueue(application.id)
        processed = service.process(application.id)

        self.assertEqual(processed.status, ApplicationStatus.FAILED)
        self.assertEqual(
            processed.error_message,
            "Fallo controlado de prueba.",
        )
        self.assertIsNone(processed.submitted_at)

    def test_application_keeps_traceability(self):
        service = ApplicationService()
        application = service.create_and_queue(sample_payload())

        self.assertEqual(application.candidate_id, "cand_1")
        self.assertEqual(application.job_id, "job_1")
        self.assertEqual(application.customized_cv_id, "cv_custom_1")
        self.assertEqual(
            application.provider,
            ApplicationProviderName.MANUAL_REVIEW,
        )
        self.assertIsNotNone(application.created_at)
        self.assertIsNotNone(application.updated_at)
        self.assertEqual(application.status, ApplicationStatus.REVIEW_REQUIRED)
        self.assertIsNone(application.submitted_at)
        self.assertIsNone(application.error_message)
        self.assertNotIn("experiencia", application.model_dump())

    def test_direct_apply_provider_is_contract_only(self):
        provider = DirectApplyProvider()
        job = JobContext(
            job_id="job_1",
            company="Empresa X",
            position="Backend Developer",
        )
        self.assertFalse(provider.can_handle(job))
        with self.assertRaises(NotImplementedError):
            provider.submit(service_application())


def service_application():
    return ApplicationService().create(sample_payload())


if __name__ == "__main__":
    unittest.main()
