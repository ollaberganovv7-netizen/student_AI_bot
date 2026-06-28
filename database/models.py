from __future__ import annotations
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean,
    DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    language = Column(String(8), default="uz")
    free_used = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False) # Deprecated but kept for compatibility
    is_banned = Column(Boolean, default=False)
    premium_expires = Column(DateTime, nullable=True) # Deprecated
    balance = Column(Integer, default=0)
    referred_by = Column(BigInteger, nullable=True)  # who invited this user
    referral_count = Column(Integer, default=0)  # how many users invited
    referral_earnings = Column(Integer, default=0)  # total earned from referrals
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = relationship("Payment", back_populates="user", lazy="select")
    requests = relationship("Request", back_populates="user", lazy="select")
    referrals = relationship("Referral", back_populates="referrer", foreign_keys="Referral.referrer_id", lazy="select")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    package = Column(String(64), nullable=False)
    screenshot_file_id = Column(String(256), nullable=True)
    status = Column(String(16), default="pending")  # pending / approved / rejected
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")

    def __repr__(self):
        return f"<Payment id={self.id} user={self.user_id} status={self.status}>"


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    service_type = Column(String(32), nullable=False)
    topic = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    file_id = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="requests")

    def __repr__(self):
        return f"<Request id={self.id} type={self.service_type}>"


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    service_type = Column(String(32), nullable=False)  # presentation, referat, etc.
    rating = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Rating user={self.user_id} service={self.service_type} rating={self.rating}>"


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(256), nullable=False)
    total_questions = Column(Integer, default=0)
    per_quiz = Column(Integer, default=20)
    time_per_q = Column(Integer, default=30)
    shuffle_mode = Column(String(16), default="none")
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("QuizQuestion", back_populates="quiz", lazy="select", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz id={self.id} name={self.name} questions={self.total_questions}>"


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)     # list of strings
    correct_index = Column(Integer, nullable=False)
    order_num = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="questions")

    def __repr__(self):
        return f"<QuizQuestion id={self.id} quiz={self.quiz_id}>"


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    referred_id = Column(BigInteger, nullable=False)  # new user who joined
    bonus_given = Column(Integer, default=0)  # bonus amount credited
    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", back_populates="referrals", foreign_keys=[referrer_id])

    def __repr__(self):
        return f"<Referral referrer={self.referrer_id} referred={self.referred_id}>"


class PostReaction(Base):
    __tablename__ = "post_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)       # channel/group chat id
    message_id = Column(BigInteger, nullable=False)    # message id in channel
    user_id = Column(BigInteger, nullable=False)       # who reacted
    user_name = Column(String(128), nullable=True)     # display name
    emoji = Column(String(16), default="🔥")           # which reaction
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PostReaction msg={self.message_id} user={self.user_id}>"
