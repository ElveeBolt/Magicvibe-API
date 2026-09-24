from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    BANNED = "banned"
    DELETED = "deleted"


class UserProfileGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
