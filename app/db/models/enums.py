import enum

class UserRole(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class Visibility(str, enum.Enum):
    PRIVATE = "PRIVATE"
    DEPARTMENT = "DEPARTMENT"
    PUBLIC = "PUBLIC"

class FileStatus(str, enum.Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"
