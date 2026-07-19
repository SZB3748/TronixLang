import math

class percent:
    def __init__(self, value:float=0.0):
        self.value = value

    def __repr__(self):
        return f"{self.value*100}%"
    
    def __bool__(self):
        return bool(self.value)
    
    def __int__(self):
        return int(self.value)
    
    def __float__(self):
        return float(self.value)

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

    def __repr__(self):
        return f"{self.value}°"

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

    def __repr__(self):
        return f"{self.value/math.pi}πrad"

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