WARNING: This Remote Access Tool (RAT) is intended for educational and ethical purposes only.  
Unauthorized use or distribution of this software is illegal and may result in severe penalties.  
Use responsibly and with explicit permission from the target system owner.

DISCLAIMER:  
I am NOT responsible for any misuse, damage, or legal consequences caused by this software.  
This tool is provided "as is" for educational and authorized testing purposes only.  
Use at your own risk and always obtain proper permission before accessing any system.



Install all moudles and packages in the moudle.txt with this command
pip install -r moudle.txt

For others it might not work so try these instead
py -m pip install -r moudle.txt
py pip install -r moudle.txt
python -m pip install -r moudle.txt
python pip install -r moudle.txt
Have had these problems with many diffrent computers

Go to edit mode in Client.py, line 30
And change to your computers IPv4
Now you're done and run the Server.py first just like a normal executable file.
Diffrent for the Client.py, i crashes when trying to double click it.
So rather go to cmd in the same directory and run
python Client.py, or just run the "run client.bat" its the same.


If you're unsure of how to get your IPv4 address.
Open Command Promt and run this command

ipconfig

And copy the IPv4 address on your current running network.
Make sure its not on any non connected wifi networks else it wont work
Now replace this ip address into your client.py SERVER_IP = 
