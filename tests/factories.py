"""Helpers that create rows for tests. Each one commits, which inside a test
only releases a savepoint of the rolled-back test transaction (or really
commits in a concurrency test's own session)."""

import itertools
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from magicvibe.ban.enums import BanReason
from magicvibe.ban.models import Ban
from magicvibe.reaction.enums import ReactionAction
from magicvibe.reaction.models import Match, Reaction
from magicvibe.region.enums import RegionCodeType
from magicvibe.region.models import Region, RegionCity
from magicvibe.report.enums import ReportReason, ReportStatus
from magicvibe.report.models import Report
from magicvibe.user.enums import DatingGoal, UserProfileGender, UserStatus
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
    city: RegionCity | None = None,
    dating_goal: DatingGoal = DatingGoal.RELATIONSHIP,
    bio: str | None = "Bio",
    is_visible: bool = True,
) -> UserProfile:
    """A complete profile; a made-up city is created when none is given."""
    if city is None:
        city = await create_city(session, await create_region(session))
    profile = UserProfile(
        user_id=user.id,
        name=name,
        birth_date=birth_date,
        gender=gender,
        city_id=city.id,
        dating_goal=dating_goal,
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
    city: RegionCity | None = None,
    dating_goal: DatingGoal | None = None,
) -> UserPreference:
    """Preferences; every criterion left out means "any"."""
    preference = UserPreference(
        user_id=user.id,
        min_age=min_age,
        max_age=max_age,
        gender=gender,
        city_id=city.id if city is not None else None,
        dating_goal=dating_goal,
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


async def create_match(session: AsyncSession, first: User, second: User) -> Match:
    """A match row for two users (their likes are created separately)."""
    match = Match(
        user_a_id=min(first.id, second.id), user_b_id=max(first.id, second.id)
    )
    session.add(match)
    await session.commit()
    return match


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
    lifted: bool = False,
) -> Ban:
    """An active ban, or a lifted one with `lifted=True`. Like the `ban`
    domain, an active ban also sets the user's status."""
    ban = Ban(
        user_id=user.id,
        reason=reason,
        comment=comment,
        lifted_at=datetime.now(UTC) if lifted else None,
    )
    if not lifted:
        user.status = UserStatus.BANNED
    session.add(ban)
    await session.commit()
    return ban


def _katotth_code(number: int) -> str:
    """A made-up code in the KATOTTH format (`UA` + 17 digits); only the test
    database may hold made-up regions and cities."""
    return f"UA{number:017d}"


async def create_region(
    session: AsyncSession,
    *,
    name: str = "Тестова",
    name_en: str = "Testova",
    code_type: RegionCodeType = RegionCodeType.OBLAST,
) -> Region:
    region = Region(
        katotth_code=_katotth_code(next(_sequence)),
        name=name,
        name_en=name_en,
        code_type=code_type,
    )
    session.add(region)
    await session.commit()
    return region


async def create_city(
    session: AsyncSession,
    region: Region,
    *,
    name: str = "Тестове",
    name_en: str = "Testove",
) -> RegionCity:
    city = RegionCity(
        region_id=region.id,
        katotth_code=_katotth_code(next(_sequence)),
        name=name,
        name_en=name_en,
    )
    session.add(city)
    await session.commit()
    return city
