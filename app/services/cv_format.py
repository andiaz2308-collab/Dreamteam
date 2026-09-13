from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobProfile
from app.schemas.optimization import CustomizedCV


def render_cleaned_cv(profile: CandidateProfile) -> str:
    lines: list[str] = [profile.name]
    if profile.headline:
        lines.append(profile.headline)

    contact = [
        item
        for item in [profile.location, profile.email, profile.phone]
        if item
    ]
    if contact:
        lines.append(" · ".join(str(item) for item in contact))

    if profile.summary:
        lines.extend(["", "Perfil", profile.summary])

    if profile.experience:
        lines.extend(["", "Experiencia"])
        for item in profile.experience:
            title = " · ".join(
                part for part in [item.position, item.company] if part
            )
            dates = " – ".join(
                part
                for part in [
                    item.start_date,
                    item.end_date or ("Actual" if item.current else None),
                ]
                if part
            )
            if title:
                lines.append(title)
            if dates:
                lines.append(dates)
            if item.description:
                lines.append(item.description)

    if profile.education:
        lines.extend(["", "Educación"])
        for item in profile.education:
            lines.append(
                " · ".join(
                    part
                    for part in [item.degree, item.field, item.institution]
                    if part
                )
            )

    if profile.skills:
        lines.extend(["", "Habilidades", ", ".join(profile.skills)])

    if profile.languages:
        lines.extend(["", "Idiomas"])
        for item in profile.languages:
            lines.append(
                " · ".join(part for part in [item.language, item.level] if part)
            )

    if profile.certifications:
        lines.extend(["", "Certificaciones"])
        for item in profile.certifications:
            lines.append(
                " · ".join(
                    part for part in [item.name, item.institution, item.date] if part
                )
            )

    if profile.projects:
        lines.extend(["", "Proyectos"])
        for item in profile.projects:
            line = item.name
            if item.description:
                line = f"{line}: {item.description}"
            lines.append(line)

    return "\n".join(lines).strip()


def render_customized_cv(
    profile: CandidateProfile,
    customized: CustomizedCV,
    job: JobProfile,
) -> str:
    """CV listo para postular: mismos datos reales, reordenados para la oferta."""
    lines: list[str] = [profile.name]

    headline = customized.headline or profile.headline
    if headline:
        lines.append(headline)

    contact = [
        item
        for item in [profile.location, profile.email, profile.phone]
        if item
    ]
    if contact:
        lines.append(" · ".join(str(item) for item in contact))

    lines.extend(
        [
            "",
            f"Postulación: {job.title} — {job.company}",
        ]
    )

    if customized.summary:
        lines.extend(["", "Perfil profesional", customized.summary])

    if customized.emphasize:
        lines.extend(
            [
                "",
                "Competencias alineadas a la oferta",
                ", ".join(customized.emphasize),
            ]
        )

    if customized.experience:
        lines.extend(["", "Experiencia"])
        lines.extend(customized.experience)

    if profile.education:
        lines.extend(["", "Educación"])
        for item in profile.education:
            lines.append(
                " · ".join(
                    part
                    for part in [item.degree, item.field, item.institution]
                    if part
                )
            )

    if customized.skills:
        lines.extend(["", "Habilidades", ", ".join(customized.skills)])

    if profile.languages:
        lines.extend(["", "Idiomas"])
        for item in profile.languages:
            lines.append(
                " · ".join(part for part in [item.language, item.level] if part)
            )

    if profile.certifications:
        lines.extend(["", "Certificaciones"])
        for item in profile.certifications:
            lines.append(
                " · ".join(
                    part for part in [item.name, item.institution, item.date] if part
                )
            )

    if profile.projects:
        lines.extend(["", "Proyectos"])
        for item in profile.projects:
            line = item.name
            if item.description:
                line = f"{line}: {item.description}"
            lines.append(line)

    lines.extend(
        [
            "",
            "Nota: CV adaptado a partir del CV maestro. No se inventaron datos.",
        ]
    )
    return "\n".join(lines).strip()
