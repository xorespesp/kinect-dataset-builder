from enum import IntEnum

class FormattedIntEnum(IntEnum):
    @property
    def formatted_name(self) -> str:
        return self.name.lower()
