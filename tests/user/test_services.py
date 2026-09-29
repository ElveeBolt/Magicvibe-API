from magicvibe.ban.enums import BanReason
from magicvibe.ban.models import Ban
from magicvibe.core.exceptions import ErrorCode
from magicvibe.user.services import user_banned_error


def test_user_banned_error_carries_only_reason_and_comment() -> None:
    ban = Ban(id=7, user_id=1, reason=BanReason.SPAM, comment="Ads", lift_comment="x")

    error = user_banned_error(ban)

    assert error.code is ErrorCode.USER_BANNED
    assert error.status_code == 403
    assert error.extra == {"ban": {"reason": BanReason.SPAM, "comment": "Ads"}}
