"""Provisional independent pool budgets; no claim of combat balance."""

from ..contracts import MonsterAssemblyProfileDTO


def profiles():
    result = {}
    senior_bases = {"ordinary": (0, 0, 0), "patrol": (23, 46, 69), "guard": (30, 53, 76), "leader": (45, 68, 98)}
    senior_caps = {"ordinary": (0, 0, 0), "patrol": (23, 23, 23), "guard": (23, 30, 30), "leader": (23, 30, 30)}
    increments = {"ordinary": (0, 0, 0), "patrol": (5, 8, 10), "guard": (7, 10, 15), "leader": (10, 20, 30)}
    for kind in senior_bases:
        result[kind] = {}
        for i, difficulty in enumerate(("easy", "normal", "hard")):
            roles = [{"role": "minion", "min_count": 0, "max_count": 8}]
            if kind != "ordinary":
                roles.append({"role": "veteran", "min_count": int(kind == "patrol"), "max_count": 3})
            if kind in ("guard", "leader"):
                roles.append(
                    {"role": "elite", "min_count": int(kind == "guard"), "max_count": 2 if difficulty == "hard" else 1}
                )
            if kind == "leader":
                roles.append({"role": "boss", "min_count": 1, "max_count": 1})
            result[kind][difficulty] = MonsterAssemblyProfileDTO.model_validate(
                {
                    "id": f"solo.{kind}.{difficulty}",
                    "minions": {
                        "base_points": (30, 45, 60)[i] if kind == "ordinary" else 30,
                        "gs_bonus_max": (9, 15, 21)[i] if kind == "ordinary" else 0,
                        "gs_points_per_step": (3, 5, 7)[i] if kind == "ordinary" else 0,
                    },
                    "seniors": {
                        "base_points": senior_bases[kind][i],
                        "gs_bonus_max": senior_caps[kind][i],
                        "gs_points_per_step": increments[kind][i],
                    },
                    "roles": roles,
                }
            )
    return result
