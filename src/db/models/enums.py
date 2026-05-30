"""Enum mirrors for backend-owned MySQL enum columns."""

from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    BARISTA = "BARISTA"
    ADMIN = "ADMIN"
    DELETED = "DELETED"


class ImageType(str, Enum):
    THUMB = "THUMB"
    SUB = "SUB"


class Region(str, Enum):
    SEOUL = "SEOUL"
    GYEONGGI = "GYEONGGI"
    INCHEON = "INCHEON"
    BUSAN = "BUSAN"
    DAEGU = "DAEGU"
    GWANGJU = "GWANGJU"
    DAEJEON = "DAEJEON"
    ULSAN = "ULSAN"
    SEJONG = "SEJONG"
    GANGWON = "GANGWON"
    CHUNGBUK = "CHUNGBUK"
    CHUNGNAM = "CHUNGNAM"
    JEONBUK = "JEONBUK"
    JEONNAM = "JEONNAM"
    GYEONGBUK = "GYEONGBUK"
    GYEONGNAM = "GYEONGNAM"
    JEJU = "JEJU"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"


class RoastingLevel(str, Enum):
    LIGHT = "LIGHT"
    MEDIUM = "MEDIUM"
    DARK = "DARK"
    MEDIUMLIGHT = "MEDIUMLIGHT"
    MEDIUMDARK = "MEDIUMDARK"


class FlavorCategory(str, Enum):
    FRUITY = "FRUITY"
    FLORAL = "FLORAL"
    SWEET = "SWEET"
    BROWN_SUGAR = "BROWN_SUGAR"
    CHOCOLATY = "CHOCOLATY"
    NUTTY = "NUTTY"
    SPICE = "SPICE"
    ROASTED = "ROASTED"
    FERMENTED = "FERMENTED"
    GREEN_VEGETATIVE = "GREEN_VEGETATIVE"
    EARTHY = "EARTHY"
    WOODY = "WOODY"
    CHEMICAL = "CHEMICAL"
    SAVORY = "SAVORY"
    MOUTHFEEL = "MOUTHFEEL"
    DEFECT = "DEFECT"
    OTHER = "OTHER"


class PaymentProvider(str, Enum):
    KAKAO = "KAKAO"
    NAVER = "NAVER"
    TOSS = "TOSS"
    CARD = "CARD"
    ETC = "ETC"


class PaymentStatus(str, Enum):
    READY = "READY"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARTIAL_CANCELLED = "PARTIAL_CANCELLED"


class ScheduleStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ENDED = "ENDED"


class DifficultyLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class LessonCategory(str, Enum):
    HOBBY = "HOBBY"
    CERTIFICATE = "CERTIFICATE"


class UserProvider(str, Enum):
    GOOGLE = "GOOGLE"
    NAVER = "NAVER"
    KAKAO = "KAKAO"

