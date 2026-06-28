from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, func
from datetime import datetime, timedelta
from typing import Optional

from config import DATABASE_URL
from database.models import Base, User, Payment, Request, Referral, Rating, Quiz, QuizQuestion, PostReaction

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ─── User helpers ───────────────────────────────────────────────────────────

async def get_or_create_user(
    user_id: int,
    username: Optional[str],
    full_name: Optional[str],
) -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                username=username,
                full_name=full_name,
                balance=0,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Update name/username if changed
            user.username = username
            user.full_name = full_name
            user.last_active = datetime.utcnow()
            await session.commit()
        return user


async def get_user(user_id: int) -> Optional[User]:
    async with async_session() as session:
        return await session.get(User, user_id)


async def mark_free_used(user_id: int):
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(free_used=True)
        )
        await session.commit()


async def activate_premium(user_id: int, days: int = 30):
    expires = datetime.utcnow() + timedelta(days=days)
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_premium=True, premium_expires=expires)
        )
        await session.commit()

async def add_balance(user_id: int, amount: int) -> Optional[User]:
    """Adds amount to user balance."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.balance = (user.balance or 0) + amount
            await session.commit()
            await session.refresh(user)
        return user

async def set_balance(user_id: int, new_balance: int) -> Optional[User]:
    """Sets user balance to a specific amount."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.balance = new_balance
            await session.commit()
            await session.refresh(user)
        return user

async def deduct_balance(user_id: int, amount: int) -> bool:
    """Deducts amount from user balance. Returns True if successful."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and (user.balance or 0) >= amount:
            user.balance = 0
            await session.commit()
            return True
        return False


async def update_user_language(user_id: int, lang: str):
    """Update user's interface language."""
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(language=lang)
        )
        await session.commit()


async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


async def get_user_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar()


async def get_premium_count() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(User.id)).where(User.is_premium == True)
        )
        return result.scalar()


# ─── Payment helpers ─────────────────────────────────────────────────────────

async def create_payment(
    user_id: int,
    amount: int,
    package: str,
    screenshot_file_id: str,
) -> Payment:
    async with async_session() as session:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            package=package,
            screenshot_file_id=screenshot_file_id,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment


async def get_pending_payments() -> list[Payment]:
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.status == "pending").order_by(Payment.created_at)
        )
        return result.scalars().all()


async def get_payment(payment_id: int) -> Optional[Payment]:
    async with async_session() as session:
        return await session.get(Payment, payment_id)


async def update_payment_status(
    payment_id: int,
    status: str,
    admin_note: Optional[str] = None,
) -> Optional[Payment]:
    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if payment:
            payment.status = status
            payment.admin_note = admin_note
            payment.reviewed_at = datetime.utcnow()
            await session.commit()
            await session.refresh(payment)
        return payment


async def get_payment_count() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Payment.id)).where(Payment.status == "approved")
        )
        return result.scalar()


# ─── Request helpers ──────────────────────────────────────────────────────────

async def create_request(
    user_id: int,
    service_type: str,
    topic: str,
    options: Optional[dict] = None,
    file_id: Optional[str] = None,
) -> Request:
    async with async_session() as session:
        req = Request(
            user_id=user_id,
            service_type=service_type,
            topic=topic,
            options=options or {},
            file_id=file_id,
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)
        return req


async def get_request_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Request.id)))
        return result.scalar()


async def get_recent_requests(limit: int = 10) -> list[Request]:
    async with async_session() as session:
        result = await session.execute(
            select(Request).order_by(Request.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


# ─── Referral helpers ────────────────────────────────────────────────────────

async def process_referral(referrer_id: int, new_user_id: int, bonus_inviter: int, bonus_invitee: int) -> bool:
    """
    Process a referral: give bonuses to both users, record the referral.
    Returns True if referral was processed (first time), False if already exists.
    """
    async with async_session() as session:
        # Check if this referral already exists
        existing = await session.execute(
            select(Referral).where(
                Referral.referrer_id == referrer_id,
                Referral.referred_id == new_user_id,
            )
        )
        if existing.scalar():
            return False  # already processed

        # Don't allow self-referral
        if referrer_id == new_user_id:
            return False

        # Check referrer exists
        referrer = await session.get(User, referrer_id)
        if not referrer:
            return False

        # Give bonus to inviter
        referrer.balance = (referrer.balance or 0) + bonus_inviter
        referrer.referral_count = (referrer.referral_count or 0) + 1
        referrer.referral_earnings = (referrer.referral_earnings or 0) + bonus_inviter

        # Give bonus to new user
        new_user = await session.get(User, new_user_id)
        if new_user:
            new_user.balance = (new_user.balance or 0) + bonus_invitee
            new_user.referred_by = referrer_id

        # Record referral
        ref = Referral(
            referrer_id=referrer_id,
            referred_id=new_user_id,
            bonus_given=bonus_inviter,
        )
        session.add(ref)
        await session.commit()
        return True


async def get_referral_stats(user_id: int) -> dict:
    """Get referral statistics for a user."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return {"count": 0, "earnings": 0}
        return {
            "count": user.referral_count or 0,
            "earnings": user.referral_earnings or 0,
        }


async def save_rating(user_id: int, service_type: str, rating: int):
    """Save user's quality rating (1-5) for a generated document."""
    async with async_session() as session:
        r = Rating(user_id=user_id, service_type=service_type, rating=rating)
        session.add(r)
        await session.commit()


# ─── Quiz helpers ─────────────────────────────────────────────────────────────

async def save_quiz(user_id: int, name: str, questions: list[dict],
                    per_quiz: int = 20, time_per_q: int = 30, shuffle_mode: str = "none") -> Quiz:
    """Save quiz and its questions to DB. Returns Quiz object."""
    async with async_session() as session:
        quiz = Quiz(
            user_id=user_id,
            name=name,
            total_questions=len(questions),
            per_quiz=per_quiz,
            time_per_q=time_per_q,
            shuffle_mode=shuffle_mode,
        )
        session.add(quiz)
        await session.flush()  # get quiz.id

        for i, q in enumerate(questions):
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question=q["question"],
                options=q["options"],
                correct_index=q["correct_index"],
                order_num=i,
            )
            session.add(qq)

        await session.commit()
        await session.refresh(quiz)
        return quiz


async def get_user_quizzes(user_id: int) -> list[Quiz]:
    """Get all quizzes for a user."""
    async with async_session() as session:
        result = await session.execute(
            select(Quiz).where(Quiz.user_id == user_id).order_by(Quiz.created_at.desc())
        )
        return result.scalars().all()


async def get_quiz_with_questions(quiz_id: int) -> Optional[Quiz]:
    """Get quiz with all questions loaded."""
    from sqlalchemy.orm import selectinload
    async with async_session() as session:
        result = await session.execute(
            select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions))
        )
        return result.scalar_one_or_none()


async def delete_quiz(quiz_id: int):
    """Delete a quiz and all its questions."""
    async with async_session() as session:
        quiz = await session.get(Quiz, quiz_id)
        if quiz:
            await session.delete(quiz)
            await session.commit()
