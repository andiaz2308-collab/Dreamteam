from io import BytesIO

from app.services.cv_docx import build_customized_cv_docx, docx_download_name, safe_filename
from app.services.demo import DEMO_JOBS, DEMO_PROFILE
from app.services.matching.job_matcher import match_profile_to_job
from app.services.optimization.cv_optimizer import build_customized_cv, build_plan


def test_safe_filename_strips_bad_chars():
    assert "Empresa_X" in safe_filename("Empresa X!!!")
    assert safe_filename("") == "CV_adaptado"


def test_build_customized_cv_docx_is_valid_zip():
    job = next(item for item in DEMO_JOBS if item.id == "job_biodiversidad")
    match = match_profile_to_job(DEMO_PROFILE, job)
    plan = build_plan(DEMO_PROFILE, job, match)
    customized = build_customized_cv(DEMO_PROFILE, job, plan, "cv_docx_test")

    payload = build_customized_cv_docx(DEMO_PROFILE, customized, job)
    assert payload.startswith(b"PK")
    assert len(payload) > 1000
    assert docx_download_name(job, DEMO_PROFILE).endswith(".docx")

    # python-docx can reopen it
    from docx import Document

    document = Document(BytesIO(payload))
    text = "\n".join(p.text for p in document.paragraphs)
    assert DEMO_PROFILE.name in text
    assert job.company in text
