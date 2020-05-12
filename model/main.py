import matplotlib.pyplot as plt
import numpy as np

from PID import PID
from Liquid import Liquid


def model_liquid():
    amount_of_water_gallons = 2
    mass_of_water_kg = 3.785 * amount_of_water_gallons

    ambient_temperature_c = 20
    heater_watts = 1000.0

    initial_liquid_temperature_c = 20
    desired_liquid_temperature_c = 53

    # 1000 watt heater
    # 1 gallon of water = 3.785kg
    # Specific Heat Capacity of Water: 4,200 J per Kg per *C
    # Means: 4,200 Joules to raise the temperature of 1kg of water 1*C
    # W = J/sec

    # Raise temperature of 1 gallon of water 1*C:
    # 1 gallon = 3.785kg
    # (4,200J / kg / degC) * 3.785kg * 1*C = 15,897J
    # How much time does it take?
    # 1000W = 15897J / sec
    # sec = 15,897J / 1000W = 15.897 sec

    # Raise temperature of 3 gallons of water from 10C to 53C
    # with 1000W heater:
    # 3 gallons = 3 x 3.785kg = 11.355kg
    # delta_temperature_C = 43C
    # (4,200J / kg / degC) * (11.355kg) * (43C) = 2,050,713J
    # 2,050,713 J / 1000W = 2,050.713 seconds = 34.18 minutes

    liquid_k = 0.0001
    experiment_length_minutes = 60 * 1

    dT = 35
    time_sec = np.arange(0.0, experiment_length_minutes * 60.0, dT)

    liquid = Liquid(liquid_k, initial_temperature_c=initial_liquid_temperature_c,
                    ambient_temperature_c=ambient_temperature_c,
                    mass=mass_of_water_kg,
                    heat_capacity=Liquid.HEAT_CAPACITY_WATER)

    P, I, D = 1.0, 0.00001, 0.0
    # P, I, D = 1.0, 0.00001, 0.0
    pid = PID(desired_liquid_temperature_c, P, I, D, dT)

    temp_c = []
    err = []
    dc = []
    for i in range(len(time_sec)):
        t = time_sec[i]

        # duty_cycle is expected to be between 0-100
        duty_cycle = pid.pid(liquid.temperature_c())
        # print('duty_cycle: {:02f}'.format(duty_cycle))
        if duty_cycle > 1.0:
            duty_cycle = 1.0
        elif duty_cycle < 0:
            duty_cycle = 0

        dc.append(duty_cycle)

        # Simulate the duty cycle by applying heat for the first part
        # of the duty cycle, and then simply allowing the ambient temperature
        # to do its work for the rest of it
        time_on = duty_cycle * dT
        time_off = dT - time_on

        liquid.apply_heat(heater_watts, time_on)
        if time_off > 0:
            liquid.idle(time_off)

        temp_c.append(liquid.temperature_c())
        # print('Error: {}'.format(desired_liquid_temperature_c - liquid.temperature_c()))
        err.append(desired_liquid_temperature_c - liquid.temperature_c())

    plt.subplot(3, 1, 1)
    plt.plot(time_sec / 60.0, temp_c)
    plt.ylabel('Temperature (C)')
    plt.xlabel('Time (Minutes)')
    # plt.ylim([50, 55])
    # plt.ylim([desired_liquid_temperature_c - 5, desired_liquid_temperature_c + 5])
    plt.hlines(desired_liquid_temperature_c, 0, experiment_length_minutes)

    plt.subplot(3, 1, 2)
    plt.plot(time_sec / 60.0, err)
    plt.ylabel('Error (Deg. C)')
    plt.xlabel('Time (Minutes)')

    plt.subplot(3, 1, 3)
    plt.plot(time_sec / 60.0, dc)
    plt.ylabel('Duty Cycle (%)')
    plt.xlabel('Time (Minutes)')
    plt.show()


def main():
    model_liquid()


if __name__ == '__main__':
    main()
