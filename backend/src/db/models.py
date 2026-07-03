from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from src.db.base import Base


class UserRole(str, enum.Enum):
    AGENT = "agent"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    encrypted_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    policies = relationship("Policy", back_populates="user")
    claims = relationship("Claim", back_populates="user")
    rate_snapshots = relationship("RateSnapshot", back_populates="user")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    carrier_id = Column(String(100), nullable=True)
    status = Column(String(50), default="active")
    current_rate = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="policies")
    snapshots = relationship("PolicySnapshot", back_populates="policy")


class PolicySnapshot(Base):
    __tablename__ = "policy_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    raw_slip_content = Column(Text, nullable=True)
    parsed_limits = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    policy = relationship("Policy", back_populates="snapshots")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    carrier_id = Column(String(100), nullable=True)
    status = Column(String(50), default="filed")
    filed_date = Column(DateTime(timezone=True), server_default=func.now())
    photo_blob = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="claims")


class RateSnapshot(Base):
    __tablename__ = "rate_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    carrier_id = Column(String(100), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    rate = Column(Float, nullable=False)

    user = relationship("User", back_populates="rate_snapshots")