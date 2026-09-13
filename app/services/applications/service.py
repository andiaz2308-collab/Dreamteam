from collections import deque
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.application import (
    Application,
    ApplicationCreate,
    ApplicationProviderName,
    ApplicationReview,
    ApplicationStats,
    ApplicationStatus,
    JobContext,
)
from app.services.applications.providers import (
    ApplicationProvider,
    DirectApplyProvider,
    ManualReviewProvider,
)


ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: {
        ApplicationStatus.ANALYZING,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.ANALYZING: {
        ApplicationStatus.MATCHED,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.MATCHED: {
        ApplicationStatus.CV_READY,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.CV_READY: {
        ApplicationStatus.READY_TO_APPLY,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.READY_TO_APPLY: {
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.REVIEW_REQUIRED,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.FAILED: {
        ApplicationStatus.READY_TO_APPLY,
    },
    ApplicationStatus.REVIEW_REQUIRED: {
        ApplicationStatus.READY_TO_APPLY,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.SUBMITTED: set(),
}


class ApplicationStore:
    def __init__(self) -> None:
        self._items: dict[str, Application] = {}

    def add(self, application: Application) -> Application:
        self._items[application.id] = application
        return application

    def get(self, application_id: str) -> Application | None:
        return self._items.get(application_id)

    def list(self) -> list[Application]:
        return sorted(
            self._items.values(),
            key=lambda item: item.created_at,
            reverse=True,
        )

    def update(self, application: Application) -> Application:
        self._items[application.id] = application
        return application


class ApplicationQueue:
    def __init__(self) -> None:
        self._items: deque[str] = deque()

    def enqueue(self, application_id: str) -> None:
        if application_id not in self._items:
            self._items.append(application_id)

    def dequeue(self) -> str | None:
        if not self._items:
            return None
        return self._items.popleft()

    def remove(self, application_id: str) -> None:
        self._items = deque(
            item for item in self._items if item != application_id
        )


class ApplicationError(Exception):
    pass


class ApplicationService:
    def __init__(
        self,
        store: ApplicationStore | None = None,
        queue: ApplicationQueue | None = None,
        providers: list[ApplicationProvider] | None = None,
    ) -> None:
        self.store = store or ApplicationStore()
        self.queue = queue or ApplicationQueue()
        self.providers = providers or [
            DirectApplyProvider(),
            ManualReviewProvider(),
        ]

    def create(self, payload: ApplicationCreate) -> Application:
        now = datetime.now(timezone.utc)
        application = Application(
            id=str(uuid4()),
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            customized_cv_id=payload.customized_cv_id,
            provider=None,
            status=ApplicationStatus.CV_READY,
            created_at=now,
            updated_at=now,
            submitted_at=None,
            error_message=None,
            notes=payload.notes,
            company=payload.company,
            position=payload.position,
            job_url=payload.job_url,
            match_percent=payload.match_percent,
            cover_letter_id=payload.cover_letter_id,
            answers=list(payload.answers),
        )
        return self.store.add(application)

    def enqueue(self, application_id: str) -> Application:
        application = self._require(application_id)
        self._transition(application, ApplicationStatus.READY_TO_APPLY)
        self.queue.enqueue(application.id)
        return application

    def process(self, application_id: str) -> Application:
        application = self._require(application_id)
        self.queue.remove(application_id)

        if application.status != ApplicationStatus.READY_TO_APPLY:
            self._transition(application, ApplicationStatus.READY_TO_APPLY)

        job = JobContext(
            job_id=application.job_id,
            company=application.company,
            position=application.position,
            url=application.job_url,
            match_percent=application.match_percent,
        )
        provider = self._select_provider(job)
        application.provider = provider.name

        try:
            result = provider.submit(application)
            application.status = result.status
            application.notes = result.notes
            application.error_message = result.error_message
            application.updated_at = datetime.now(timezone.utc)
            if result.status == ApplicationStatus.SUBMITTED:
                application.submitted_at = application.updated_at
        except Exception as exc:
            application.status = ApplicationStatus.FAILED
            application.error_message = str(exc)
            application.updated_at = datetime.now(timezone.utc)

        return self.store.update(application)

    def create_and_queue(self, payload: ApplicationCreate) -> Application:
        application = self.create(payload)
        self.enqueue(application.id)
        return self.process(application.id)

    def retry(self, application_id: str) -> Application:
        application = self._require(application_id)
        if application.status != ApplicationStatus.FAILED:
            raise ApplicationError(
                "Solo se pueden reintentar postulaciones en estado FAILED."
            )
        application.error_message = None
        self._transition(application, ApplicationStatus.READY_TO_APPLY)
        self.queue.enqueue(application.id)
        return self.process(application.id)

    def review(self, application_id: str) -> ApplicationReview:
        application = self._require(application_id)
        if application.status != ApplicationStatus.REVIEW_REQUIRED:
            raise ApplicationError(
                "Esta postulación no está lista para revisión."
            )

        adapted_cv_text = None
        try:
            from app.services.workspace import workspace

            customized = workspace.customized.get(application.customized_cv_id)
            if customized is not None:
                adapted_cv_text = customized.rendered_text
        except Exception:
            adapted_cv_text = None

        checklist = [
            "Revisa el CV adaptado antes de enviar.",
            "Copia o descarga el texto del CV.",
            "Postula manualmente en la URL de la oferta.",
            "El CV maestro no fue modificado.",
        ]
        if application.job_url:
            checklist.insert(2, f"Abrir oferta: {application.job_url}")

        return ApplicationReview(
            message=(
                "Paquete de postulación listo. Usa el CV adaptado "
                "para aplicar de forma manual."
            ),
            status=application.status,
            job_url=application.job_url,
            company=application.company,
            position=application.position,
            customized_cv_id=application.customized_cv_id,
            cover_letter_id=application.cover_letter_id,
            answers=list(application.answers),
            notes=application.notes,
            adapted_cv_text=adapted_cv_text,
            checklist=checklist,
        )

    def list(self) -> list[Application]:
        return self.store.list()

    def get(self, application_id: str) -> Application:
        return self._require(application_id)

    def stats(self) -> ApplicationStats:
        items = self.store.list()
        return ApplicationStats(
            jobs_analyzed=sum(
                1
                for item in items
                if item.status != ApplicationStatus.DISCOVERED
            ),
            matches=sum(
                1
                for item in items
                if item.status
                in {
                    ApplicationStatus.MATCHED,
                    ApplicationStatus.CV_READY,
                    ApplicationStatus.READY_TO_APPLY,
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.REVIEW_REQUIRED,
                }
            ),
            cvs_ready=sum(
                1
                for item in items
                if item.status
                in {
                    ApplicationStatus.CV_READY,
                    ApplicationStatus.READY_TO_APPLY,
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.REVIEW_REQUIRED,
                }
            ),
            ready_to_apply=sum(
                1
                for item in items
                if item.status == ApplicationStatus.READY_TO_APPLY
            ),
            submitted=sum(
                1
                for item in items
                if item.status == ApplicationStatus.SUBMITTED
            ),
            review_required=sum(
                1
                for item in items
                if item.status == ApplicationStatus.REVIEW_REQUIRED
            ),
        )

    def seed_demo(self) -> None:
        if self.store.list():
            return

        self.create_and_queue(
            ApplicationCreate(
                candidate_id="candidate_andreina",
                job_id="job_lab_ambiental",
                customized_cv_id="cv_custom_hidroandes",
                company="HidroAndes",
                position="Analista de laboratorio ambiental",
                job_url="https://example.com/jobs/laboratorio-ambiental",
                match_percent=88,
                notes="CV maestro intacto. Versión adaptada referenciada por ID.",
            )
        )
        self._insert_demo(
            company="Fundación Bosque Vivo",
            position="Investigadora junior en biodiversidad",
            status=ApplicationStatus.CV_READY,
            match_percent=82,
        )
        self._insert_demo(
            company="Aula Verde",
            position="Profesional de educación ambiental",
            status=ApplicationStatus.ANALYZING,
            match_percent=70,
        )
        self._insert_demo(
            company="Reserva El Roble",
            position="Asistente de monitoreo",
            status=ApplicationStatus.DISCOVERED,
            match_percent=76,
        )
        self._insert_demo(
            company="Lab Costa",
            position="Técnica de laboratorio",
            status=ApplicationStatus.SUBMITTED,
            match_percent=80,
            provider=ApplicationProviderName.MANUAL_REVIEW,
        )
        self._insert_demo(
            company="AquaDatos",
            position="Analista de datos ambientales",
            status=ApplicationStatus.FAILED,
            match_percent=64,
            error_message="La plataforma no tiene integración permitida.",
        )

    def _insert_demo(
        self,
        *,
        company: str,
        position: str,
        status: ApplicationStatus,
        match_percent: int,
        provider: ApplicationProviderName | None = None,
        error_message: str | None = None,
    ) -> Application:
        now = datetime.now(timezone.utc)
        application = Application(
            id=str(uuid4()),
            candidate_id="candidate_andreina",
            job_id=f"job_{company.lower().replace(' ', '_')}",
            customized_cv_id=f"cv_custom_{company.lower().replace(' ', '_')}",
            provider=provider,
            status=status,
            created_at=now,
            updated_at=now,
            submitted_at=(
                now if status == ApplicationStatus.SUBMITTED else None
            ),
            error_message=error_message,
            notes=None,
            company=company,
            position=position,
            job_url=None,
            match_percent=match_percent,
        )
        return self.store.add(application)

    def _select_provider(self, job: JobContext) -> ApplicationProvider:
        for provider in self.providers:
            if provider.can_handle(job):
                return provider
        raise ApplicationError(
            "No hay un provider disponible para esta oferta."
        )

    def _require(self, application_id: str) -> Application:
        application = self.store.get(application_id)
        if application is None:
            raise ApplicationError("La postulación no existe.")
        return application

    def _transition(
        self,
        application: Application,
        new_status: ApplicationStatus,
    ) -> None:
        if application.status == new_status:
            application.updated_at = datetime.now(timezone.utc)
            self.store.update(application)
            return

        allowed = ALLOWED_TRANSITIONS.get(application.status, set())
        if new_status not in allowed:
            raise ApplicationError(
                f"No se puede pasar de {application.status.value} "
                f"a {new_status.value}."
            )
        application.status = new_status
        application.updated_at = datetime.now(timezone.utc)
        self.store.update(application)
