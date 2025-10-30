import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import asyncio
import aiohttp
import json
import os

class XDripClient:
    def __init__(self, base_urls=None):
        self.base_urls = base_urls or [
            "http://127.0.0.1:17580",
            "http://localhost:17580", 
            "http://10.0.2.2:17580",
        ]
    
    async def get_latest_glucose(self):
        """Get the latest glucose reading from xDrip+"""
        for base_url in self.base_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url}/sgv.json", timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and len(data) > 0:
                                latest = data[0]
                                return {
                                    'value': latest['sgv'],
                                    'direction': latest.get('direction', 'Unknown'),
                                    'timestamp': latest['date'],
                                    'date_string': latest['dateString'],
                                    'raw_data': latest
                                }
            except Exception:
                continue
        return None

class DiabuddyBulb(toga.App):
    def __init__(self):
        super().__init__()
        self.xdrip_client = XDripClient()
        self.tapo_device = None
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Settings with defaults
        self.tapo_email = ""
        self.tapo_password = ""
        self.tapo_ip = ""
        self.check_interval = 100
        
        # Settings state
        self.settings_visible = False
        
        # Current status for icon
        self.current_status = "ready"
        
        # Color palette
        self.colors = {
            "cream": "#fff9eb",
            "dark_blue": "#00566e",
            "teal": "#00d1ca",
            "yellow": "#ffe08c"
        }
        
    def startup(self):
        # Load settings first
        self.load_settings()
        
        # Create main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Create main scroll container for entire app
        self.main_scroll = toga.ScrollContainer(style=Pack(flex=1))
        
        # Create main box that goes inside scroll container
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=0, flex=1))
        
        # Build the initial UI (without settings)
        self.build_ui()
        
        # Set the scroll container content
        self.main_scroll.content = self.main_box
        
        # Set the main window content
        self.main_window.content = self.main_scroll
        self.main_window.show()

    def get_direction_arrow(self, direction):
        """Convert xDrip+ direction to arrow"""
        arrow_map = {
            "DoubleUp": "↑↑",
            "SingleUp": "↑",
            "FortyFiveUp": "↗",
            "Flat": "→",
            "FortyFiveDown": "↘",
            "SingleDown": "↓",
            "DoubleDown": "↓↓",
            "NONE": "→",
            "NOT COMPUTABLE": "?",
            "RATE OUT OF RANGE": "?"
        }
        return arrow_map.get(direction, "?")

    def get_icon_for_status(self, status):
        """Get the appropriate icon for current status"""
        icon_map = {
            "ready": "icon_ready.png",
            "critical": "icon_critical.png",
            "low": "icon_low.png", 
            "normal": "icon_normal.png",
            "high": "icon_high.png"
        }
        return icon_map.get(status, "icon_ready.png")

    def build_ui(self):
        """Build the UI - completely replace content"""
        # Clear the main box
        if hasattr(self, 'current_children'):
            for child in self.current_children:
                try:
                    self.main_box.remove(child)
                except:
                    pass
        
        self.current_children = []
        
        # Header with icon and title
        header_box = toga.Box(
            style=Pack(
                direction=COLUMN, 
                padding=20, 
                background_color=self.colors["dark_blue"],
                alignment="center"
            )
        )
        
        # Status icon
        self.status_icon = toga.ImageView(
            image=self.get_icon_for_status(self.current_status),
            style=Pack(width=80, height=80, padding_bottom=10)
        )
        
        # Title with cream color
        title_label = toga.Label(
            "Diabuddy Bulb",
            style=Pack(
                font_size=28, 
                font_weight="bold", 
                color=self.colors["cream"],
                text_align="center",
                font_family="sans-serif"
            )
        )
        
        header_box.add(self.status_icon)
        header_box.add(title_label)
        
        self.main_box.add(header_box)
        self.current_children.append(header_box)
        
        # Status Section
        status_box = toga.Box(
            style=Pack(
                direction=COLUMN, 
                padding=20, 
                background_color=self.colors["cream"]
            )
        )
        
        self.glucose_status = toga.Label(
            "Glucose: --",
            style=Pack(
                padding_bottom=10, 
                font_size=32, 
                font_weight="bold", 
                text_align="center",
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        self.direction_status = toga.Label(
            "Direction: --",
            style=Pack(
                padding_bottom=15, 
                font_size=20, 
                text_align="center",
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        self.alert_status = toga.Label(
            "Status: Ready",
            style=Pack(
                padding_bottom=10, 
                font_size=18, 
                text_align="center", 
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        self.bulb_status = toga.Label(
            "💡 Bulb: Not Connected",
            style=Pack(
                font_size=14, 
                text_align="center", 
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        status_box.add(self.glucose_status)
        status_box.add(self.direction_status)
        status_box.add(self.alert_status)
        status_box.add(self.bulb_status)
        
        self.main_box.add(status_box)
        self.current_children.append(status_box)
        
        # Control Buttons
        button_box = toga.Box(
            style=Pack(
                direction=COLUMN, 
                padding=20, 
                background_color=self.colors["dark_blue"]
            )
        )
        
        # Monitor and Check buttons
        monitor_row = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        self.monitor_btn = toga.Button(
            "Start Monitoring",
            on_press=self.toggle_monitoring,
            style=Pack(
                flex=1, 
                padding_right=5,
                background_color=self.colors["cream"],
                color=self.colors["dark_blue"],
                font_family="sans-serif",
                padding_top=10,
                padding_bottom=10
            )
        )
        check_btn = toga.Button(
            "Check Now",
            on_press=self.check_now,
            style=Pack(
                flex=1, 
                padding_left=5,
                background_color=self.colors["cream"],
                color=self.colors["dark_blue"],
                font_family="sans-serif",
                padding_top=10,
                padding_bottom=10
            )
        )
        monitor_row.add(self.monitor_btn)
        monitor_row.add(check_btn)
        
        # Settings button
        settings_row = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        settings_btn_text = "⬆️ Hide Settings" if self.settings_visible else "⚙️ Show Settings"
        self.settings_btn = toga.Button(
            settings_btn_text,
            on_press=self.toggle_settings,
            style=Pack(
                flex=1, 
                padding_right=5,
                background_color=self.colors["cream"],
                color=self.colors["dark_blue"],
                font_family="sans-serif",
                padding_top=10,
                padding_bottom=10
            )
        )
        help_btn = toga.Button(
            "❓ Help",
            on_press=self.show_about,
            style=Pack(
                flex=1, 
                padding_left=5,
                background_color=self.colors["cream"],
                color=self.colors["dark_blue"],
                font_family="sans-serif",
                padding_top=10,
                padding_bottom=10
            )
        )
        settings_row.add(self.settings_btn)
        settings_row.add(help_btn)
        
        button_box.add(monitor_row)
        button_box.add(settings_row)
        
        self.main_box.add(button_box)
        self.current_children.append(button_box)
        
        # Add settings section if visible
        if self.settings_visible:
            self.add_settings_section()

    def add_settings_section(self):
        """Add settings section to UI"""
        settings_section = toga.Box(
            style=Pack(
                direction=COLUMN, 
                padding=20, 
                background_color=self.colors["cream"]
            )
        )
        
        settings_title = toga.Label(
            "Tapo Bulb Settings",
            style=Pack(
                padding_bottom=15, 
                font_size=20, 
                font_weight="bold",
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        # Email
        email_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        email_box.add(toga.Label(
            "Email:", 
            style=Pack(width=80, color=self.colors["dark_blue"], font_family="sans-serif")
        ))
        self.email_input = toga.TextInput(
            value=self.tapo_email,
            placeholder="your@email.com",
            style=Pack(flex=1)
        )
        email_box.add(self.email_input)
        
        # Password
        password_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        password_box.add(toga.Label(
            "Password:", 
            style=Pack(width=80, color=self.colors["dark_blue"], font_family="sans-serif")
        ))
        self.password_input = toga.PasswordInput(
            value=self.tapo_password,
            placeholder="Tapo password",
            style=Pack(flex=1)
        )
        password_box.add(self.password_input)
        
        # IP Address
        ip_box = toga.Box(style=Pack(direction=ROW, padding_bottom=20))
        ip_box.add(toga.Label(
            "Bulb IP:", 
            style=Pack(width=80, color=self.colors["dark_blue"], font_family="sans-serif")
        ))
        self.ip_input = toga.TextInput(
            value=self.tapo_ip,
            placeholder="192.168.1.100",
            style=Pack(flex=1)
        )
        ip_box.add(self.ip_input)
        
        # Test and Save buttons
        test_save_row = toga.Box(style=Pack(direction=ROW, padding_bottom=5))
        test_btn = toga.Button(
            "Test Connections",
            on_press=self.test_connections,
            style=Pack(
                flex=1, 
                padding_right=5,
                background_color=self.colors["cream"],
                color=self.colors["dark_blue"],
                font_family="sans-serif",
                padding_top=10,
                padding_bottom=10
            )
        )
        save_btn = toga.Button(
            "Save Settings",
            on_press=self.save_settings,
            style=Pack(
                flex=1, 
                padding_left=5,
                background_color=self.colors["cream"],
                color=self.colors["dark_blue"],
                font_family="sans-serif",
                padding_top=10,
                padding_bottom=10
            )
        )
        test_save_row.add(test_btn)
        test_save_row.add(save_btn)
        
        # Add all to settings section
        settings_section.add(settings_title)
        settings_section.add(email_box)
        settings_section.add(password_box)
        settings_section.add(ip_box)
        settings_section.add(test_save_row)
        
        # Add to main box
        self.main_box.add(settings_section)
        self.current_children.append(settings_section)

    def load_settings(self):
        """Load settings from file"""
        try:
            if hasattr(self, 'app'):
                app_dir = self.app.paths.data
                settings_file = os.path.join(app_dir, 'diabuddy_settings.json')
                
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                        self.tapo_email = settings.get('tapo_email', '')
                        self.tapo_password = settings.get('tapo_password', '')
                        self.tapo_ip = settings.get('tapo_ip', '')
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings_to_file(self):
        """Save settings to file"""
        try:
            if hasattr(self, 'app'):
                app_dir = self.app.paths.data
                settings_file = os.path.join(app_dir, 'diabuddy_settings.json')
                
                settings = {
                    'tapo_email': self.tapo_email,
                    'tapo_password': self.tapo_password,
                    'tapo_ip': self.tapo_ip
                }
                
                os.makedirs(app_dir, exist_ok=True)
                
                with open(settings_file, 'w') as f:
                    json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings to file: {e}")

    def toggle_settings(self, widget):
        """Toggle settings section visibility"""
        self.settings_visible = not self.settings_visible
        self.build_ui()
    
    def show_about(self, widget):
        """Show instructions"""
        about_text = """

🌈 WHAT THIS APP DOES:
• Connects to xDrip+ to get glucose readings
• Changes your Tapo bulb color based on glucose levels
• Provides visual alerts for lows and highs
• Updates automatically every 100 seconds

🚀 SETUP INSTRUCTIONS:

1. TAPO BULB SETUP:
   • Install Tapo L530E bulb using the official Tapo app
   • Find the bulb's IP address in the Tapo app (Device Info)
   • Enter your Tapo email/password in this app
   • Save the settings

2. XDRIP+ SETUP:
   • Open xDrip+ app
   • Go to Settings → Inter-App Settings
   • Enable "Broadcast Data Locally"
   • Make sure "Local Broadcast" is active

3. TEST & START:
   • Press "Test Connections" to verify everything works
   • Then press "Start Monitoring" to begin automatic checking
   • Use "Check Now" for immediate updates while monitoring

🎨 COLOR MEANINGS:
🔴 RED: Critical Low (<50) - Emergency!
🟡 YELLOW: Low (50-70) - Needs attention
🟢 GREEN: Normal (70-180) - All good!
🟣 PURPLE: High (>180) - Needs attention

🔧 TROUBLESHOOTING:

❌ Can't connect to xDrip+?
   • Make sure xDrip+ is running
   • Check "Broadcast Data Locally" is enabled in xDrip+
   • Ensure phone is on same network

❌ Bulb not changing colors?
   • Verify Tapo email/password are correct
   • Check bulb IP address is correct (from Tapo app)
   • Ensure bulb is online in Tapo app
   • Try "Test Connections" button

❌ App stops monitoring?
   • Keep the app open for continuous monitoring
   • Android may put apps to sleep to save battery
   • Plug phone into power for overnight monitoring

❌ Glucose readings not updating?
   • Check xDrip+ has recent CGM data
   • Verify sensor is active and connected
   • Restart both xDrip+ and Diabuddy Bulb

💡 TIPS FOR PARENTS:
• Place bulb in a central location for easy visibility
• Use "Check Now" before bedtime for latest reading
• Keep phone plugged in overnight for continuous monitoring
• Test different bulb locations for best visibility

📞 NEED MORE HELP?
Contact support with any questions!

Version 1.0 - Made with ❤️ for diabetes families

"""
        self.main_window.info_dialog("📖 Instructions", about_text)
    
    def show_alert(self, message, is_error=False):
        """Show alert dialog"""
        title = "⚠️ Alert" if is_error else "💡 Info"
        self.main_window.info_dialog(title, message)
    
    def update_status(self, glucose_value, direction, alert_level=""):
        """Update the status display with arrows and icon"""
        self.glucose_status.text = f"Glucose: {glucose_value}"
        
        # Convert direction to arrow
        arrow = self.get_direction_arrow(direction)
        self.direction_status.text = f"Direction: {arrow}"
        
        if alert_level:
            colors = {
                "critical": ("🔴 CRITICAL LOW", "#ff4444"),
                "low": ("🟡 LOW", "#ffaa00"), 
                "normal": ("🟢 NORMAL", "#00aa00"),
                "high": ("🟣 HIGH", "#aa00aa")
            }
            text, color = colors.get(alert_level, ("", self.colors["dark_blue"]))
            self.alert_status.text = f"Status: {text}"
            self.alert_status.style.color = color
            
            # Update the icon based on status
            self.current_status = alert_level
            self.status_icon.image = self.get_icon_for_status(alert_level)
            
            if alert_level in ["critical", "low", "high"]:
                self.show_alert(f"Glucose Alert: {glucose_value} ({text})", is_error=True)
    
    async def initialize_tapo(self, email=None, password=None, ip=None):
        """Initialize Tapo connection"""
        email = email or self.tapo_email
        password = password or self.tapo_password
        ip = ip or self.tapo_ip
        
        if not all([email, password, ip]):
            self.show_alert("Please configure Tapo settings first", is_error=True)
            return False
            
        try:
            from plugp100.common.credentials import AuthCredential
            from plugp100.new.device_factory import connect, DeviceConnectConfiguration
            
            credentials = AuthCredential(email, password)
            device_configuration = DeviceConnectConfiguration(
                host=ip,
                credentials=credentials
            )
            
            self.tapo_device = await connect(device_configuration)
            await self.tapo_device.update()
            self.bulb_status.text = "💡 Bulb: Connected"
            self.bulb_status.style.color = "#00aa00"
            return True
            
        except Exception as e:
            self.bulb_status.text = "💡 Bulb: Connection Failed"
            self.bulb_status.style.color = "#ff4444"
            return False

    def test_connections(self, widget):
        """Test both connections with minimal dialogs and icon changes"""
        async def _test_connections():
            was_monitoring = False
            if self.is_monitoring:
                was_monitoring = True
                self.stop_monitoring()
                await asyncio.sleep(1)
            
            self.alert_status.text = "Status: Testing connections..."
            self.alert_status.style.color = self.colors["dark_blue"]
            
            # Test xDrip
            glucose = await self.xdrip_client.get_latest_glucose()
            xdrip_ok = glucose is not None
            
            if xdrip_ok:
                alert_level = self.get_alert_level(glucose['value'])
                self.update_status(glucose['value'], glucose['direction'], alert_level)
            
            # Test Tapo
            tapo_ok = await self.initialize_tapo()
            
            if tapo_ok:
                try:
                    # Turn on and cycle through colors with matching icon changes
                    await self.tapo_device.turn_on()
                    
                    # Color demo with icon changes
                    color_sequence = [
                        (0, 100, "critical"),    # Red - Critical
                        (60, 100, "low"),        # Yellow - Low
                        (120, 100, "normal"),    # Green - Normal
                        (270, 100, "high")       # Purple - High
                    ]
                    
                    for hue, saturation, status in color_sequence:
                        # Change both bulb color and app icon
                        await self.tapo_device.set_hue_saturation(hue, saturation)
                        self.status_icon.image = self.get_icon_for_status(status)
                        await asyncio.sleep(1.5)
                    
                    # Set back based on current glucose or default to normal
                    if xdrip_ok:
                        await self.update_bulb_color(glucose['value'])
                        self.current_status = self.get_alert_level(glucose['value'])
                        self.status_icon.image = self.get_icon_for_status(self.current_status)
                    else:
                        await self.tapo_device.set_hue_saturation(120, 100)
                        self.status_icon.image = self.get_icon_for_status("normal")
                        self.current_status = "normal"
                
                except Exception as e:
                    tapo_ok = False
                    self.status_icon.image = self.get_icon_for_status("ready")
                    self.current_status = "ready"
            
            # Show single result dialog
            if xdrip_ok and tapo_ok:
                self.show_alert("✅ Connections working!\n\nxDrip+ and Tapo bulb are both connected successfully.")
                self.alert_status.text = "Status: Connections Working"
                self.alert_status.style.color = "#00aa00"
            elif xdrip_ok and not tapo_ok:
                self.show_alert("❌ Partial connection\n\nxDrip+ is working but Tapo bulb failed to connect.", is_error=True)
                self.alert_status.text = "Status: xDrip+ Only"
                self.alert_status.style.color = "#ffaa00"
            elif not xdrip_ok and tapo_ok:
                self.show_alert("❌ Partial connection\n\nTapo bulb is connected but xDrip+ failed.", is_error=True)
                self.alert_status.text = "Status: Tapo Only" 
                self.alert_status.style.color = "#ffaa00"
            else:
                self.show_alert("❌ Connection failed\n\nBoth xDrip+ and Tapo bulb failed to connect.", is_error=True)
                self.alert_status.text = "Status: Connection Failed"
                self.alert_status.style.color = "#ff4444"
                self.status_icon.image = self.get_icon_for_status("ready")
                self.current_status = "ready"
            
            if was_monitoring:
                self.alert_status.text += " - Restart"
        
        asyncio.create_task(_test_connections())
    
    def check_now(self, widget):
        """Manual check"""
        async def _check_now():
            if not self.is_monitoring:
                self.show_alert("Please start monitoring first", is_error=True)
                return
                
            self.alert_status.text = "Status: Checking..."
            self.alert_status.style.color = self.colors["dark_blue"]
            
            glucose = await self.xdrip_client.get_latest_glucose()
            if glucose:
                alert_level = self.get_alert_level(glucose['value'])
                self.update_status(glucose['value'], glucose['direction'], alert_level)
                
                if all([self.tapo_email, self.tapo_password, self.tapo_ip]):
                    if await self.initialize_tapo():
                        await self.update_bulb_color(glucose['value'])
                        self.show_alert(f"✅ Check complete: {glucose['value']}")
                    else:
                        self.show_alert(f"Glucose: {glucose['value']} (Bulb not connected)")
                else:
                    self.show_alert(f"Glucose: {glucose['value']} (Configure bulb in Settings)")
            else:
                self.alert_status.text = "Status: Check Failed"
                self.alert_status.style.color = "#ff4444"
                self.show_alert("❌ Could not get glucose reading", is_error=True)
        
        asyncio.create_task(_check_now())
    
    def get_alert_level(self, glucose_value):
        """Determine alert level"""
        if glucose_value < 50:
            return "critical"
        elif glucose_value < 70:
            return "low"
        elif glucose_value <= 180:
            return "normal"
        else:
            return "high"
    
    def save_settings(self, widget):
        """Save settings"""
        try:
            self.tapo_email = self.email_input.value
            self.tapo_password = self.password_input.value
            self.tapo_ip = self.ip_input.value
            
            # Save to file
            self.save_settings_to_file()
            
            self.alert_status.text = "Status: Settings Saved!"
            self.alert_status.style.color = "#00aa00"
            self.show_alert("✅ Settings saved!")
            
        except Exception as e:
            self.show_alert(f"❌ Error saving: {str(e)}", is_error=True)
    
    def toggle_monitoring(self, widget):
        """Start/stop monitoring"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start monitoring"""
        if not all([self.tapo_email, self.tapo_password, self.tapo_ip]):
            self.show_alert("Configure Tapo settings first", is_error=True)
            return
            
        self.is_monitoring = True
        self.monitor_btn.text = "Stop Monitoring"
        self.alert_status.text = "Status: Monitoring Active"
        self.alert_status.style.color = "#00aa00"
        self.show_alert(f"🟢 Monitoring started - checking every {self.check_interval}s")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.monitor_btn.text = "Start Monitoring"
        self.alert_status.text = "Status: Monitoring Stopped" 
        self.alert_status.style.color = "#ffaa00"
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
    
    async def update_bulb_color(self, glucose_value):
        """Update bulb color"""
        if not self.tapo_device:
            return
            
        try:
            alert_level = self.get_alert_level(glucose_value)
            color_map = {
                "critical": (0, 100),
                "low": (60, 100),
                "normal": (120, 100),
                "high": (270, 100)
            }
            hue, saturation = color_map.get(alert_level, (120, 100))
            await self.tapo_device.turn_on()
            await self.tapo_device.set_hue_saturation(hue, saturation)
        except Exception as e:
            print(f"Error updating bulb: {e}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        last_glucose = None
        
        while self.is_monitoring:
            try:
                glucose = await self.xdrip_client.get_latest_glucose()
                
                if glucose:
                    alert_level = self.get_alert_level(glucose['value'])
                    self.update_status(glucose['value'], glucose['direction'], alert_level)
                    
                    if not last_glucose or abs(glucose['value'] - last_glucose['value']) > 2:
                        if await self.initialize_tapo():
                            await self.update_bulb_color(glucose['value'])
                        last_glucose = glucose
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(self.check_interval)

def main():
    return DiabuddyBulb()
