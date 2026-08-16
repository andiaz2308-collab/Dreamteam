from abc import ABC, abstractmethod

from app.schemas.application import (
    Application,
    ApplicationProviderName,
    ApplicationStatus,
    JobContext,
    ProviderResult,
)


class ApplicationProvider(ABC):
    name: ApplicationProviderName

    @abstractmethod
    def can_handle(self, job: JobContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def submit(self, application: Application) -> ProviderResult:
        raise NotImplementedError


class DirectApplyProvider(ApplicationProvider):
    """Contrato para integraciones permitidas. Sin llamadas externas todavía."""

    name = ApplicationProviderName.DIRECT_APPLY

    def can_handle(self, job: JobContext) -> bool:
        return False

    def submit(self, application: Application) -> ProviderResult:
        raise NotImplementedError(
            "No hay integración directa habilitada para esta oferta."
        )


class ManualReviewProvider(ApplicationProvider):
    name = ApplicationProviderName.MANUAL_REVIEW

    def can_handle(self, job: JobContext) -> bool:
        return True

    def submit(self, application: Application) -> ProviderResult:
        return ProviderResult(
            status=ApplicationStatus.REVIEW_REQUIRED,
            provider=self.name,
            job_url=application.job_url,
            company=application.company,
            position=application.position,
            customized_cv_id=application.customized_cv_id,
            cover_letter_id=application.cover_letter_id,
            answers=list(application.answers),
            notes=(
                application.notes
                or "Esta postulación está lista para revisión."
            ),
        )
