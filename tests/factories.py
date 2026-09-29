"""Helpers that create rows for tests. Each one commits, which inside a test
only releases a savepoint of the rolled-back test transaction (or really
commits in a concurrency test's own session)."""

import itertools
from datetime import date
from typing import TYPE_CHECKING

from magicvibe.ban.enums import BanReason
from magicvibe.ban.models import Ban
from magicvibe.reaction.enums import ReactionAction
from magicvibe.reaction.models import Reaction
from magicvibe.report.enums import ReportReason, ReportStatus
from magicvibe.report.models import Report
from magicvibe.user.enums import UserProfileGender, UserStatus
from magicvibe.user.models import User, UserPreference, UserProfile, UserTelegram

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_sequence = itertools.count(1)


async def create_user(
    session: AsyncSession,
    *,
    telegram_id: int | None = None,
    status: UserStatus = UserStatus.ACTIVE,
    first_name: str = "Test",
    username: str | None = None,
) -> User:
    number = next(_sequence)
    user = User(
        status=status,
        telegram=UserTelegram(
            telegram_id=telegram_id or 1_000_000 + number,
            first_name=first_name,
            username=username,
        ),
    )
    session.add(user)
    await session.commit()
    return user


async def create_profile(
    session: AsyncSession,
    user: User,
    *,
    name: str = "Test",
    birth_date: date = date(2000, 1, 1),
    gender: UserProfileGender = UserProfileGender.FEMALE,
    bio: str = "Bio",
    is_visible: bool = True,
) -> UserProfile:
    profile = UserProfile(
        user_id=user.id,
        name=name,
        birth_date=birth_date,
        gender=gender,
        bio=bio,
        is_visible=is_visible,
    )
    session.add(profile)
    await session.commit()
    return profile


async def create_preference(
    session: AsyncSession,
    user: User,
    *,
    min_age: int = 18,
    max_age: int = 100,
    gender: UserProfileGender | None = None,
) -> UserPreference:
    preference = UserPreference(
        user_id=user.id, min_age=min_age, max_age=max_age, gender=gender
    )
    session.add(preference)
    await session.commit()
    return preference


async def create_reaction(
    session: AsyncSession,
    from_user: User,
    to_user: User,
    *,
    action: ReactionAction = ReactionAction.LIKE,
    is_super: bool = False,
    message: str | None = None,
) -> Reaction:
    reaction = Reaction(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        action=action,
        is_super=is_super,
        message=message,
    )
    session.add(reaction)
    await session.commit()
    return reaction


async def create_report(
    session: AsyncSession,
    reporter: User,
    target: User,
    *,
    reason: ReportReason = ReportReason.SPAM,
    comment: str | None = None,
    status: ReportStatus = ReportStatus.OPEN,
) -> Report:
    report = Report(
        reporter_id=reporter.id,
        target_id=target.id,
        reason=reason,
        comment=comment,
        status=status,
    )
    session.add(report)
    await session.commit()
    return report


async def create_ban(
    session: AsyncSession,
    user: User,
    *,
    reason: BanReason = BanReason.SPAM,
    comment: str | None = None,
) -> Ban:
    """An active ban; like the `ban` domain, it also sets the user's status."""
    ban = Ban(user_id=user.id, reason=reason, comment=comment)
    user.status = UserStatus.BANNED
    session.add(ban)
    await session.commit()
    return ban
