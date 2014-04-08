template<class T> inline Print &operator <<(Print &obj, T arg) { obj.print(arg); return obj; } //Add streaming operator to Serial (

#include <Adafruit_NeoPixel.h>


#define BOARD_ID      129  // ASCII character number that this board listens to on serial port
#define BROADCAST_ID  255 // ASCII character number that this board listens to on serial port
#define NO_OF_PIXELS  100  // Number of leds on board
#define LED_PIN        11  // Pin the LEDs are attached to
#define BUFFER_SIZE   300  // Buffer for commands coming from serial

#define CLR(x,y) (x&=(~(1<<y)))
#define SET(x,y) (x|=(1<<y))

// common colors for convinience
#define LED_RED   led_matrix.Color(10, 0, 0)
#define LED_GREEN led_matrix.Color(0, 10, 0)
#define LED_BLUE  led_matrix.Color(0, 0, 10)
#define LED_OFF   led_matrix.Color(0, 0, 0)

// Gamma correction improves appearance of midrange colors
const uint8_t PROGMEM gamma8[] = {
      0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
      0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  1,  1,  1,
      1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,  2,  3,  3,  3,  3,
      3,  3,  4,  4,  4,  4,  5,  5,  5,  5,  5,  6,  6,  6,  6,  7,
      7,  7,  8,  8,  8,  9,  9,  9, 10, 10, 10, 11, 11, 11, 12, 12,
     13, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20,
     20, 21, 21, 22, 22, 23, 24, 24, 25, 25, 26, 27, 27, 28, 29, 29,
     30, 31, 31, 32, 33, 34, 34, 35, 36, 37, 38, 38, 39, 40, 41, 42,
     42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
     58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 69, 70, 71, 72, 73, 75,
     76, 77, 78, 80, 81, 82, 84, 85, 86, 88, 89, 90, 92, 93, 94, 96,
     97, 99,100,102,103,105,106,108,109,111,112,114,115,117,119,120,
    122,124,125,127,129,130,132,134,136,137,139,141,143,145,146,148,
    150,152,154,156,158,160,162,164,166,168,170,172,174,176,178,180,
    182,184,186,188,191,193,195,197,199,202,204,206,209,211,213,215,
    218,220,223,225,227,230,232,235,237,240,242,245,247,250,252,255
};


Adafruit_NeoPixel led_matrix = Adafruit_NeoPixel(NO_OF_PIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

char cmd_buffer[BUFFER_SIZE];  // a buffer to hold incoming command

uint16_t cmd_index = 0;
boolean cmd_complete = false;  // whether the command string is complete


void setup() {
  led_matrix.begin();
  led_matrix.show();  //Switch LED's
  //Serial direction pins
  pinMode(2, OUTPUT);    //NOT Receiveing Enable
  pinMode(A5, OUTPUT);   //Driver Enable
  serial_mode(false); //Receiving mode
  Serial.begin(500000);
}

void loop() {  
  if (cmd_complete) {
    switch (cmd_buffer[cmd_index]) {
    /*case char(0):
      serial_mode(true); //Sending mode
      Serial << "<" << cmd_buffer << ':' << cmd_index << ">";
      Serial.flush();
      serial_mode(false); //Receiving mode
      break;
      */
    case '!':
      setPixels((uint8_t*)cmd_buffer);
      //Not needed anymore, as flushing is always done before:
      Serial.flush();    //Ensure everything is sent before disabling interrupts
      led_matrix.show();
      break;
    case '?':
      delayMicroseconds((BOARD_ID-128)*500+1); // delayMicroseconds(0) will wait for 16ms!!
      serial_mode(true); //Sending mode
      int result = analogRead(2);
      Serial << (char)BOARD_ID << result << '.';
      Serial.flush();
      serial_mode(false); //Receiving mode
    }

    cmd_complete = false;
  }
  
  serialPart();
}

void setPixels(uint8_t *input_data) {
  uint8_t data_side = 1; // Määrab ära, missugused 3 bitti järgmisena loetakse kas xx000xxx või xxxxx000
  uint32_t color;    //Current color value
  uint8_t data;      //Data recieved and decoded from serial 
  uint8_t intensity;  //Intensity calculated from gammacorrection
  

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
      else {data = 0;/*ERR*/}
      intensity = pgm_read_byte(&gamma8[data]);
      //Serial.println(data);
      //Serial.println(((2-color_nr)*8));
      //Serial.println(((uint32_t)data << ((2-color_nr)*8)));
      color |= ((uint32_t)intensity << ((2-color_nr)*8));
      //Serial.println(color);
    }
    //Serial.println(color);
    led_matrix.setPixelColor(i, color);
  }
}

//Set serial in sending or receiving mode
// true -  send
// false - receive
void serial_mode(bool sending){
  if(sending){    
    SET(PORTD, 2);
    SET(PORTC, 5);
  }
  else{
    CLR(PORTC, 5);
    CLR(PORTD, 2);
  }
}


void serialPart() {  
  boolean cmd_started  = false;
  
  while (Serial.available() || cmd_started) {
     
    while(!Serial.available()) {} //Block here until recieve   //TODO: timeout
    char inChar = (char)Serial.read();
    
    if(cmd_started){
      cmd_buffer[cmd_index] = inChar;
      if (inChar == (char)0 || inChar == '!' || inChar == '?'){
        cmd_complete = true; //currently it will return buffer contents fo debugging
        cmd_started = false;
      }
      else{
        if (cmd_index < BUFFER_SIZE-1){
          cmd_buffer[cmd_index++] = inChar;
        }
      }
    }
    
    if (inChar == (char)BOARD_ID || inChar == (char) BROADCAST_ID ){
      cmd_started = true;
      cmd_index = 0;
      /*
      if(inChar == (char)BOARD_ID){
        serial_mode(true); //Sending mode
        Serial.print(inChar); //ACK with own ID!
        Serial.flush();
        serial_mode(false); //Receiving mode
      }
      */
    }
  }
}
