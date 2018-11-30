# raspberry
Raspberry code to video submission
## Setup
1. Install OpenCV library `$ sudo apt-get install libopencv-dev python-opencv`
2. Create virtualenv `$ virtualenv --system-site-packages -p python3 venv`
3. Activate virtualenv `$ source venv/bin/activate`
4. Install requirements `$ pip install -r requirements.txt`


## Common errors and solutions

- `ImportError: libcblas.so.3: cannot open shared object file: No such file or directory`  
`sudo apt-get install libatlas-base-dev`
- `ImportError: libjasper.so.1: cannot open shared object file: No such file or directory`  
`sudo apt-get install libjasper-dev`
- `ImportError: libQtGui.so.4: cannot open shared object file: No such file or directory`  
`sudo apt-get install libqtgui4`
- `ImportError: libQtTest.so.4: cannot open shared object file: No such file or directory`  
`sudo apt install libqt4-test`


## Run
- Activate virtualenv `$ source venv/bin/activate`
- Run `python3 main.py -h` to get help