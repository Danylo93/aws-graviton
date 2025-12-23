from src.infrastructure.models import SubGroupModel

# Subgrupos para o Grupo Público
SUBGROUP_PUBLIC_USER = SubGroupModel(
    name="Public User",
    description="The Public User subgroup belongs to the Public group. "
                "Defines the level of permission and access to resources/services "
                "on the PorscheCUP Brazil ARCS platform for general spectators.",
    permissions={},
    group_id=None
)


# Subgrupos para o Grupo de Pilotos
SUBGROUP_PILOT_MAIN = SubGroupModel(
    name="Pilot Main",
    description="The Pilot Main subgroup belongs to the Pilot group. "
                "This level allows primary pilots to access all driver-related resources "
                "on the PorscheCUP Brazil ARCS platform.",
    permissions={},
    group_id=None
)

SUBGROUP_PILOT_COACH = SubGroupModel(
    name="Pilot Coach",
    description="The Pilot Coach subgroup belongs to the Pilot group. "
                "Grants higher permissions for the lead pilot responsible for team management and coordination.",
    permissions={},
    group_id=None
)

SUBGROUP_PILOT_GUEST = SubGroupModel(
    name="Pilot Guest",
    description="The Pilot Guest subgroup belongs to the Pilot group. "
                "Designed for co-drivers and assistant pilots with limited access to team resources and data.",
    permissions={},
    group_id=None
)

SUBGROUP_PILOT_ADVISOR = SubGroupModel(
    name="Pilot Adivisor",
    description="The Pilot Secondary subgroup belongs to the Pilot group. "
                "Designed for co-drivers and assistant pilots with limited access to team resources and data.",
    permissions={},
    group_id=None
)

# Subgrupos para o Grupo de Gestão de Engenharia
SUBGROUP_ENGINEERING_TEAM_LEADER = SubGroupModel(
    name="Engineering Team Leader",
    description="The Engineering Team Leader subgroup belongs to the Engineering Management group. "
                "Allows the lead engineer to oversee technical staff and manage engineering strategies.",
    permissions={},
    group_id=None
)

SUBGROUP_ENGINEERING_PRIMARY = SubGroupModel(
    name="Engineering Primary",
    description="The Engineering Primary subgroup belongs to the Engineering Management group. "
                "Gives engineers full access to telemetry, diagnostics, and real-time analytics.",
    permissions={},
    group_id=None
)


SUBGROUP_ENGINEERING_SECONDARY = SubGroupModel(
    name="Engineering Secondary",
    description="The Engineering Secondary subgroup belongs to the Engineering Management group. "
                "Provides restricted access for junior engineers or technical assistants.",
    permissions={},
    group_id=None
)

# Subgrupos para o Grupo de Convidados
SUBGROUP_GUEST = SubGroupModel(
    name="Guest Secondary",
    description="The Guest Secondary subgroup belongs to the Guests group. "
                "Grants limited access for event participants with basic privileges.",
    permissions={},
    group_id=None
)

# Subgrupos para o Grupo Administrativo
SUBGROUP_ADMIN_TEAM_LEADER = SubGroupModel(
    name="Admin Team Leader",
    description="The Admin Team Leader subgroup belongs to the Administrative group. "
                "Provides primary administrative users access to the full suite of management tools.",
    permissions={},
    group_id=None
)

SUBGROUP_ADMIN_PRIMARY = SubGroupModel(
    name="Admin Primary",
    description="The Admin Primary subgroup belongs to the Administrative group. "
                "Grants elevated privileges for team leads to oversee and assign administrative tasks.",
    permissions={},
    group_id=None
)

SUBGROUP_ADMIN_SECONDARY = SubGroupModel(
    name="Admin Secondary",
    description="The Admin Secondary subgroup belongs to the Administrative group. "
                "Designed for assistant administrators with restricted access to management tools.",
    permissions={},
    group_id=None
)

# Subgrupos para o Grupo de Operações
SUBGROUP_OPERATIONS_TEAM_LEADER = SubGroupModel(
    name="Operations Team Leader",
    description="The Operations Main subgroup belongs to the Operations group. "
                "Allows primary operational staff access to all event management resources.",
    permissions={},
    group_id=None
)

SUBGROUP_OPERATIONS_PRIMARY = SubGroupModel(
    name="Operations Primary",
    description="The Operations Team Leader subgroup belongs to the Operations group. "
                "Grants oversight capabilities for leaders managing event logistics.",
    permissions={},
    group_id=None
)

SUBGROUP_OPERATIONS_SECONDARY = SubGroupModel(
    name="Operations Secondary",
    description="The Operations Secondary subgroup belongs to the Operations group. "
                "Provides limited access for supporting staff with a focus on operational tasks.",
    permissions={},
    group_id=None
)
