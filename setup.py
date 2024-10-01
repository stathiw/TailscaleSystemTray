#!/usr/bin/env python3

import glob
import os
import subprocess

from setuptools import setup, Command

class InstallScripts(Command):
    description = "Installs the main python script and assets"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print('Installing tailscale-systray')
        
        # Install at /usr/share/tailscale-systray
        install_dir = "/usr/share/tailscale-systray"
        # os.makedirs(install_dir, exist_ok=True)
        # os.system(f"cp -r src/* {install_dir}")
        # os.system(f"cp assets/* {install_dir}")
        subprocess.run(["mkdir", "-p", install_dir])
        for file in glob.glob("src/*"):
            subprocess.run(["cp", "-r", file, install_dir])
        for file in glob.glob("assets/*"):
            subprocess.run(["cp", file, install_dir])

        # Install the desktop file
        desktop_file = "/usr/share/applications/tailscale-systray.desktop"
        subprocess.run(["cp", "tailscale-systray.desktop", desktop_file])


setup(
    name="tailscale-systray",
    version="0.1.0",
    description="Tailscale systray app",
    author="Stathi Weir",
    packages=["tailscale_systray"],
    cmdclass={
        "install": InstallScripts,
    },
    entry_points={"console_scripts": ["tailscale-systray=src.tailscale_systray:main"]},
)
