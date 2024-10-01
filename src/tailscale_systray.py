import os
import time
import subprocess
import json
from threading import Thread
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib

class TailscaleInterface:
    def __init__(self):
        self.exit_node = ""
        self.exit_node_enabled = self.is_exit_node_enabled()
        self.indicator = AppIndicator3.Indicator.new(
            "Tailscale Status",
            "indicator-messages",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.available_exit_nodes = self.get_available_exit_nodes()
        self.selected_exit_node = None

        # Add a menu with:
        # - toggle button to enable/disable exit node
        # - a list of available exit nodes
        # - a quit option
        self.menu = Gtk.Menu()

        # Exit Node Enabled Toggle
        exit_node_enabled_item = Gtk.CheckMenuItem("Enable Exit Node")
        exit_node_enabled_item.set_active(self.exit_node_enabled)
        exit_node_enabled_item.connect("toggled", self.toggle_exit_node)
        self.menu.append(exit_node_enabled_item)

        # Available Exit Nodes Dropdown
        self.exit_nodes_menu = Gtk.Menu()
        group = []
        for node in self.available_exit_nodes:
            menu_item = Gtk.RadioMenuItem.new_with_label(group, node)
            menu_item.set_active(False)
            group.append(menu_item)
            menu_item.connect("activate", self.select_exit_node, node)
            self.exit_nodes_menu.append(menu_item)


        exit_nodes_item = Gtk.MenuItem("Exit Nodes")
        exit_nodes_item.set_submenu(self.exit_nodes_menu)
        self.menu.append(exit_nodes_item)

        quit_item = Gtk.MenuItem("Quit")
        quit_item.connect("activate", Gtk.main_quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        # Start a background thread to update the icon
        thread = Thread(target=self.update_icon)
        thread.daemon = True
        thread.start()

        Gtk.main()

    def is_exit_node_enabled(self):
        # Get exit node status
        peers_json = json.loads(subprocess.run(["tailscale", "status", "--peers", "--json"], stdout=subprocess.PIPE).stdout)
        # If peers_json has field 'ExitNodeStatus' and it is not None, then exit node is enabled
        if peers_json.get('ExitNodeStatus', None) is not None:
            return True
        return False

    def toggle_exit_node(self, toggled):
        print("Toggling exit node:", self.exit_node_enabled)
        self.exit_node_enabled = not self.exit_node_enabled
        if not self.exit_node_enabled:
            print("Disabling exit node")
            # Run sys command to disable exit node (tailscale set --exit-node="")
            sys_command = ["tailscale", "set", "--exit-node", ""]
            subprocess.run(sys_command)
        else:
            self.selected_exit_node = self.get_selected_exit_node()
            print("Enabling exit node: ", self.selected_exit_node)
            # Run sys command to enable exit node (tailscale set --exit-node=self.selected_exit_node)
            sys_command = ["tailscale", "set", "--exit-node", self.selected_exit_node]
            subprocess.run(sys_command)

    def get_selected_exit_node(self):
        print("Getting selected exit node")
        for menu_item in self.exit_nodes_menu.get_children():
            if menu_item.get_active():
                return menu_item.get_label()
        return None


    def select_exit_node(self, menu_item, exit_node):
        print("Select exit node:", exit_node)
        if menu_item.get_active():
            self.selected_exit_node = exit_node

    def is_tailscale_online(self):
        try:
            # Check if tailscale is online
            result = subprocess.run(["tailscale", "status"], stdout=subprocess.PIPE)
            if result.returncode == 0:
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def get_available_exit_nodes(self):
        # tailscale status --peers --json | jq '.Peer[] | select(.ExitNodeOption == true) | .HostName'
        try:
            result = subprocess.run(["tailscale", "status", "--peers", "--json"], stdout=subprocess.PIPE)
            if result.returncode == 0:
                peers_json = json.loads(result.stdout)
                exit_node_hosts = []
                for node_key, node_info in peers_json.get('Peer', {}).items():
                    if node_info.get('ExitNodeOption', False):
                        exit_node_hosts.append(node_info.get('HostName'))
                return exit_node_hosts
        except Exception as e:
            print(e)
            return []

    def update_icon(self):
        while True:
            # Get absolute to this script
            base_path = os.path.dirname(os.path.abspath(__file__))
            
            if self.is_tailscale_online():
                if self.exit_node_enabled:
                    icon_path = os.path.join(base_path, "tailscale-logo-green.png")
                else:
                    icon_path = os.path.join(base_path, "tailscale-logo-blue.png")
            else:
                icon_path = os.path.join(base_path, "tailscale-logo-red.png")

            GLib.idle_add(
                self.indicator.set_icon_full,
                icon_path,
                "Tailscale Status",
            )
            # Update available exit nodes
            self.available_exit_nodes = self.get_available_exit_nodes()
            
            # Update exit node menu state (checked/unchecked)
            for menu_item in self.menu.get_children():
                if menu_item.get_label() == "Enable Exit Node":
                    # Check if exit node enabled has been toggled externally (eg. through cli)
                    if self.exit_node_enabled != self.is_exit_node_enabled():
                        menu_item.set_active(not self.exit_node_enabled)
                    continue

            time.sleep(1)  # Update every 5 seconds

def main():
    print("Starting Tailscale Systray")

if __name__ == "__main__":
    tailscale_interface = TailscaleInterface()
