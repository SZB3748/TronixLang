import math
import operator
from typing import Callable

__all__ = [
    "_duration",
    "_weeks_duration",
    "_days_duration",
    "_hours_duration",
    "_minutes_duration",
    "_seconds_duration",
    "_milliseconds_duration",
    "_microseconds_duration",
    "_nanoseconds_duration",
    "_complex_duration",
    "_unitspace_convert"
]

class _duration:
    def __init__(self, x:float):
        self.x = x
    
    UNIT = ""
    FACTOR = 0
    POWER = 1

    def _copy(self):
        return type(self)(self.x)

    def __repr__(self):
        if self.x.is_integer():
            return f"{int(self.x)}{self.UNIT}"
        else:
            return f"{self.x}{self.UNIT}"

    def _prep_rhs_operand(self, other, dur:bool=True, complex:bool=True, scalar:bool=True):
        if dur and isinstance(other, _duration):
            return other.x * _unitspace_convert(self.FACTOR, self.POWER, other.FACTOR, other.POWER)
        elif complex and isinstance(other, _complex_duration):
            return other._as_duration(type(self)).x
        elif scalar and isinstance(other, (int,float)):
            return other

    def __bool__(self):
        return bool(self.x)

    def __lt__(self, other):
        rhs = self._prep_rhs_operand(other)
        if rhs is None:
            return NotImplemented
        return self.x < rhs

    def __le__(self, other):
        rhs = self._prep_rhs_operand(other)
        if rhs is None:
            return NotImplemented
        return self.x <= rhs

    def __gt__(self, other):
        rhs = self._prep_rhs_operand(other)
        if rhs is None:
            return NotImplemented
        return self.x > rhs

    def __ge__(self, other):
        rhs = self._prep_rhs_operand(other)
        if rhs is None:
            return NotImplemented
        return self.x >= rhs

    def __eq__(self, value):
        rhs = self._prep_rhs_operand(value)
        if rhs is None:
            return NotImplemented
        return self.x == rhs

    def __ne__(self, value):
        rhs = self._prep_rhs_operand(value)
        if rhs is None:
            return NotImplemented
        return self.x != rhs

    def __add__(self, other):
        if isinstance(other, _duration):
            if type(self) == type(other):
                c = self._copy()
                c.x += other.x
                return c
            else:
                return _complex_duration().combine_durations(self, other, operation=operator.add).simplify()
        elif isinstance(other, _complex_duration):
            return other._copy().combine_durations(self, operation=operator.add).simplify()
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.x += other
            return c
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, _duration):
            if type(self) == type(other):
                c = self._copy()
                c.x -= other
                return c
            else:
                return _complex_duration().combine_durations(self).combine_durations(other, operation=operator.sub).simplify()
        elif isinstance(other, _complex_duration):
            return other.__neg__().combine_durations(self, operation=operator.add).simplify()
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.x -= other
            return c
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, _duration):
            c = self._copy()
            c.x *= other.x * _unitspace_convert(self.FACTOR, self.POWER, other.FACTOR, other.POWER)
            return c
        elif isinstance(other, _complex_duration):
            c = self._copy()
            c.x *= other._as_duration(type(self)).x
            return c
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.x *= other
            return c
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, _duration):
            c = self._copy()
            c.x /= other.x * _unitspace_convert(self.FACTOR, self.POWER, other.FACTOR, other.POWER)
            return c
        elif isinstance(other, _complex_duration):
            c = self._copy()
            c.x /= other._as_duration(type(self)).x
            return c
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.x /= other
            return c
        else:
            return NotImplemented

    def __floordiv__(self, other):
        if isinstance(other, _duration):
            c = self._copy()
            c.x //= other.x * _unitspace_convert(self.FACTOR, self.POWER, other.FACTOR, other.POWER)
            return c
        elif isinstance(other, _complex_duration):
            c = self._copy()
            c.x //= other._as_duration(type(self)).x
            return c
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.x //= other
            return c
        else:
            return NotImplemented
    
    def __mod__(self, other):
        if isinstance(other, _duration):
            c = self._copy()
            c.x %= other.x * _unitspace_convert(self.FACTOR, self.POWER, other.FACTOR, other.POWER)
            return c
        elif isinstance(other, _complex_duration):
            c = self._copy()
            c.x %= other._as_duration(type(self)).x
            return c
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.x %= other
            return c
        else:
            return NotImplemented

    def __divmod__(self, other):
        return self // other, self % other
    
    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__neg__().__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return type(self)(1 / self.x).__mul__(other)

    def __rfloordiv__(self, other):
        new = self.__rtruediv__(other)
        new.x = math.floor(new.x)
        return new

    def __rmod__(self, other):
        return other % self.x

    def __iadd__(self, other):
        return self.__add__(other)

    def __isub__(self, other):
        return self.__sub__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __ifloordiv__(self, other):
        return self.__floordiv__(other)

    def __imod__(self, other):
        return self.__mod__(other)

    def __pos__(self):
        return type(self)(+self.x)

    def __neg__(self):
        return type(self)(-self.x)

class _nanoseconds_duration(_duration):
    UNIT = "ns"
    FACTOR = 10
    POWER = -9

class _microseconds_duration(_duration):
    UNIT = "μs"
    FACTOR = 10
    POWER = -6

class _milliseconds_duration(_duration):
    UNIT = "ms"
    FACTOR = 10
    POWER = -3

class _seconds_duration(_duration):
    UNIT = "s"
    FACTOR = 1
    POWER = 1

class _minutes_duration(_duration):
    UNIT = "m"
    FACTOR = 60
    POWER = 1

class _hours_duration(_duration):
    UNIT = "h"
    FACTOR = 3600
    POWER = 1

class _days_duration(_duration):
    UNIT = "d"
    FACTOR = 86400
    POWER = 1

class _weeks_duration(_duration):
    UNIT = "w"
    FACTOR = 604800
    POWER = 1

def _zero_or_close(x:float):
    return x == 0.0 or _close_zero(x)

def _close_zero(x:float):
    return round(abs(x), 12) == 0.0

def _below_zero(x:float):
    return x < 0.0 and round(abs(x), 12) > 0.0

def _above_zero(x:float):
    return x > 0.0 and round(abs(x), 12) > 0.0

class _complex_duration:

    _indexes = [_weeks_duration, _days_duration, _hours_duration, _minutes_duration, _seconds_duration, _milliseconds_duration, _microseconds_duration, _nanoseconds_duration]

    def __init__(self, weeks:_weeks_duration|float|int=0, days:_days_duration|float|int=0,
                 hours:_hours_duration|float|int=0, mins:_minutes_duration|float|int=0, secs:_seconds_duration|float|int=0,
                 ms:_milliseconds_duration|float|int=0, us:_microseconds_duration|float|int=0, ns:_nanoseconds_duration|float|int=0):
        self.weeks = weeks if isinstance(weeks, _weeks_duration) else _weeks_duration(float(weeks))
        self.days = days if isinstance(days, _days_duration) else _days_duration(float(days))
        self.hours = hours if isinstance(hours, _hours_duration) else _hours_duration(float(hours))
        self.mins = mins if isinstance(mins, _minutes_duration) else _minutes_duration(float(mins))
        self.secs = secs if isinstance(secs, _seconds_duration) else _seconds_duration(float(secs))
        self.ms = ms if isinstance(ms, _milliseconds_duration) else _milliseconds_duration(float(ms))
        self.us = us if isinstance(us, _microseconds_duration) else _microseconds_duration(float(us))
        self.ns = ns if isinstance(ns, _nanoseconds_duration) else _nanoseconds_duration(float(ns))

    def _copy(self):
        return _complex_duration(
            self.weeks.x, self.days.x,
            self.hours.x, self.mins.x, self.secs.x,
            self.ms.x, self.us.x, self.ns.x
        )

    def combine_durations(self, *durations:_duration, operation:Callable[[float, float], float]=operator.add):
        durs = [d.x for d in self.iter_durations()]
        for duration in durations:
            i = self._indexes.index(type(duration))
            durs[i] = operation(durs[i], duration.x)
        self.weeks = _weeks_duration(durs[0])
        self.days = _days_duration(durs[1])
        self.hours = _hours_duration(durs[2])
        self.mins = _minutes_duration(durs[3])
        self.secs = _seconds_duration(durs[4])
        self.ms = _milliseconds_duration(durs[5])
        self.us = _microseconds_duration(durs[6])
        self.ns = _nanoseconds_duration(durs[7])
        return self

    def iter_durations(self):
        yield self.weeks
        yield self.days
        yield self.hours
        yield self.mins
        yield self.secs
        yield self.ms
        yield self.us
        yield self.ns

    def _as_duration[T:_duration](self, t:type[T])->T:
        x = 0
        for d in self.iter_durations():
            if d:
                x += d.x * _unitspace_convert(t.FACTOR, t.POWER, d.FACTOR, d.POWER)
        return t(x)

    def as_weeks(self):
        return self._as_duration(_weeks_duration)
    def as_days(self):
        return self._as_duration(_days_duration)
    def as_hours(self):
        return self._as_duration(_hours_duration)
    def as_minutes(self):
        return self._as_duration(_minutes_duration)
    def as_seconds(self):
        return self._as_duration(_seconds_duration)
    def as_milliseconds(self):
        return self._as_duration(_milliseconds_duration)
    def as_microseconds(self):
        return self._as_duration(_microseconds_duration)
    def as_nanoseconds(self):
        return self._as_duration(_nanoseconds_duration)

    def simplify(self):
        s = self.as_seconds().x
        if _zero_or_close(s): #is 0 or close enough to 0 (allows 3 decimal places on nanoseconds)
            for d in self:
                d.x = 0
        else:
            durations = list(self.iter_durations())
            if s < 0:
                for i in range(len(durations)-1, 0, -1):
                    d = durations[i]
                    if d.x == 0:
                        continue
                    elif _close_zero(d.x):
                        d.x = 0
                    elif d.x > 0:
                        ahead = durations[i-1]
                        limit = _unitspace_convert(d.FACTOR, d.POWER, ahead.FACTOR, ahead.POWER)
                        reduce = abs(d.x)//limit + 1
                        ahead.x += reduce
                        d.x -= reduce * limit

                if _above_zero(self.weeks.x):
                    w = 0
                    w_pre = 0
                    i = len(durations)
                    while w < self.weeks.x:
                        i -= 1
                        assert i >= 0, "How did this happen?"
                        d = durations[i]
                        w_pre = w
                        w -= d.x * _unitspace_convert(_weeks_duration.FACTOR, _weeks_duration.POWER, d.FACTOR, d.POWER)
                    
                    if _zero_or_close(self.weeks.x + w):
                        for d in durations[i:]:
                            d.x = 0
                    else: # w > self.weeks.x
                        self.weeks.x += w_pre
                        for d in durations[i+1:-1]:
                            d.x = 0
                        behind = durations[i]
                        behind.x += self.weeks.x * _unitspace_convert(behind.FACTOR, behind.POWER, _weeks_duration.FACTOR, _weeks_duration.POWER)
                        self.weeks.x = 0
                
                for i in range(0, len(durations)-1):
                    d = durations[i]
                    behind = durations[i+1]
                    if d.x == 0:
                        continue
                    xf, xi = math.modf(d.x)
                    if xf:
                        behind.x += xf * _unitspace_convert(behind.FACTOR, behind.POWER, d.FACTOR, d.POWER)
                        d.x = xi

                for i in range(1, len(durations)):
                    d = durations[i]
                    ahead = durations[i-1]
                    limit = -_unitspace_convert(d.FACTOR, d.POWER, ahead.FACTOR, ahead.POWER)
                    if _close_zero(d.x - limit):
                        d.x = 0
                        ahead.x -= 1
                    elif d.x < limit:
                        ahead.x -= int(d.x / limit)
                        d.x %= limit
            else: # s > 0
                for i in range(len(durations)-1, 0, -1):
                    d = durations[i]
                    if d.x == 0:
                        continue
                    elif _close_zero(d.x):
                        d.x = 0
                    elif d.x < 0:
                        ahead = durations[i-1]
                        limit = _unitspace_convert(d.FACTOR, d.POWER, ahead.FACTOR, ahead.POWER)
                        reduce = abs(d.x)//limit + 1
                        ahead.x -= reduce
                        d.x += reduce * limit
                
                if _below_zero(self.weeks.x):
                    w = 0
                    w_pre = 0
                    i = len(durations)
                    while w > self.weeks.x:
                        i -= 1
                        assert i >= 0, "How did this happen?"
                        d = durations[i]
                        w_pre = w
                        w += d.x * _unitspace_convert(_weeks_duration.FACTOR, _weeks_duration.POWER, d.FACTOR, d.POWER)
                    
                    if _zero_or_close(self.weeks.x - w):
                        for d in durations[i:]:
                            d.x = 0
                    else: #w > self.weeks.w
                        self.weeks.x -= w_pre
                        for d in durations[i+1:-1]:
                            d.x = 0
                        behind = durations[i]
                        behind.x -= self.weeks.x * _unitspace_convert(behind.FACTOR, behind.POWER, _weeks_duration.FACTOR, _weeks_duration.POWER)
                        self.weeks.x = 0
                
                for i in range(0, len(durations)-1):
                    d = durations[i]
                    behind = durations[i+1]
                    if d.x == 0:
                        continue
                    xf, xi = math.modf(d.x)
                    if xf:
                        behind.x += xf * _unitspace_convert(behind.FACTOR, behind.POWER, d.FACTOR, d.POWER)
                        d.x = xi

                for i in range(1, len(durations)):
                    d = durations[i]
                    ahead = durations[i-1]
                    limit = _unitspace_convert(d.FACTOR, d.POWER, ahead.FACTOR, ahead.POWER)
                    if _close_zero(d.x - limit):
                        d.x = 0
                        ahead.x += 1
                    elif d.x > limit:
                        ahead.x += int(d.x / limit)
                        d.x %= limit
        return self
    
    def __iter__(self):
        for d in self.iter_durations():
            if d:
                yield d

    def __repr__(self):
        return " ".join(repr(d) for d in self) if self else repr(self.secs)

    def __bool__(self):
        return any(self.iter_durations())

    def __lt__(self, other):
        if isinstance(other, _complex_duration):
            return self.as_seconds().x < other.as_seconds().x
        elif isinstance(other, _duration):
            return self._as_duration(type(other)) < other
        elif isinstance(other, (int,float)):
            return self.as_seconds().x < other
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, _complex_duration):
            return self.as_seconds().x <= other.as_seconds().x
        elif isinstance(other, _duration):
            return self._as_duration(type(other)) <= other
        elif isinstance(other, (int,float)):
            return self.as_seconds().x <= other
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, _complex_duration):
            return self.as_seconds().x > other.as_seconds().x
        elif isinstance(other, _duration):
            return self._as_duration(type(other)) > other
        elif isinstance(other, (int,float)):
            return self.as_seconds().x > other
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, _complex_duration):
            return self.as_seconds().x >= other.as_seconds().x
        elif isinstance(other, _duration):
            return self._as_duration(type(other)) >= other
        elif isinstance(other, (int,float)):
            return self.as_seconds().x >= other
        else:
            return NotImplemented

    def __eq__(self, value):
        if isinstance(value, _complex_duration):
            return self.as_seconds().x == value.as_seconds().x
        elif isinstance(value, _duration):
            return self._as_duration(type(value)) == value
        elif isinstance(value, (int,float)):
            return self.as_seconds().x == value
        else:
            return NotImplemented

    def __ne__(self, value):
        if isinstance(value, _complex_duration):
            return self.as_seconds().x != value.as_seconds().x
        elif isinstance(value, _duration):
            return self._as_duration(type(value)) != value
        elif isinstance(value, (int,float)):
            return self.as_seconds().x != value
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, _duration):
            c = self._copy()
            return c.combine_durations(other, operation=operator.add).simplify()
        elif isinstance(other, _complex_duration):
            c = self._copy()
            return c.combine_durations(*other, operation=operator.add).simplify()
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.secs.x += other
            return self.simplify()
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, _duration):
            c = self._copy()
            return c.combine_durations(other, operation=operator.sub).simplify()
        elif isinstance(other, _complex_duration):
            c = self._copy()
            return c.combine_durations(*other, operation=operator.sub).simplify()
        elif isinstance(other, (int, float)):
            c = self._copy()
            c.secs.x -= other
            return self.simplify()
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, _duration):
            return self._as_duration(type(other)) * other
        elif isinstance(other, _complex_duration):
            return type(self)(secs=self.as_seconds()*other.as_seconds()).simplify()
        elif isinstance(other, (int, float)):
            return type(self)(*(d.x * other for d in self.iter_durations()))
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, _duration):
            return self._as_duration(type(other)) / other
        elif isinstance(other, _complex_duration):
            return type(self)(secs=self.as_seconds()/other.as_seconds()).simplify()
        elif isinstance(other, (int, float)):
            return type(self)(*(d.x / other for d in self.iter_durations()))
        else:
            return NotImplemented

    def __floordiv__(self, other):
        if isinstance(other, _duration):
            return self._as_duration(type(other)) // other
        elif isinstance(other, _complex_duration):
            return type(self)(secs=self.as_seconds()//other.as_seconds()).simplify()
        elif isinstance(other, (int, float)):
            return type(self)(*(d.x // other for d in self.iter_durations()))
        else:
            return NotImplemented
    
    def __mod__(self, other):
        if isinstance(other, _duration):
            return self._as_duration(type(other)) % other
        elif isinstance(other, _complex_duration):
            return type(self)(secs=self.as_seconds()%other.as_seconds()).simplify()
        elif isinstance(other, (int, float)):
            return type(self)(*(d.x % other for d in self.iter_durations()))
        else:
            return NotImplemented

    def __divmod__(self, other):
        return self // other, self % other
    
    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__neg__().__iadd__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return type(self)(*(other/d.x if d.x else 0 for d in self.iter_durations()))

    def __rfloordiv__(self, other):
        return type(self)(*(other//d.x if d.x else 0 for d in self.iter_durations()))

    def __rmod__(self, other):
        return other % self.as_seconds().x

    def __iadd__(self, other):
        return self.__add__(other)

    def __isub__(self, other):
        return self.__sub__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __ifloordiv__(self, other):
        return self.__floordiv__(other)

    def __imod__(self, other):
        return self.__mod__(other)

    def __pos__(self):
        return type(self)(*(+d.x for d in self.iter_durations()))

    def __neg__(self):
        return type(self)(*(-d.x for d in self.iter_durations()))


_BEFORE_1 = math.nextafter(1.0, 0.0)

#multiply this with the y value to convert the y value to the unit of the x value
def _unitspace_convert(x_factor:int, x_power:int, y_factor:int, y_power:int)->float:
    if x_power == y_power:
        c = y_factor/x_factor
    else:
        c = y_factor**y_power/x_factor**x_power
    
    if c >= _BEFORE_1:
        return round(c, 10)
    else:
        return c