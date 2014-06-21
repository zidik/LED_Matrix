#include "serial485bus.h"
#include <Arduino.h>

#define CLR(x,y) (x&=(~(1<<y)))
#define SET(x,y) (x|=(1<<y))

void set_serial_mode(SerialMode mode){
	switch (mode)
	{
	case Off:
		CLR(PORTC, 5);
		SET(PORTD, 2);
		break;
	case Send:
		SET(PORTD, 2);
		SET(PORTC, 5);
		break;
	case Receive:
		CLR(PORTC, 5);
		CLR(PORTD, 2);
		break;
	case SendReceive:
		SET(PORTC, 5);
		CLR(PORTD, 2);
		break;
	}
}