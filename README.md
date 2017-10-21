# DecaWaveEVB1000Collector
DecaWaveEVB1000 Collector is a tool that collect ranging, autoranging and trilateration data from DecaWave EVB1000 enabled devices.

Usage
------------
Python 3.x is required.

Libraries required are
 * pySerial
 * tqdm
 
- **On Linux:**
```
    $ git clone https://github.com/xEnVrE/DecaWaveEVB1000Collector.git
    $ cd DecaWaveEVB1000Collector.git
    $ python collector.py
```
> You may need to add your user to the group that owns serial port device files  (e.g. /dev/ttyACM0) to 
     execute the application succesfully. However you can always run the script as a super user like
     ```
     sudo python app.py
     ```

The application works also on Windows.
  
Configuration
-------------
The only thing you need to run the application is a configuration file `config.ini` containing the VIDs and PIDs of
USB serial ports you would like to use with the application.  
The structure of the file is quite simple
```
CONFIG_VID_PID
VID PID
<vid_1> <pid_1>
...
<vid_N> <pid_N>
```
