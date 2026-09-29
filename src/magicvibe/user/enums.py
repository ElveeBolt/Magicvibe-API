from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    BANNED = "banned"


class UserProfileGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class DatingGoal(StrEnum):
    RELATIONSHIP = "relationship"
    FRIENDSHIP = "friendship"
    CASUAL = "casual"
    CHATTING = "chatting"
