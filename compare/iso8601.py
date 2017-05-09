from .compare import Hook
import iso8601
import datetime

class ISO8601(Hook):
    """Hook for comparing datetimes. It can handle comprasion between:
    - two datetimes
    - datetime and string in iso8601 format
    - two strings which consist of valid time in iso8601 format
    You can also specify that two datetimes should be considered equal when
    difference between then is within given tolerance.
    """
    def __init__(self, **kwargs):
        """Constructor.

        Keyword args:
        from_str -- should we try to parse string to gather datetime instance.
        tolerance -- tolerance (in seconds)
        """
        self.from_str = kwargs.get("from_str",True)
        self.tolerance = datetime.timedelta(seconds=kwargs.get("tolerance",0.01))

    def _getdatetime(self, o):
        """Gather datetime instance from an object accoring to specified options."""
        if isinstance(o, datetime.datetime):
            return o
        elif isinstance(o,str) and self.from_str:
            try:
                return iso8601.parse_date(o)
            except iso8601.ParseError:
                return None
        return None

    def condition(self, lhs, rhs):
        """Returns whether two objects should be compared as datetimes."""
        self.lhs_dt = self._getdatetime(lhs)
        self.rhs_dt = self._getdatetime(rhs)
        return self.lhs_dt and self.rhs_dt

    def compare(self, lhs, rhs, stack, hooks):
        """Performs comprasion of two datetimes."""
        if abs(self.lhs_dt - self.rhs_dt) > self.tolerance:
            raise CompareError("datetimes@ difference exceedes tolerance",stack)
