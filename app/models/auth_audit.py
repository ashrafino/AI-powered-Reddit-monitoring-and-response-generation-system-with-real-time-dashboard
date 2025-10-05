from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.types import TypeDecorator, VARCHAR
import json

from app.db.base import Base


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""
    
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class AuthAuditLog(Base):
    """Authentication audit log for security monitoring and compliance"""
    __tablename__ = "auth_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    client_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, token_refresh, etc.
    success = Column(Boolean, nullable=False, index=True)
    error_code = Column(String(50), nullable=True, index=True)
    error_detail = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    additional_data = Column(JSONEncodedDict, nullable=True)  # For extra context
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuthAuditLog(id={self.id}, user_email='{self.user_email}', event_type='{self.event_type}', success={self.success})>"