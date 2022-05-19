#include <multi_channel_relay.h>

/**
    channle: 4 3 2 1
    state: 0b0000 -> 0x00  (all off)
    state: 0b1111 -> 0x0f   (all on)
*/

Multi_Channel_Relay relay;
const int buttonPin1 = 2;     // the number of pins of the interface to the lopy
const int buttonPin2 = 3;
const int buttonPin3 = 4;
const int buttonPin4 = 5;

int buttonState1 = 0; 
int buttonState2 = 0;
int buttonState3 = 0;
int buttonState4 = 0;

void setup() {

  //Declare the pins of the interface as inputs
    pinMode(buttonPin1, INPUT);
    pinMode(buttonPin2, INPUT);
    pinMode(buttonPin3, INPUT);
    pinMode(buttonPin4, INPUT);


    
    DEBUG_PRINT.begin(9600);
    while (!DEBUG_PRINT);

    // Set I2C address and start relay
    relay.begin(0x11);

    /* Begin Controlling Relay */
    DEBUG_PRINT.println("Channel 1 on");
    relay.turn_on_channel(1);
    delay(500);
    DEBUG_PRINT.println("Channel 2 on");
    relay.turn_off_channel(1);
    relay.turn_on_channel(2);
    delay(500);
    DEBUG_PRINT.println("Channel 3 on");
    relay.turn_off_channel(2);
    relay.turn_on_channel(3);
    delay(500);
    DEBUG_PRINT.println("Channel 4 on");
    relay.turn_off_channel(3);
    relay.turn_on_channel(4);
    delay(500);
    relay.turn_off_channel(4);

    relay.channelCtrl(CHANNLE1_BIT |
                      CHANNLE2_BIT |
                      CHANNLE3_BIT |
                      CHANNLE4_BIT);
    DEBUG_PRINT.print("Turn all channels on, State: ");
    DEBUG_PRINT.println(relay.getChannelState(), BIN);

    delay(2000);

    relay.channelCtrl(CHANNLE1_BIT |
                      CHANNLE3_BIT);
    DEBUG_PRINT.print("Turn 1 3 channels on, State: ");
    DEBUG_PRINT.println(relay.getChannelState(), BIN);

    delay(2000);

    relay.channelCtrl(CHANNLE2_BIT |
                      CHANNLE4_BIT);
    DEBUG_PRINT.print("Turn 2 4 channels on, State: ");
    DEBUG_PRINT.println(relay.getChannelState(), BIN);

    delay(2000);


    relay.channelCtrl(0);
    DEBUG_PRINT.print("Turn off all channels, State: ");
    DEBUG_PRINT.println(relay.getChannelState(), BIN);

    delay(2000);
}

void loop() {
  
//Read the pins  
  buttonState1 = digitalRead(buttonPin1);
  buttonState2 = digitalRead(buttonPin2);
  buttonState3 = digitalRead(buttonPin3);
  buttonState4 = digitalRead(buttonPin4);


 //******************************
//  RLY 3
  if (buttonState1 == HIGH) {
    // turn LED on:
    //digitalWrite(ledPin, HIGH);
    relay.turn_on_channel(1);
  } else {
    // turn LED off:
    //digitalWrite(ledPin, LOW);
     relay.turn_off_channel(1);
  }



//******************************
//  RLY 2
  if (buttonState2 == HIGH) {
    // turn LED on:
    //digitalWrite(ledPin, HIGH);
    relay.turn_on_channel(2);
  } else {
    // turn LED off:
    //digitalWrite(ledPin, LOW);
     relay.turn_off_channel(2);
  }
//******************************
//  RLY 3
    if (buttonState3 == HIGH) {
    // turn LED on:
    //digitalWrite(ledPin, HIGH);
    relay.turn_on_channel(3);
  } else {
    // turn LED off:
    //digitalWrite(ledPin, LOW);
     relay.turn_off_channel(3);
  }

//**************************
//RLY 4
  if (buttonState4 == HIGH) {
    // turn LED on:
    //digitalWrite(ledPin, HIGH);
    relay.turn_on_channel(4);
  } else {
    // turn LED off:
    //digitalWrite(ledPin, LOW);
     relay.turn_off_channel(4);
  }
  
}
