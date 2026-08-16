from app.schemas.candidate import (
    CandidateProfile,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    LanguageItem,
    ProjectItem,
)
from app.schemas.job import JobProfile


DEMO_PROFILE = CandidateProfile(
    id="candidate_andreina",
    name="Andreina Díaz Durán",
    headline="Bióloga",
    email=None,
    phone=None,
    location="Colombia",
    summary=(
        "Bióloga con experiencia en trabajo de campo, laboratorio y "
        "análisis de información ambiental. Interés en biodiversidad, "
        "calidad de agua y conservación."
    ),
    experience=[
        ExperienceItem(
            company="Grupo de investigación en biodiversidad",
            position="Asistente de investigación",
            start_date="2023",
            end_date=None,
            current=True,
            description=(
                "Apoyo en muestreo de campo, registro de especies y "
                "organización de datos biológicos."
            ),
            skills=["Muestreo de campo", "Biodiversidad", "Excel"],
        ),
        ExperienceItem(
            company="Laboratorio de microbiología",
            position="Practicante de laboratorio",
            start_date="2022",
            end_date="2023",
            current=False,
            description=(
                "Preparación de medios, manejo básico de muestras y "
                "registro de resultados bajo protocolos de bioseguridad."
            ),
            skills=["Microbiología", "Bioseguridad", "Laboratorio"],
        ),
    ],
    education=[
        EducationItem(
            institution="Universidad",
            degree="Bióloga",
            field="Biología",
            start_date="2018",
            end_date="2023",
        )
    ],
    skills=[
        "Biología",
        "Muestreo de campo",
        "Microbiología",
        "Biodiversidad",
        "Calidad de agua",
        "Excel",
        "R",
        "SIG",
        "Redacción científica",
        "Bioseguridad",
    ],
    soft_skills=["Trabajo en equipo", "Observación", "Comunicación escrita"],
    languages=[
        LanguageItem(language="Español", level="Nativo"),
        LanguageItem(language="Inglés", level="Intermedio"),
    ],
    certifications=[
        CertificationItem(
            name="Bioseguridad en laboratorio",
            institution="Formación interna",
            date="2023",
        )
    ],
    projects=[
        ProjectItem(
            name="Monitoreo de calidad de agua",
            description="Registro de parámetros básicos y apoyo en informe técnico.",
            technologies=["Excel", "R"],
        )
    ],
    achievements=[
        "Participación en jornadas de muestreo y sistematización de datos de campo."
    ],
    source="demo",
)


DEMO_JOBS = [
    JobProfile(
        id="job_lab_ambiental",
        title="Analista de laboratorio ambiental",
        company="HidroAndes",
        location="Colombia",
        modality="Presencial",
        seniority="Junior",
        required_skills=["Laboratorio", "Calidad de agua", "Bioseguridad", "Excel"],
        preferred_skills=["Microbiología", "R"],
        education="Biología o afines",
        experience_requirements="Experiencia en laboratorio o prácticas",
        languages=["Español"],
        keywords=["laboratorio", "agua", "muestras"],
        responsibilities=[
            "Procesar muestras ambientales",
            "Registrar resultados",
            "Seguir protocolos de bioseguridad",
        ],
        source="demo",
    ),
    JobProfile(
        id="job_biodiversidad",
        title="Investigadora junior en biodiversidad",
        company="Fundación Bosque Vivo",
        location="Colombia",
        modality="Campo / híbrido",
        seniority="Junior",
        required_skills=["Biodiversidad", "Muestreo de campo", "Redacción científica"],
        preferred_skills=["SIG", "R"],
        education="Biología",
        experience_requirements="Trabajo de campo",
        languages=["Español", "Inglés"],
        keywords=["biodiversidad", "campo", "especies"],
        responsibilities=[
            "Apoyar muestreos",
            "Organizar datos biológicos",
            "Contribuir a informes",
        ],
        source="demo",
    ),
    JobProfile(
        id="job_educacion_ambiental",
        title="Profesional de educación ambiental",
        company="Aula Verde",
        location="Colombia",
        modality="Híbrido",
        seniority="Junior",
        required_skills=["Comunicación escrita", "Biología", "Trabajo en equipo"],
        preferred_skills=["Educación ambiental", "SIG"],
        education="Biología o educación ambiental",
        experience_requirements="Interés en divulgación científica",
        languages=["Español"],
        keywords=["educación", "divulgación"],
        responsibilities=[
            "Preparar contenidos de divulgación",
            "Acompañar actividades con comunidad",
        ],
        source="demo",
    ),
]
