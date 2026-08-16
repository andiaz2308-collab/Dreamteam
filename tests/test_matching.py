import unittest

from app.services.demo import DEMO_JOBS, DEMO_PROFILE
from app.services.matching.job_matcher import match_profile_to_job
from app.services.optimization.cv_optimizer import build_customized_cv, build_plan


class MatchingTests(unittest.TestCase):
    def test_andreina_matches_lab_job(self):
        job = next(item for item in DEMO_JOBS if item.id == "job_lab_ambiental")
        match = match_profile_to_job(DEMO_PROFILE, job)
        self.assertGreaterEqual(match.score, 70)
        matched_labels = {item.label for item in match.matched}
        self.assertTrue({"Laboratorio", "Excel"} & matched_labels or match.matched)

    def test_missing_skill_is_never_matched(self):
        job = next(item for item in DEMO_JOBS if item.id == "job_lab_ambiental")
        job = job.model_copy(deep=True)
        job.required_skills = ["Laboratorio", "Kubernetes"]
        match = match_profile_to_job(DEMO_PROFILE, job)
        missing = {item.label for item in match.missing}
        matched = {item.label for item in match.matched}
        self.assertIn("Kubernetes", missing)
        self.assertNotIn("Kubernetes", matched)

    def test_customized_cv_does_not_invent(self):
        job = next(item for item in DEMO_JOBS if item.id == "job_biodiversidad")
        match = match_profile_to_job(DEMO_PROFILE, job)
        plan = build_plan(DEMO_PROFILE, job, match)
        customized = build_customized_cv(DEMO_PROFILE, job, plan, "cv_test")
        self.assertFalse(customized.invented)
        self.assertIn("CV maestro", customized.notes)
        self.assertTrue(
            any("biodiversidad" in line.lower() or "campo" in line.lower()
                for line in customized.experience)
        )


if __name__ == "__main__":
    unittest.main()
