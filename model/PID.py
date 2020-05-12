class PID:
    _Kp = 0.0
    _Ki = 0.0
    _Kd = 0.0

    _p_max = None
    _i_max = None
    _d_max = None

    _dT = 0.0

    _Setpoint = 0.0
    _err_prev = 0.0
    _err_sum = 0.0

    def __init__(self, setpoint=0.0, Kp=1.0, Ki=0.0, Kd=0.0, dt=0.0, p_max=None, i_max=None, d_max=None):
        self._Setpoint = setpoint
        self._Kp = Kp
        self._Ki = Ki
        self._Kd = Kd
        self._dT = dt

        self._p_max = p_max
        self._i_max = i_max
        self._d_max = d_max

        self._err_prev = 0.0
        self._err_sum = 0.0

    def p(self, pos):
        err = self._Setpoint - pos
        if self._p_max is not None:
            return min(self._Kp * err, self._p_max)
        else:
            return self._Kp * err

    def pd(self, pos):
        err = self._Setpoint - pos
        de_dt = (err - self._err_prev) / self._dT
        self._err_prev = err

        if self._d_max is not None:
            return self.p(pos) + min(self._Kd * de_dt, self._d_max)
        else:
            return self.p(pos) + self._Kd * de_dt

    def pid(self, pos):
        err = self._Setpoint - pos
        self._err_sum += err * self._dT

        if self._i_max is not None:
            return min(self._Ki * self._err_sum, self._i_max) + self.pd(pos)
        else:
            return self._Ki * self._err_sum + self.pd(pos)
