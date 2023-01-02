import dataclasses
import enum


class AlertNoDataState(enum.Enum):
    NODATA = "NoData"
    ALERTING = "Alerting"
    OK = "OK"


class AlertExecErrState(enum.Enum):
    ERROR = "Error"
    ALERTING = "Alerting"
    OK = "OK"


class AlertReduceMode(enum.Enum):
    STRICT = ""
    DROPNN = "dropNN"
    REPLACENN = "replaceNN"


class KubernetesEventTypes(enum.Enum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"


@dataclasses.dataclass
class RelativeTimeRange:
    from_: int
    to_: int

    def to_dict(self):
        return dict(**{
            'from': self.from_,
            'to': self.to_
        })
