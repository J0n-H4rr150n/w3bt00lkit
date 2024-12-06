"""__init__.py"""
import hashlib
from typing import Any
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, BigInteger, Column, DateTime, ForeignKey, func, Index, Integer, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import _RelationshipDeclared
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()
# CONNECTION_OPTION = 'sqlite'
CONNECTION_OPTION = 'postgres'


class ChecklistModel(Base): # pylint: disable=R0903
    """ChecklistModel."""
    __tablename__: str = 'checklist'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    checklist_version = Column(String)
    category = Column(String)
    category_id = Column(String)
    category_order = Column(Integer)
    item_id = Column(String, unique=True)
    item_name = Column(String)
    objectives = Column(String)
    useful_tools = Column(String)
    link = Column(String)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    Index('ux_name_version_item', name, checklist_version, item_id, unique=True)

class ProxyModel(Base): # pylint: disable=R0903
    """ProxyModel."""
    __tablename__: str = 'proxy'

    id = Column(Integer, primary_key=True)
    target_id = Column(Integer)
    name = Column(String)
    action = Column(String)
    request = Column(String)
    host = Column(String)
    port = Column(Integer)
    method = Column(String)
    scheme = Column(String)
    authority = Column(String)
    path = Column(String)
    headers = Column(String)
    content = Column(String)
    response_status_code = Column(Integer)
    response_reason = Column(String)
    response_headers = Column(String)
    response_text = Column(String)
    timestamp_start = Column(BigInteger)
    timestamp_end = Column(BigInteger)
    full_url = Column(String)
    parsed_full_url = Column(String)
    parsed_path = Column(String)
    parsed_url =  Column(String)
    raw_request = Column(String)
    raw_response = Column(String)
    decoded_content = Column(String)
    flow = Column(String)
    dynamic_host = Column(String)
    dynamic_full_url = Column(String)
    note = Column(String)
    favorite_ind = Column(Boolean)
    params_ind = Column(Boolean)
    comments_ind = Column(Boolean)
    interesting_ind = Column(Boolean)
    needs_testing_ind = Column(Boolean)
    finding_ind = Column(Boolean)
    finding_note = Column(String)
    finding_category = Column(String)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)

class SynackTargetModel(Base): # pylint: disable=R0903
    """SynackTargetModel."""
    __tablename__: str = 'synacktarget'

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String, unique=True, index=True)
    target_name = Column(String)
    target_type = Column(String)
    auth_ind = Column(Boolean)
    creds_ind = Column(Boolean)
    note = Column(String)
    settings = Column(String)
    active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)

class SynackMissionModel(Base): # pylint: disable=R0903
    """SynackMissionModel."""
    __tablename__: str = 'synackmission'

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String)
    target_name = Column(String)
    note = Column(String)
    active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)


class TargetModel(Base): # pylint: disable=R0903
    """TargetModel."""
    __tablename__: str = 'target'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    platform = Column(String)
    active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)

class TargetScopeModel(Base): # pylint: disable=R0903
    """TargetScopeModel."""
    __tablename__: str = 'targetscope'

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey('target.id'), index=True)
    fqdn = Column(String)
    path = Column(String)
    wildcard_ind = Column(Boolean)
    in_scope_ind = Column(Boolean)
    out_of_scope_ind = Column(Boolean)
    active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)

    Index('ux_target_id_fqdn_path', target_id, fqdn, path, unique=True)

class TargetNoteModel(Base): # pylint: disable=R0903
    """TargetNoteModel."""
    __tablename__: str = 'targetnote'

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey('target.id'), index=True)
    title = Column(String)
    summary = Column(String)
    short_note = Column(String)
    full_note = Column(String)
    fqdn = Column(String)
    path = Column(String)
    url = Column(String)
    page = Column(String)
    checklist_item_id = Column(String)
    active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)


class VulnerabilityModel(Base):
    """VulnerabilityModel."""
    __tablename__ = 'vulnerability'

    id = Column(Integer, primary_key=True)
    vuln_category_id = Column(String, unique=True)
    parent_category_id = Column(String)
    category_name = Column(String)
    category_acronym = Column(String)
    cwe_id = Column(String)
    cwe_name = Column(String)
    cwe_link = Column(String)
    capec_id = Column(String)
    capec_name = Column(String)
    capec_link = Column(String)
    kev_link = Column(String)

    if CONNECTION_OPTION == 'sqlite':
        references = Column(String)
        cheatsheets = Column(String)
        tools = Column(String)
        payload_lists = Column(String)
        tests = Column(String)
    else:
        references = Column(JSONB)
        cheatsheets = Column(JSONB)
        tools = Column(JSONB)
        payload_lists = Column(JSONB)
        tests = Column(JSONB)

    active = Column(Boolean, default=True)
    created_timestamp = Column(DateTime, default=func.now()) # pylint: disable=E1102
    modified_timestamp = Column(DateTime, nullable=True)
