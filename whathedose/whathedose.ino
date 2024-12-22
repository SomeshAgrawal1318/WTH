#include <LiquidCrystal_I2C.h>
#include <Wire.h>

#define BUTTON_PIN 4        // Button in the drawer
#define BUZZER_PIN 5        // Buzzer pin

LiquidCrystal_I2C lcd(0x27, 16, 2); // LCD with address 0x27 and 16x2 display

unsigned long previousMillis = 0; // For tracking simulated time
int seconds = 0, minutes = 0, hours = 0; // Simulated clock variables

bool alarmActive = false;         // Tracks if the alarm is active
bool lastButtonState = HIGH;      // Previous button state
unsigned long debounceTime = 50;  // Debounce time in milliseconds
unsigned long lastDebounceTime = 0;

// Pill schedule (customize as needed)
int pillSchedule[10][2];          // Max 10 pill times
int scheduleSize = 0;             // Number of pills in the schedule
int currentPillIndex = 0;         // Tracks the current pill in the schedule

void setup() {
    Serial.begin(9600); 
    lcd.init(); 
    lcd.backlight(); 

    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(BUZZER_PIN, OUTPUT);

    lcd.setCursor(0, 0);
    lcd.print("Smart Pill Box");
    delay(2000);
    lcd.clear();

    Serial.println("Setup complete.");
}

void loop() {
    updateClock();
    checkAlarm();
    handleButtonPress();
    handleSerialCommands();
}

void updateClock() {
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= 1000) {
        previousMillis = currentMillis;
        seconds++;

        if (seconds >= 60) {
            seconds = 0;
            minutes++;
        }
        if (minutes >= 60) {
            minutes = 0;
            hours++;
        }
        if (hours >= 24) {
            hours = 0;
        }

        displayTime();
    }
}

void displayTime() {
    lcd.setCursor(0, 0);
    lcd.print("Time: ");
    if (hours < 10) lcd.print("0");
    lcd.print(hours);
    lcd.print(":");
    if (minutes < 10) lcd.print("0");
    lcd.print(minutes);
    lcd.print("     "); // Clear leftover characters

    lcd.setCursor(0, 1);
    if (scheduleSize > 0) {
        lcd.print("Next: ");
        if (pillSchedule[currentPillIndex][0] < 10) lcd.print("0");
        lcd.print(pillSchedule[currentPillIndex][0]);
        lcd.print(":");
        if (pillSchedule[currentPillIndex][1] < 10) lcd.print("0");
        lcd.print(pillSchedule[currentPillIndex][1]);
    } else {
        lcd.print("No Schedule    ");
    }
}

void checkAlarm() {
    if (scheduleSize > 0 && hours == pillSchedule[currentPillIndex][0] && minutes == pillSchedule[currentPillIndex][1] && !alarmActive) {
        alarmActive = true;
        Serial.println("Time to take a pill! Alarm activated.");
        tone(BUZZER_PIN, 1000);
    }
}

void handleButtonPress() {
    int buttonState = digitalRead(BUTTON_PIN);
    if (buttonState != lastButtonState) {
        lastDebounceTime = millis();
    }

  
    if (buttonState == HIGH && lastButtonState == LOW) {
        if (alarmActive) {
            alarmActive = false;
            noTone(BUZZER_PIN);      // Turn off buzzer
            Serial.println("Pill taken, alarm deactivated.");
            moveToNextPill();
        }
    }


    lastButtonState = buttonState;
}

void moveToNextPill() {
    currentPillIndex++;
    if (currentPillIndex >= scheduleSize) {
        currentPillIndex = 0; // Reset to the first pill
    }
    displayTime();
}

void handleSerialCommands() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command.startsWith("SET_TIME")) {
            String time = command.substring(9);
            int newHours = time.substring(0, 2).toInt();
            int newMinutes = time.substring(3, 5).toInt();
            hours = newHours;
            minutes = newMinutes;
            seconds = 0;
            Serial.println("Time updated");
        } else if (command.startsWith("ADD_PILL")) {
            if (scheduleSize < 10) {
                String time = command.substring(9);
                int pillHour = time.substring(0, 2).toInt();
                int pillMinute = time.substring(3, 5).toInt();
                pillSchedule[scheduleSize][0] = pillHour;
                pillSchedule[scheduleSize][1] = pillMinute;
                scheduleSize++;
                Serial.println("Pill time added");
            } else {
                Serial.println("Error: Schedule full");
            }
        } else if (command.startsWith("SET_SCHEDULE")) {
            String schedule = command.substring(13);
            scheduleSize = 0;
            while (schedule.length() > 0 && scheduleSize < 10) {
                int spaceIndex = schedule.indexOf(' ');
                String time;
                if (spaceIndex == -1) {
                    time = schedule;
                    schedule = "";
                } else {
                    time = schedule.substring(0, spaceIndex);
                    schedule = schedule.substring(spaceIndex + 1);
                }
                int pillHour = time.substring(0, 2).toInt();
                int pillMinute = time.substring(3, 5).toInt();
                pillSchedule[scheduleSize][0] = pillHour;
                pillSchedule[scheduleSize][1] = pillMinute;
                scheduleSize++;
            }
            currentPillIndex = 0;
            Serial.println("Schedule updated");
        } else if (command == "RESET_ALARM") {
            alarmActive = false;
            noTone(BUZZER_PIN);
            Serial.println("Alarm reset");
        } else {
            Serial.println("Unknown command");
        }

        displayTime();
    }
}
