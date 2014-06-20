#ifndef SERIAL486BUS_H
#define SERIAL486BUS_H

enum SerialMode
{
	Off,
	Send,
	Receive,
	SendReceive
};

void set_serial_mode(SerialMode mode);

#endif