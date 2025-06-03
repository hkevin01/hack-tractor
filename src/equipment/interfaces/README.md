# Equipment Interfaces

This directory contains interfaces for communicating with various agricultural equipment.

## Interface Types

- `can/` - CAN bus communication interfaces
- `serial/` - Serial communication interfaces
- `modbus/` - Modbus protocol interfaces
- `obd/` - OBD-II port interfaces
- `john_deere/` - John Deere API interfaces
- `proprietary/` - Proprietary diagnostic port interfaces

## Hardware Support

- `hardware/` - Support for Raspberry Pi, Arduino, and other hardware interfaces

## Implementation Notes

- Each interface follows a common API pattern
- Safety mechanisms are implemented at the interface level
- Logging is enabled for all communication
