#ifndef COMMANDS_H
#define COMMANDS_H

enum Command
{
	// From Master to Board
	ResetID        = 0x01, //Master forces to reset id
	OfferID        = 0x03, //Master is offering a new ID
	PingFromMaster = 0x04, //Master pings board
	OfferSeqNo     = 0x06, //Master is offering a Bus Sequence Number
	LedData        = 0x10, //Master sends data to LED's
	ReqSensor      = 0x11, //Master requests current sensor value

	ReqInfo        = 0x1D, //Master requests information about board (version number, id etc.)
	
	// From Board to Master
	RequestID      = 0x02, //Board requests ID from Master
	PongToMaster   = 0x05, //Board responds to Master's ping
	SensorData     = 0x12, //Board sends sensor value to Master

	Info           = 0x1E, //Board sends information about itself (version number, id etc.)
	DebugData      = 0x1F, //Board sends debug data to master

};

#endif
	