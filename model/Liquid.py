class Liquid:
    _heat_capacity = 0.0
    _temperature_c = 0.0
    _ambient_temperature_c = 0.0
    _k = 0.0
    _mass = 0.0

    HEAT_CAPACITY_WATER = 4200

    def __init__(self, k, initial_temperature_c=0.0, ambient_temperature_c=0.0, heat_capacity=HEAT_CAPACITY_WATER,
                 mass=1.0):
        self._k = k
        self._temperature_c = initial_temperature_c
        self._ambient_temperature_c = ambient_temperature_c
        self._heat_capacity = heat_capacity
        self._mass = mass

    @staticmethod
    def _newton_temperature(start_temp, ambient_temp, k, dt):
        return k * (ambient_temp - start_temp) * dt

    @staticmethod
    def get_temperature_change_celsius(joules, mass, c):
        # Q = m*c*delta_temp
        # Q = thermal energy (J)
        # m = mass
        # c = material's specific heat capacity (J/kg/C)
        # delta_temp = delta temperature (*C)
        return joules / (mass * c)

    def temperature_c(self):
        return self._temperature_c

    def idle(self, delta_time_s):
        ambient_temp_c = self._ambient_temperature_c
        delta_temp = Liquid._newton_temperature(self.temperature_c(),
                                                ambient_temp_c,
                                                self._k,
                                                delta_time_s)
        self._temperature_c += delta_temp
        return self.temperature_c()

    def apply_heat(self, heat_watts, time_sec):
        delta_temp_c = Liquid.get_temperature_change_celsius(heat_watts * time_sec, self._mass, self._heat_capacity)
        self._temperature_c += delta_temp_c
        return self.temperature_c()
