package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"path"
	"strconv"
	"strings"
	"time"

	"github.com/felixge/pidctrl"
)

func CelsiusToFahrenheit(celsius float64) float64 {
	return (celsius * 9.0 / 5.0) + 32.0
}

func FahrenheitToCelsius(fahrenheit float64) float64 {
	return (fahrenheit - 32.0) * (5.0 / 9.0)
}

func readTemperatureDegreesC(sensorName string) (float64, error) {
	devicePath := path.Join("/", "sys", "bus", "w1", "devices", sensorName, "w1_slave")

	contents, err := ioutil.ReadFile(devicePath)
	if err != nil {
		log.Printf("Failed to open device file: %v", err)
		return 0.0, err
	}

	resultString := string(contents)
	elements := strings.Split(resultString, " ")
	lastOne := elements[len(elements)-1]
	tParts := strings.Split(lastOne, "=")
	tempCString := strings.TrimSpace(tParts[len(tParts)-1])
	tempCx1000, err := strconv.Atoi(tempCString)
	if err != nil {
		log.Printf("Failed to convert string to number: %v", err)
		return 0.0, err
	}

	tempC := float64(tempCx1000) / 1000.0
	return tempC, nil
}

func setGpioValue(gpio int, value bool) error {
	gpioValue := path.Join("/", "sys", "class", "gpio", fmt.Sprintf("gpio%d", gpio), "value")

	outputString := "0"
	if value {
		outputString = "1"
	}

	if err := ioutil.WriteFile(gpioValue, []byte(outputString), 0644); err != nil {
		return err
	}
	return nil
}

func enableGpio(gpio int) error {
	gpioDir := path.Join("/", "sys", "class", "gpio", fmt.Sprintf("gpio%d", gpio))
	if stat, err := os.Stat(gpioDir); err != nil {
		return err
	} else if !stat.IsDir() {
		filename := path.Join("/", "sys", "class", "gpio", "export")
		if err := ioutil.WriteFile(filename, []byte(fmt.Sprintf("%d\n", gpio)), 0644); err != nil {
			return err
		}
	}

	gpioDirFile := path.Join(gpioDir, "direction")
	log.Printf("Direction file: %v", gpioDirFile)
	if err := ioutil.WriteFile(gpioDirFile, []byte("out\n"), 0644); err != nil {
		return err
	}

	return setGpioValue(gpio, false)
}

func logTemperature(tempC float64) {
	f, err := os.OpenFile("temperature_log.txt", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Fatalf("Failed to open file for appending: %v", err)
	}
	defer f.Close()

	if _, err := f.WriteString(fmt.Sprintf("%v\n", tempC)); err != nil {
		log.Fatalf("Failed to write temperature to file: %v", err)
	}
}

func executeDutyCycle(period time.Duration, percentage float64, heaterGpio int) {
	if percentage < 0 || percentage > 1 {
		log.Fatalf("percentage must be between 0 and 1")
	}

	if period < 0 {
		log.Fatalf("Invalid period (must be > 0): %v", period)
	}

	timeOnSeconds := time.Duration(float64(period) * percentage)
	timeOffSeconds := period - timeOnSeconds

	log.Printf("Duty Cycle: %v, On/Off: %v/%v", percentage, timeOnSeconds, timeOffSeconds)

	if timeOnSeconds > 0 {
		if err := setGpioValue(heaterGpio, true); err != nil {
			log.Fatalf("Failed to set heater value: %v", err)
		}
		time.Sleep(timeOnSeconds)
	}

	if timeOffSeconds > 0 {
		if err := setGpioValue(heaterGpio, false); err != nil {
			log.Fatalf("Failed to turn heater off: %v", err)
		}
		time.Sleep(timeOffSeconds)
	}
}

const (
	SteakSetpointF = 129.0
	PorkSetpointF = 145.0
)

func main() {
	const p, i, d = 1.0, 0.00001, 0.0
	const setPoint_f = PorkSetpointF
	const minPercent, maxPercent = 0.0, 1.0
	const periodSeconds = time.Duration(time.Second * 35)
	const temperatureSensor = "28-00000ac851cb"
	const logFilename = "temperature.log"
	const powerGpio = 14

	logFile, err := os.OpenFile(logFilename, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}
	multiwriter := io.MultiWriter(os.Stdout, logFile)
	log.SetOutput(multiwriter)
	defer logFile.Close()

	if tempC, err := readTemperatureDegreesC(temperatureSensor); err != nil {
		log.Fatalf("Failed to read temperature: %v", err)
	} else {
		log.Printf("Temperature: %v C (%v F)", tempC, CelsiusToFahrenheit(tempC))
	}

	if err := enableGpio(powerGpio); err != nil {
		log.Fatalf("Failed to enable GPIO: %v", err)
	}

	temperatureSetpointC := FahrenheitToCelsius(setPoint_f)

	log.Printf("Setpoint: %vC", temperatureSetpointC)

	pid := pidctrl.NewPIDController(p, i, d)
	pid.Set(temperatureSetpointC)
	pid.SetOutputLimits(minPercent, maxPercent)

	for {
		if tempC, err := readTemperatureDegreesC(temperatureSensor); err != nil {
			log.Fatalf("Failed to read temperature: %v", err)
		} else {
			log.Printf("Temperature: %v C, Target: %v C", tempC, temperatureSetpointC)
			percentage := pid.Update(tempC)

			// Executing this duty cycle sleeps for the appropriate amount of time
			executeDutyCycle(periodSeconds, percentage, powerGpio)
		}
	}
}
