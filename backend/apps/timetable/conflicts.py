"""Conflict scan for the timetable.

The model database constraints catch exact double-bookings
(year, resource, day, period). This module catches the remaining class:

- *overlapping periods* — two periods whose times overlap in wall-clock
  time (e.g. 08:00-08:45 and 08:30-09:15) booking the same teacher or
  section twice; and
- *room clashes* — the same room string used by two entries at the same
  time, on the same campus.

``find_conflicts`` groups entries by resource + day and reports every
overlapping pair, so admins can audit and fix a damaged timetable.
"""

from .models import periods_overlap


def _pair_overlaps(entries):
    """Yield (a, b) for every overlapping pair within a group."""
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a = entries[i]
            b = entries[j]
            if periods_overlap(a.period, b.period):
                yield a, b


def _fmt_time(period):
    return (
        f"{period.start_time:%H:%M}-{period.end_time:%H:%M}"
    )


def _describe(conflict_type, day, resource_id, resource, pair):
    a, b = pair
    return {
        "type": conflict_type,
        "day": day,
        "resource_id": resource_id,
        "resource": resource,
        "entry_ids": [a.id, b.id],
        "periods": [a.period.name, b.period.name],
        "times": [_fmt_time(a.period), _fmt_time(b.period)],
        "campus": a.campus.name,
        "classes": [
            f"{a.class_obj.name}/{a.section.name}",
            f"{b.class_obj.name}/{b.section.name}",
        ],
    }


def find_conflicts(academic_year=None, campus=None):
    """Scan timetable entries and return structured conflict records.

    Optional filters: ``academic_year`` (instance) and ``campus``
    (instance). Conflicts are scoped to the same academic year, campus,
    and day, so legacy cross-year timetables do not produce noise.
    """
    from .models import TimetableEntry

    queryset = (
        TimetableEntry.objects
        .select_related(
            "academic_year",
            "campus",
            "class_obj",
            "section",
            "period",
            "teacher",
        )
        .order_by("day", "period__number")
    )

    if academic_year is not None:
        queryset = queryset.filter(academic_year=academic_year)

    if campus is not None:
        queryset = queryset.filter(campus=campus)

    entries = list(queryset)

    groups = {}

    for entry in entries:
        if entry.teacher_id:
            key = (
                "teacher",
                entry.academic_year_id,
                entry.teacher_id,
                entry.day,
            )
            groups.setdefault(key, []).append(entry)

        if entry.section_id:
            key = (
                "section",
                entry.academic_year_id,
                entry.section_id,
                entry.day,
            )
            groups.setdefault(key, []).append(entry)

        room = (entry.room or "").strip().lower()

        if room:
            key = (
                "room",
                entry.academic_year_id,
                entry.campus_id,
                room,
                entry.day,
            )
            groups.setdefault(key, []).append(entry)

    conflicts = []

    for key, group in groups.items():
        conflict_type = key[0]

        for a, b in _pair_overlaps(group):
            if conflict_type == "teacher":
                resource_id = a.teacher_id
                resource = a.teacher.full_name
            elif conflict_type == "section":
                resource_id = a.section_id
                resource = (
                    f"{a.class_obj.name} - {a.section.name}"
                )
            else:
                resource_id = None
                resource = (a.room or "").strip()

            conflicts.append(
                _describe(
                    conflict_type,
                    a.day,
                    resource_id,
                    resource,
                    (a, b),
                )
            )

    conflicts.sort(
        key=lambda item: (item["type"], item["day"])
    )

    return conflicts