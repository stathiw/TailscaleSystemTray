import os
import time
import subprocess
import json
from threading import Thread
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator3, GLib

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
        self._updating_switch_menu = False
        self._syncing_exit_node = False
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.current_icon = None

        self.menu = Gtk.Menu()

        # Exit Node Enabled Toggle
        self.exit_node_toggle = Gtk.CheckMenuItem(label="Enable Exit Node")
        self.exit_node_toggle.set_active(self.exit_node_enabled)
        self.exit_node_toggle.connect("toggled", self.toggle_exit_node)
        self.menu.append(self.exit_node_toggle)

        # Available Exit Nodes Dropdown
        self.exit_nodes_menu = Gtk.Menu()
        self._build_exit_nodes_menu()
        exit_nodes_item = Gtk.MenuItem(label="Exit Nodes")
        exit_nodes_item.set_submenu(self.exit_nodes_menu)
        self.menu.append(exit_nodes_item)

        # Switch Account Dropdown
        self.profiles = self.get_profiles()
        self.switch_menu = Gtk.Menu()
        self._build_switch_menu()
        switch_item = Gtk.MenuItem(label="Switch Account")
        switch_item.set_submenu(self.switch_menu)
        self.menu.append(switch_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", Gtk.main_quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        thread = Thread(target=self.poll_state)
        thread.daemon = True
        thread.start()

        Gtk.main()

    # -- Tailscale queries --

    def is_exit_node_enabled(self):
        peers_json = json.loads(subprocess.run(["tailscale", "status", "--peers", "--json"], stdout=subprocess.PIPE).stdout)
        return peers_json.get('ExitNodeStatus', None) is not None

    def is_tailscale_online(self):
        try:
            result = subprocess.run(["tailscale", "status"], stdout=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            print(e)
            return False

    def get_available_exit_nodes(self):
        try:
            result = subprocess.run(["tailscale", "status", "--peers", "--json"], stdout=subprocess.PIPE)
            if result.returncode != 0:
                return []
            peers = json.loads(result.stdout).get('Peer', {}).values()
            return [p.get('DNSName', '').split('.')[0] for p in peers if p.get('ExitNodeOption')]
        except Exception as e:
            print(e)
            return []

    def get_profiles(self):
        try:
            result = subprocess.run(["tailscale", "switch", "--list", "--json"], stdout=subprocess.PIPE)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(e)
            return []

    # -- Menu builders (always run on main thread) --

    def _build_exit_nodes_menu(self):
        for child in self.exit_nodes_menu.get_children():
            self.exit_nodes_menu.remove(child)
        group = []
        for node in self.available_exit_nodes:
            menu_item = Gtk.RadioMenuItem.new_with_label(group, node)
            menu_item.set_active(False)
            group.append(menu_item)
            menu_item.connect("activate", self.select_exit_node, node)
            self.exit_nodes_menu.append(menu_item)
        self.exit_nodes_menu.show_all()

    def _build_switch_menu(self):
        self._updating_switch_menu = True
        for child in self.switch_menu.get_children():
            self.switch_menu.remove(child)
        group = []
        for profile in self.profiles:
            menu_item = Gtk.RadioMenuItem.new_with_label(group, profile["nickname"])
            menu_item.set_active(profile["selected"])
            group.append(menu_item)
            menu_item.connect("activate", self.switch_profile, profile["id"])
            self.switch_menu.append(menu_item)
        self.switch_menu.show_all()
        self._updating_switch_menu = False

    # -- Signal handlers --

    def toggle_exit_node(self, toggled):
        if self._syncing_exit_node:
            return
        self.exit_node_enabled = not self.exit_node_enabled
        if not self.exit_node_enabled:
            subprocess.run(["tailscale", "set", "--exit-node", ""])
        else:
            self.selected_exit_node = self.get_selected_exit_node()
            subprocess.run(["tailscale", "set", "--exit-node", self.selected_exit_node])

    def get_selected_exit_node(self):
        for menu_item in self.exit_nodes_menu.get_children():
            if menu_item.get_active():
                return menu_item.get_label()
        return None

    def select_exit_node(self, menu_item, exit_node):
        if menu_item.get_active():
            self.selected_exit_node = exit_node

    def switch_profile(self, menu_item, profile_id):
        if self._updating_switch_menu:
            return
        if menu_item.get_active():
            Thread(target=self._do_switch, args=(profile_id,), daemon=True).start()

    def _do_switch(self, profile_id):
        subprocess.run(["tailscale", "switch", profile_id])
        exit_nodes = self.get_available_exit_nodes()
        profiles = self.get_profiles()

        def apply():
            self.available_exit_nodes = exit_nodes
            self._build_exit_nodes_menu()
            if profiles:
                self.profiles = profiles
                self._build_switch_menu()

        GLib.idle_add(apply)

    def _sync_menu_item(self, menu_item, active, flag_name):
        setattr(self, flag_name, True)
        menu_item.set_active(active)
        setattr(self, flag_name, False)

    # -- Icon --

    def _set_icon(self, icon_path):
        if icon_path != self.current_icon:
            self.current_icon = icon_path
            self.indicator.set_icon_full(icon_path, "Tailscale Status")

    # -- Background polling (sync individual states, never rebuild menus) --

    def _get_icon_name(self):
        if not self.is_tailscale_online():
            return "tailscale-logo-red.png"
        if self.exit_node_enabled:
            return "tailscale-logo-green.png"
        return "tailscale-logo-blue.png"

    def poll_state(self):
        while True:
            GLib.idle_add(self._set_icon, os.path.join(self.base_path, self._get_icon_name()))

            exit_node_enabled = self.is_exit_node_enabled()
            if exit_node_enabled != self.exit_node_enabled:
                self.exit_node_enabled = exit_node_enabled
                GLib.idle_add(self._sync_menu_item, self.exit_node_toggle, exit_node_enabled, "_syncing_exit_node")

            updated_profiles = self.get_profiles()
            if not updated_profiles:
                time.sleep(1)
                continue

            menu_items_by_nickname = {m.get_label(): m for m in self.switch_menu.get_children()}
            for profile in updated_profiles:
                menu_item = menu_items_by_nickname.get(profile["nickname"])
                if menu_item and menu_item.get_active() != profile["selected"]:
                    GLib.idle_add(self._sync_menu_item, menu_item, profile["selected"], "_updating_switch_menu")

            time.sleep(1)

def main():
    print("Starting Tailscale Systray")

if __name__ == "__main__":
    tailscale_interface = TailscaleInterface()
