import math

class percent:
    def __init__(self, value:float=0.0):
        self.value = value
    
    def __getstate__(self):
        return self.value

    def __setstate__(self, v:float):
        self.value = v

    def __repr__(self):
        return f"{self.value*100}%"
    
    def __bool__(self):
        return bool(self.value)
    
    def __int__(self):
        return int(self.value)
    
    def __float__(self):
        return float(self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, value):
        if isinstance(value, percent):
            return self.value == value.value
        return value == self.value
    
    def __ne__(self, value):
        if isinstance(value, percent):
            return self.value != value.value
        return value != self.value
    
    def __lt__(self, other):
        if isinstance(other, percent):
            return self.value < other.value
        return self.value < other
    
    def __gt__(self, other):
        if isinstance(other, percent):
            return self.value > other.value
        return self.value > other
    
    def __le__(self, other):
        if isinstance(other, percent):
            return self.value <= other.value
        return self.value <= other
    
    def __ge__(self, other):
        if isinstance(other, percent):
            return self.value >= other.value
        return self.value >= other
    
    def __add__(self, other):
        if isinstance(other, percent):
            return percent(self.value + other.value)
        return other * (1+self.value)
    
    def __sub__(self, other):
        if isinstance(other, percent):
            return percent(self.value - other.value)
        return other * (self.value-1)
    
    def __mul__(self, other):
        if isinstance(other, percent):
            return percent(self.value * other.value)
        return other * self.value
    
    def __truediv__(self, other):
        if isinstance(other, percent):
            return percent(self.value / other.value)
        return self.value / other
    
    def __floordiv__(self, other):
        if isinstance(other, percent):
            return percent(self.value // other.value)
        return self.value // other
    
    def __mod__(self, other):
        return percent(self.value % other)
    
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
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __rsub__(self, other):
        return other * (1-self.value)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __rtruediv__(self, other):
        return other / self.value
    
    def __rfloordiv__(self, other):
        return other // self.value
    
    def __rmod__(self, other):
        return other % self.value
    
    def __pos__(self):
        return percent(self.value)
    
    def __neg__(self):
        return percent(-self.value)

class degrees:
    def __init__(self, value:float=0.0):
        self.value = value
    
    def __getstate__(self):
        return self.value

    def __setstate__(self, v:float):
        self.value = v

    def __repr__(self):
        return f"{self.value}°"

    def __float__(self):
        return float(self.value)

    def __eq__(self, value):
        if isinstance(value, degrees):
            return self.value == value.value
        elif isinstance(value, radians):
            return self.value == math.degrees(value.value)
        return value == self.value
    
    def __ne__(self, value):
        if isinstance(value, degrees):
            return self.value != value.value
        elif isinstance(value, radians):
            return self.value != math.degrees(value.value)
        return value != self.value
    
    def __lt__(self, other):
        if isinstance(other, degrees):
            return self.value < other.value
        elif isinstance(other, radians):
            return self.value < math.degrees(other.value)
        return self.value < other
    
    def __gt__(self, other):
        if isinstance(other, degrees):
            return self.value > other.value
        elif isinstance(other, radians):
            return self.value > math.degrees(other.value)
        return self.value > other
    
    def __le__(self, other):
        if isinstance(other, degrees):
            return self.value <= other.value
        elif isinstance(other, radians):
            return self.value <= math.degrees(other.value)
        return self.value <= other
    
    def __ge__(self, other):
        if isinstance(other, degrees):
            return self.value >= other.value
        elif isinstance(other, radians):
            return self.value >= math.degrees(other.value)
        return self.value >= other

    def __hash__(self):
        return hash(self.value)
    
    def __add__(self, other):
        if isinstance(other, degrees):
            return degrees(self.value + other.value)
        elif isinstance(other, radians):
            return degrees(self.value + math.degrees(other.value))
        elif isinstance(other, (float,int)):
            return degrees(self.value + other)
        return NotImplemented
    
    def __sub__(self, other):
        if isinstance(other, degrees):
            return degrees(self.value - other.value)
        elif isinstance(other, radians):
            return degrees(self.value - math.degrees(other.value))
        elif isinstance(other, (float,int)):
            return degrees(other * (self.value-1))
        return NotImplemented
    
    def __mul__(self, other):
        if isinstance(other, degrees):
            return degrees(self.value * other.value)
        elif isinstance(other, radians):
            return degrees(self.value * math.degrees(other.value))
        elif isinstance(other, (float,int)):
            return degrees(other * self.value)
        return NotImplemented
    
    def __truediv__(self, other):
        if isinstance(other, degrees):
            return degrees(self.value / other.value)
        elif isinstance(other, radians):
            return degrees(self.value / math.degrees(other.value))
        elif isinstance(other, (float,int)):
            return degrees(self.value / other)
        return NotImplemented
    
    def __floordiv__(self, other):
        if isinstance(other, degrees):
            return degrees(self.value // other.value)
        elif isinstance(other, radians):
            return degrees(self.value // math.degrees(other.value))
        elif isinstance(other, (float,int)):
            return degrees(self.value // other)
        return NotImplemented
    
    def __mod__(self, other):
        return degrees(self.value % other)
    
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
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __rsub__(self, other):
        return other - self.value
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __rtruediv__(self, other):
        return other / self.value
    
    def __rfloordiv__(self, other):
        return other // self.value
    
    def __rmod__(self, other):
        return other % self.value
    
    def __pos__(self):
        return degrees(self.value)
    
    def __neg__(self):
        return degrees(-self.value)

class radians:
    def __init__(self, value:float=0.0):
        self.value = value
    
    def __getstate__(self):
        return self.value

    def __setstate__(self, v:float):
        self.value = v

    def __repr__(self):
        return f"{self.value/math.pi}πrad"

    def __hash__(self):
        return hash(self.value)

    def __float__(self):
        return float(self.value)

    def __eq__(self, value):
        if isinstance(value, radians):
            return self.value == value.value
        elif isinstance(value, degrees):
            return self.value == math.radians(value.value)
        return value == self.value
    
    def __ne__(self, value):
        if isinstance(value, radians):
            return self.value != value.value
        elif isinstance(value, degrees):
            return self.value != math.radians(value.value)
        return value != self.value
    
    def __lt__(self, other):
        if isinstance(other, radians):
            return self.value < other.value
        elif isinstance(other, degrees):
            return self.value < math.radians(other.value)
        return self.value < other
    
    def __gt__(self, other):
        if isinstance(other, radians):
            return self.value > other.value
        elif isinstance(other, degrees):
            return self.value > math.radians(other.value)
        return self.value > other
    
    def __le__(self, other):
        if isinstance(other, radians):
            return self.value <= other.value
        elif isinstance(other, degrees):
            return self.value <= math.radians(other.value)
        return self.value <= other
    
    def __ge__(self, other):
        if isinstance(other, radians):
            return self.value >= other.value
        elif isinstance(other, degrees):
            return self.value >= math.radians(other.value)
        return self.value >= other
    
    def __add__(self, other):
        if isinstance(other, radians):
            return radians(self.value + other.value)
        elif isinstance(other, degrees):
            return radians(self.value + math.radians(other.value))
        elif isinstance(other, (float, int)):
            return radians(self.value + other)
        return NotImplemented
    
    def __sub__(self, other):
        if isinstance(other, radians):
            return radians(self.value - other.value)
        elif isinstance(other, degrees):
            return radians(self.value - math.radians(other.value))
        elif isinstance(other, (float, int)):
            return radians(other * (self.value-1))
        return NotImplemented
    
    def __mul__(self, other):
        if isinstance(other, radians):
            return radians(self.value * other.value)
        elif isinstance(other, degrees):
            return radians(self.value * math.radians(other.value))
        elif isinstance(other, (float, int)):
            return radians(other * self.value)
        return NotImplemented
    
    def __truediv__(self, other):
        if isinstance(other, radians):
            return radians(self.value / other.value)
        elif isinstance(other, degrees):
            return radians(self.value / math.radians(other.value))
        elif isinstance(other, (float, int)):
            return radians(self.value / other)
        return NotImplemented
    
    def __floordiv__(self, other):
        if isinstance(other, radians):
            return radians(self.value // other.value)
        elif isinstance(other, degrees):
            return radians(self.value // math.radians(other.value))
        elif isinstance(other, (float, int)):
            return radians(self.value // other)
        return NotImplemented
    
    def __mod__(self, other):
        return radians(self.value % other)
    
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
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __rsub__(self, other):
        return other - self.value
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __rtruediv__(self, other):
        return other / self.value
    
    def __rfloordiv__(self, other):
        return other // self.value
    
    def __rmod__(self, other):
        return other % self.value

class _functional_integer(int):
    @classmethod
    def from_bytes(cls, bytes, byteorder="big", *, signed=False):
        return cls(super().from_bytes(bytes, byteorder, signed=signed))
    
    def __new__(cls, value, *args, **kwargs):
        if value is NotImplemented:
            raise NotImplementedError
        return super().__new__(cls, value)

    def _copy(self, value):
        if isinstance(value, int):
            cls = type(self)
            new = cls.__new__(cls, value)
            new.__dict__.update(self.__dict__)
            return new
        else:
            return value
    
    def __index__(self):
        return int(self)

    def __float__(self):
        return float(int(self))

    def __str__(self):
        return "%d" % int(self)

    def __repr__(self):
        return f"<{type(self).__name__} {int(self)} at {hex(id(self)).upper()}>"

    def __bool__(self):
        return bool(int(self))

    def __hash__(self):
        return hash(int(self))

    def __trunc__(self):
        return self._copy(super(_functional_integer, self).__trunc__())

    def __round__(self, ndigits = ...):
        return self._copy(super(_functional_integer, self).__round__(ndigits))

    def __abs__(self):
        return self._copy(super(_functional_integer, self).__abs__())

    def __neg__(self):
        return self._copy(super(_functional_integer, self).__neg__())

    def __pos__(self):
        return self._copy(super(_functional_integer, self).__pos__())

    def __add__(self, value):
        return self._copy(super(_functional_integer, self).__add__(value))

    def __sub__(self, value):
        return self._copy(super(_functional_integer, self).__sub__(value))

    def __mul__(self, value):
        return self._copy(super(_functional_integer, self).__mul__(value))

    def __truediv__(self, value):
        return self._copy(super(_functional_integer, self).__truediv__(value))

    def __floordiv__(self, value):
        return self._copy(super(_functional_integer, self).__floordiv__(value))

    def __pow__(self, value):
        return self._copy(super(_functional_integer, self).__pow__(value))

    def __mod__(self, value):
        return self._copy(super(_functional_integer, self).__mod__(value))

    def __radd__(self, value):
        return self._copy(super(_functional_integer, self).__radd__(value))

    def __rsub__(self, value):
        return self._copy(super(_functional_integer, self).__rsub__(value))

    def __rmul__(self, value):
        return self._copy(super(_functional_integer, self).__rmul__(value))

    def __rtruediv__(self, value):
        return self._copy(super(_functional_integer, self).__rtruediv__(value))

    def __rfloordiv__(self, value):
        return self._copy(super(_functional_integer, self).__rfloordiv__(value))

    def __eq__(self, value):
        if isinstance(value, _functional_integer):
            return int(self) == int(value)
        return int(self) == value
    
    def __ne__(self, value):
        if isinstance(value, _functional_integer):
            return int(self) != int(value)
        return int(self) != value
    
    def __gt__(self, value):
        if isinstance(value, _functional_integer):
            return int(self) > int(value)
        return int(self) > value

    def __ge__(self, value):
        if isinstance(value, _functional_integer):
            return int(self) >= int(value)
        return int(self) >= value
    
    def __lt__(self, value):
        if isinstance(value, _functional_integer):
            return int(self) < int(value)
        return int(self) < value

    def __le__(self, value):
        if isinstance(value, _functional_integer):
            return int(self) <= int(value)
        return int(self) <= value

    def __invert__(self):
        return self._copy(super(_functional_integer, self).__invert__())

    def __and__(self, value):
        return self._copy(super(_functional_integer, self).__and__(value))

    def __or__(self, value):
        return self._copy(super(_functional_integer, self).__or__(value))

    def __xor__(self, value):
        return self._copy(super(_functional_integer, self).__xor__(value))

    def __rand__(self, value):
        return self._copy(super(_functional_integer, self).__rand__(value))

    def __ror__(self, value):
        return self._copy(super(_functional_integer, self).__ror__(value))

    def __rxor__(self, value):
        return self._copy(super(_functional_integer, self).__rxor__(value))

    def __lshift__(self, value):
        return self._copy(super(_functional_integer, self).__lshift__(value))

    def __rshift__(self, value):
        return self._copy(super(_functional_integer, self).__rshift__(value))

    def __rlshift__(self, value):
        return self._copy(super(_functional_integer, self).__rlshift__(value))

    def __rrshift__(self, value):
        return self._copy(super(_functional_integer, self).__rrshift__(value))

class color_component(_functional_integer):
    LOWER = 0
    UPPER = 1

    @classmethod
    def from_percent(cls, p:float, clamp:bool=True):
        value = p*(cls.UPPER-cls.LOWER)+cls.LOWER
        if clamp:
            value = min(max(cls.LOWER, value), cls.UPPER)
        return cls(value)
    
    def __init__(self, *args, **kwargs):
        if self < self.LOWER or self > self.UPPER:
            raise ValueError(f"{type(self).__name__} object must be in range {self.LOWER}-{self.UPPER}, got {int(self)}")

    def _copy(self, value):
        if isinstance(value, int):
            cls = type(self)
            new = cls.__new__(cls, min(max(self.LOWER, value), self.UPPER))
            new.__dict__.update(self.__dict__)
            return new
        else:
            return value


class color_component_rgba(color_component):
    UPPER = 255

class color_component_cmyk(color_component):
    UPPER = 100
        