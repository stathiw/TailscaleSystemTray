# TailscaleSystemTray
A simple system tray application to interface with Tailscale.


## Install
1. Clone this repository
2. Install python3 requirements
`python3 -m pip install -r requirements.txt`
3. Install
`sudo ./setup.py install`

## Usage
Launch using the installed desktop application. 
![Screenshot from 2024-10-02 12-34-52](https://github.com/user-attachments/assets/a78309ac-f26b-4253-9dba-c290c7c92bdc)

The system tray icon should appear when you launch the application.

The icon will change colour depending on the state of Tailscale.

**Red** if Tailscale is down.

![Screenshot from 2024-10-02 12-37-29](https://github.com/user-attachments/assets/dfcf2edf-e2f2-45d6-97cd-9e16d191a34f)

**Blue** if Tailscale is up.

![Screenshot from 2024-10-02 12-37-09](https://github.com/user-attachments/assets/8e4a8f4b-af5c-4943-bc70-2c607f271084)

**Green** if Tailscale is up and you are connected to an exit-node.

![Screenshot from 2024-10-02 12-37-18](https://github.com/user-attachments/assets/1b52dcb0-980e-47b0-b972-ff659157d002)
