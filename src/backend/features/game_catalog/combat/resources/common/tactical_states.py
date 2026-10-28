"""Conservative starting values. Balance acceptance is explicitly pending."""

TACTICAL_ENTRY = 0.25
TACTICAL_LOSS = 0.25
TACTICAL_INITIATIVE_SCALE = 50.0
TACTICAL_POLICIES = {
    "skill_two_handed": {"parry": 0.05},
    "skill_shield_mastery": {"anti_dodge": 0.05},
    "skill_dual_wield": {"crit": 0.05},
}
