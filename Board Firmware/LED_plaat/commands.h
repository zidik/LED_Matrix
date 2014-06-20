#ifndef COMMANDS_H
#define COMMANDS_H

enum Command
{
	LedData        = 0x21, //Master sends data to LED's
	ReqSensor      = 0x3F, //Master requests current sensor value
	ResetID        = 0x20, //Master forces to reset id
	OfferID        = 0x23, //Master is offering a new ID
	PingFromMaster = 0x24, //Master pings board
	OfferSeqNo     = 0x26, //Master is offering a Bus Sequence Number
	UNUSED         = 0x00, //TODO: TEST REMOVAL OF THIS

	PongToMaster   = 0x25, //Board responds to Master's ping
	RequestID      = 0x22, //Board requests ID from Master
	


};

#endif
	