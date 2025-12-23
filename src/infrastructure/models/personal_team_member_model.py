from sqlalchemy import ForeignKey, Column, DateTime, String
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from sqlalchemy.orm import relationship

class PersonalTeamStatus:
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'

class PersonalTeamMemberModel(PostgreSqlModel):

    __tablename__ = 'personal_team_members'
    __timestamp__ = True

    id = ColumnId()
    pilot_id = ColumnId(ForeignKey('access_profiles.profile_id'), nullable=False, unique=False)
    member_id = ColumnId(ForeignKey('access_profiles.profile_id'), nullable=False, unique=False)
    acceptance_status = Column(String, nullable=False, default='PENDING', server_default='PENDING', comment='PENDING, ACCEPTED, REJECTED')
    member_acceptance = Column(DateTime(timezone=True), nullable=True)
    member_rejection = Column(DateTime(timezone=True), nullable=True)

    pilot = relationship('AccessProfileModel',
                         foreign_keys=[pilot_id],
                         lazy='joined')

    member = relationship('AccessProfileModel',
                          foreign_keys=[member_id],
                          lazy='joined')
