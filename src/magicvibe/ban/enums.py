from enum import StrEnum


class BanReason(StrEnum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    UNDERAGE = "underage"
    SCAM = "scam"
    OTHER = "other"
