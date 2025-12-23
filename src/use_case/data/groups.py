from src.infrastructure.models import GroupModel

GROUP_PUBLIC = GroupModel(
    name="Public",
    description="The 'Public' user group in the PorscheCUP Brazil ARCS application "
                "is aimed at all spectators and motorsport enthusiasts "
                "who want to follow the news, results, and information about PorscheCUP Brasil events. "
                "Members of this group have access to the application in both mobile and web versions, "
                "being able to view exclusive content, access information about drivers, teams and race calendar, "
                "in addition to monitoring live broadcasts and real-time data during events. "
                "This access allows the public to stay up to date and engaged with everything happening in the PorscheCUP world, "
                "with an interactive and accessible experience.",
    image=None,
    meta_data={}
)

GROUP_PILOT = GroupModel(
    name="Pilot",
    description="The 'Pilot' group grants pilots exclusive access to their performance metrics, "
                "training schedules, and personalized race analytics. Through this group, pilots can "
                "view private insights, race telemetry, and manage their profiles, allowing them to stay informed "
                "and prepared for upcoming events and competitions within PorscheCUP Brasil.",
    image=None,
    meta_data={}
)

GROUP_ENGINEERING_MANAGEMENT = GroupModel(
    name="Engineering Management",
    description="The 'Engineering Management' group provides access for engineers and technical staff "
                "to vehicle telemetry, configuration settings, and diagnostics. This group enables users "
                "to manage technical parameters, analyze real-time performance data, and support drivers with insights "
                "to optimize race strategies and car setups in PorscheCUP Brasil events.",
    image=None,
    meta_data={}
)

GROUP_GUESTS = GroupModel(
    name="Guests",
    description="The 'Guests' group is designed for VIP members, sponsors, and event invitees, allowing them "
                "exclusive access to race-related events, hospitality services, and additional insights into the "
                "race activities. Members in this group can access a dedicated interface with event schedules, special content, "
                "and private viewing areas within the application.",
    image=None,
    meta_data={}
)

GROUP_ADMINISTRATIVE = GroupModel(
    name="Administrative",
    description="The 'Administrative' group is responsible for users who handle organizational tasks, "
                "such as managing user permissions, coordinating events, and handling logistical aspects of PorscheCUP Brasil. "
                "This group grants access to user management, event scheduling, and administrative dashboards for efficient "
                "event coordination and resource allocation.",
    image=None,
    meta_data={}
)

GROUP_OPERATIONS = GroupModel(
    name="Operations",
    description="The 'Operations' group includes personnel responsible for event logistics, track setup, "
                "and real-time operational tasks. Users in this group can monitor live event data, manage track resources, "
                "and ensure safety protocols are followed during PorscheCUP Brasil events. This group is essential for "
                "maintaining smooth operations throughout each race event.",
    image=None,
    meta_data={}
)
