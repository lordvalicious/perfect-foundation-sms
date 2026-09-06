"""Helpers for deriving codes/slugs from a school's name.

Entity codes (students / teachers / staff / school code) follow the pattern
``<NAME-PREFIX>-<TYPE>-<SEQUENCE>`` so that every ID visible to admins is
recognizably tied to the school that issued it.
"""

import re

_STOP_WORDS = {"THE", "OF", "AND", "FOR", "A", "AN", "AT", "IN", "ON", "TO", "BY"}


def school_name_prefix(name):
    """Derive a short uppercase prefix from a school name.

    'Perfect Foundation' -> 'PF'
    'Springfield Academy' -> 'SA'
    'Springfield' -> 'SPR'
    """
    words = [
        re.sub(r"[^A-Za-z]", "", w).upper()
        for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*", str(name or ""))
    ]
    words = [w for w in words if w]
    meaningful = [w for w in words if w not in _STOP_WORDS]
    words = meaningful or words

    if not words:
        return "SCH"

    if len(words) >= 2:
        prefix = "".join(w[0] for w in words[:3])
    else:
        prefix = words[0][:3]

    return prefix or "SCH"


def school_code_for_name(name, exclude_pk=None):
    """Return a unique School.code derived from the school's name.

    Falls back to the name prefix plus a numeric suffix when the prefix is
    already taken, and finally to a random code if even that collides.
    """
    from .models import School

    prefix = school_name_prefix(name)
    qs = School.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)

    candidate = prefix
    for _ in range(100):
        if not qs.filter(code=candidate).exists():
            return candidate
        candidate = f"{prefix}{len(candidate) - len(prefix) + 1}"

    return School.generate_random_code()


def next_entity_code(school, doc_type, model, field):
    """Generate the next sequential entity code for a school.

    Produces values like ``PF-ST-0001`` (students) or ``SA-EMP-0003``
    (teachers / staff). Sequence numbers are derived from existing codes
    sharing the same school prefix so deletions never reuse a number.
    """
    prefix = school_name_prefix(school.name if school is not None else "")
    base = f"{prefix}-{doc_type}-"

    count = model.objects.filter(**{f"{field}__startswith": base}).count() + 1
    while model.objects.filter(**{field: f"{base}{count:04d}"}).exists():
        count += 1

    return f"{base}{count:04d}"