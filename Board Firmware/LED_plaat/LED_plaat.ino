#include <EEPROM.h>
#include <Adafruit_NeoPixel.h>
#include "serial485bus.h"
#include "commands.h"

template<class T> inline Print &operator <<(Print &obj, T arg) { obj.print(arg); return obj; } //Add streaming operator to Serial


#define BROADCAST_ID  255  // ASCII character number that all boards listen to on serial port
#define UNUSED_ID     254  // ASCII character number that all boards ignore on serial port. Only master listens to it

#define NO_OF_PIXELS  100  // Number of leds on board
#define LED_PIN        11  // Pin the LEDs are attached to
#define BUFFER_SIZE   300  // Buffer for commands coming from serial

#define VERSIONSTRING F("0.9.10")


// Gamma correction improves appearance of midrange colors
const uint8_t PROGMEM gamma8[] = {
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
	1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3,
	3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 7,
	7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12,
	13, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20,
	20, 21, 21, 22, 22, 23, 24, 24, 25, 25, 26, 27, 27, 28, 29, 29,
	30, 31, 31, 32, 33, 34, 34, 35, 36, 37, 38, 38, 39, 40, 41, 42,
	42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
	58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 69, 70, 71, 72, 73, 75,
	76, 77, 78, 80, 81, 82, 84, 85, 86, 88, 89, 90, 92, 93, 94, 96,
	97, 99, 100, 102, 103, 105, 106, 108, 109, 111, 112, 114, 115, 117, 119, 120,
	122, 124, 125, 127, 129, 130, 132, 134, 136, 137, 139, 141, 143, 145, 146, 148,
	150, 152, 154, 156, 158, 160, 162, 164, 166, 168, 170, 172, 174, 176, 178, 180,
	182, 184, 186, 188, 191, 193, 195, 197, 199, 202, 204, 206, 209, 211, 213, 215,
	218, 220, 223, 225, 227, 230, 232, 235, 237, 240, 242, 245, 247, 250, 252, 255
};

Adafruit_NeoPixel led_matrix = Adafruit_NeoPixel(NO_OF_PIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

uint8_t boardID = BROADCAST_ID;
uint8_t busSeqNo = 255;

char cmd_buffer[BUFFER_SIZE];  // a buffer to hold incoming command
uint16_t cmd_index = 0;
boolean cmd_started = false;  // whether currently reading a cmd to the buffer
boolean cmd_complete = false;  // whether the command string is complete

unsigned long last_id_request_time = 0;
boolean boardID_requested = false;

void setup() {
	led_matrix.begin();
	led_matrix.show();			//Switch LED's
	boardID = loadBoardID();	//Load ID from EEPROM
	//Serial direction pins
	pinMode(2, OUTPUT);			//NOT Receiveing Enable
	pinMode(A5, OUTPUT);		//Driver Enable
	set_serial_mode(Off);
	Serial.begin(500000);

	//Test sequence if pin 12 is pulled down externally
	const int testPin = 12;
	pinMode(testPin, INPUT_PULLUP);
	if (digitalRead(testPin) == LOW){
		fillPixels(led_matrix.Color(0xFF, 0x00, 0x00));
		delay(700);
		fillPixels(led_matrix.Color(0x00, 0xFF, 0x00));
		delay(700);
		fillPixels(led_matrix.Color(0x00, 0x00, 0xFF));
		delay(700);
		fillPixels(led_matrix.Color(0xFF, 0xFF, 0xFF));
		delay(700);
		fillPixels(led_matrix.Color(0x00, 0x00, 0x00));
	}
	pinMode(testPin, INPUT);

	set_serial_mode(Receive);
	//Clean up Serial buffers before reading again
	while (Serial.available()) { Serial.read(); }
}




void loop() {
	if (cmd_complete) {
		/*
		//DEBUG
		set_serial_mode(Send);
		Serial << (char)(boardID == BROADCAST_ID ? 0xFE : boardID) << F("RECEIVED!") << (uint8_t)cmd_buffer[0] << " " << (uint8_t)cmd_buffer[1] << " " << (uint8_t)cmd_buffer[2] << " " << (uint8_t)cmd_buffer[3] << cmd_index << (char)DebugData;
		Serial.flush();
		set_serial_mode(Receive);
		///
		*/

		switch (cmd_buffer[cmd_index]) {
		case (char)LedData:
			// This is needed to keep board from being unavailable while master is not yet sent bus sequence number
			if (busSeqNo == 255)
				break;

			setPixels((uint8_t*)cmd_buffer);
			led_matrix.show();

			//Data in Serial buffers is partial ("show" function disabled interrupts)
			//Clean up Serial buffers before reading again
			while (Serial.available()) { Serial.read(); }
			break;

		case (char)ReqSensor:{
			if (busSeqNo == 255)
				break;

			unsigned long startTime = micros();
			int resultADC = analogRead(2); //Takes about 100microseconds
			uint16_t slotTime = 400; // time in microseconds given for each board on bus
			//each responds in order, delaying proportionally to it's Sequence No
			unsigned long sendTime = (unsigned long)busSeqNo * slotTime + 100; //analogRead takes ~100us
			while (micros() - startTime < sendTime){} //Wait here for your turn to speak
			set_serial_mode(Send);
			Serial << (char)boardID << resultADC << (char)SensorData;
			Serial.flush();
			set_serial_mode(Receive);
			//Clean up Serial buffers before reading again
			while (Serial.available()) { Serial.read(); }
		} break;

		case (char)ReqInfo:{
			//TODO: Board does not need to wait, if it was an UNICAST
			uint16_t slotTime = 500; // time in microseconds given for each board on bus
			delayMicroseconds((boardID - 128) * slotTime + 1); // +1, because delayMicroseconds(0) delay's for maximum ammount
			set_serial_mode(Send);
			Serial << (char)boardID << VERSIONSTRING << (char)Info;
			Serial.flush();
			set_serial_mode(Receive);
			//Clean up Serial buffers before reading again
			while (Serial.available()) { Serial.read(); }
			}
			break;

		case (char)ResetID:
			if (cmd_index != 3)
				break;

			if (cmd_buffer[0] != 'R' ||
				cmd_buffer[1] != 'S' ||
				cmd_buffer[2] != 'T' )
				break;

			boardID = BROADCAST_ID;
			saveBoardID();
			busSeqNo = 255;
			break;

		case (char)OfferID:
			if (boardID_requested && cmd_index == 1){
				fillPixels(led_matrix.Color(0, 0, 0));
				//Clean up Serial buffers before reading again
				while (Serial.available()) { Serial.read(); }
				boardID_requested = false;
				boardID = cmd_buffer[0];
				saveBoardID();
			}
			//If somebody hears it's id given away - it looks like master sent only "[id] [OfferID]"
			if (cmd_index == 0){
				/*
				//DEBUG
				set_serial_mode(Send);
				Serial << (char)(boardID == BROADCAST_ID ? 0xFE : boardID) << F("LOST ID") << (char)DebugData;
				Serial.flush();
				set_serial_mode(Receive);
				///
				*/

				boardID = BROADCAST_ID;
				saveBoardID();
			}
			break;

		case (char)PingFromMaster:
			{
				//TODO: Board does not need to wait, if it was an UNICAST
				//each board responds to a ping in order, delaying proportionally to it's ID
				//TODO: speedup ping by reducing slot time
				uint16_t slotTime = 300; // time in microseconds given for each board on bus
				delayMicroseconds((boardID - 128) * slotTime + 1); // +1, because delayMicroseconds(0) delay's for maximum ammount
				set_serial_mode(Send);
				Serial << (char)boardID << (char)PongToMaster;
				Serial.flush();
				set_serial_mode(Receive);
				while (Serial.available()) { Serial.read(); }
			}
			break;

		case (char)OfferSeqNo:
			busSeqNo = cmd_buffer[0] & B00111111;
			busSeqNo += /*(uint16_t)*/(cmd_buffer[1] & B00111111) << 6;
			
			//DEBUG
			//set_serial_mode(Send);
			//Serial << (char)(boardID == BROADCAST_ID ? 0xFE : boardID) << F("RECEIVED!") << (uint8_t)cmd_buffer[0] << " " << (uint8_t)cmd_buffer[1] << " " << (uint8_t)cmd_buffer[2] << " " << (uint8_t)cmd_buffer[3] << cmd_index << (char)DebugData;
			//Serial << (char)(boardID == BROADCAST_ID ? 0xFE : boardID) << F("RECEIVED SEQ NO") << busSeqNo << (char)DebugData;
			//Serial.flush();
			//set_serial_mode(Receive);
			///
			

			break;
		}
		cmd_complete = false;
	}
	//IF no board ID is set (it is the same as BC_ID) then just wait for buttonpress
	if (boardID == BROADCAST_ID){
		//if request has just been sent don't get stuck here again for a while
		if (last_id_request_time + 200 < millis() || last_id_request_time == 0){
			//Inform user, that we are waiting for push
			fillPixels(led_matrix.Color(0, 0, 0));
			led_matrix.setPixelColor(0, led_matrix.Color(120, 0, 0));
			led_matrix.show();
			//fillPixels(led_matrix.Color(40, 0, 0));
			//Wait until button is pressed
			while (analogRead(2) < 100){}
			//Inform user, that push has been registred
			led_matrix.setPixelColor(0, led_matrix.Color(80, 80, 80));
			led_matrix.show();
			//fillPixels(led_matrix.Color(40, 40, 40));
			last_id_request_time = millis();
			boardID_requested = true;
			set_serial_mode(Send);
			//This is here to make next emptying faster
			while (Serial.available()) { Serial.read(); }
			Serial << (char)UNUSED_ID << (char)RequestID;
			Serial.flush();
			set_serial_mode(Receive);
			//Empty input buffer
			while (Serial.available()) { Serial.read(); }
		}
	}
}

void serialEvent() {
	//Last command has not been consumed (yet) 
	if (cmd_complete){
		return;
	}

	char inChar = (char)Serial.read();

	if (cmd_started){
		cmd_buffer[cmd_index] = inChar;
		if (
			inChar == (char)ResetID        ||
			inChar == (char)OfferID        ||
			inChar == (char)PingFromMaster ||
			inChar == (char)OfferSeqNo     ||
			inChar == (char)LedData        ||
			inChar == (char)ReqSensor      ||
			inChar == (char)ReqInfo
			){
			cmd_complete = true;
			cmd_started = false;
		}
		else{
			if (cmd_index < BUFFER_SIZE - 1){
				cmd_index++;
			}

		}
	}

	if (inChar == (char)boardID || inChar == (char)BROADCAST_ID){
		cmd_started = true;
		cmd_index = 0;
	}

	
}

void setPixels(uint8_t *input_data) {
	uint8_t data_side = 1; // Määrab ära, missugused 3 bitti järgmisena loetakse kas xx000xxx või xxxxx000
	uint32_t color;        //Current color value
	uint8_t data;          //Data recieved and decoded from serial 
	uint8_t intensity;     //Intensity calculated from gammacorrection


	for (uint8_t i = 0; i < NO_OF_PIXELS; i++){
		color = 0;
		for (uint8_t color_nr = 0; color_nr < 3; color_nr++){
			if (data_side == 1){
				data = ((*input_data & B00111000) << 2);
				data_side = 2;
			}
			else if (data_side == 2) {
				data = ((*input_data & B00000111) << 5);
				input_data++;
				data_side = 1;
			}
			else { data = 0; } //ERR
			intensity = pgm_read_byte(&gamma8[data]);
			//Serial.println(data);
			//Serial.println(((2-color_nr)*8));
			//Serial.println(((uint32_t)data << ((2-color_nr)*8)));
			color |= ((uint32_t)intensity << ((2 - color_nr) * 8));
			//Serial.println(color);
		}
		//Serial.println(color);
		led_matrix.setPixelColor(i, color);
	}
}

void fillPixels(uint32_t color){
	for (uint8_t i = 0; i < NO_OF_PIXELS; i++){
		led_matrix.setPixelColor(i, color);
	}
	led_matrix.show();
}

void saveBoardID(){
	EEPROM.write(0, boardID);
}

uint8_t loadBoardID(){
	EEPROM.read(0);
}




