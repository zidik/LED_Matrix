#include "serial485bus.h"

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