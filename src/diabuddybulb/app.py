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
        
        # Language settings
        self.current_language = 'en'
        self.languages = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'eu': 'Euskara'
        }
        self.setup_translations()
        
        # Current status for icon
        self.current_status = "ready"
        
        # Color palette
        self.colors = {
            "cream": "#fff9eb",
            "dark_blue": "#00566e",
            "teal": "#00d1ca",
            "yellow": "#ffe08c",
            "green": "#00aa00",
            "orange": "#ffaa00",
            "red": "#ff4444"
        }
        
    def setup_translations(self):
        """Define translations for all languages"""
        self.translations = {
            'en': {
                # Buttons
                "start_monitoring": "Start Monitoring",
                "stop_monitoring": "Stop Monitoring",
                "check_now": "Check Now",
                "test_connections": "Test Connections",
                "save_settings": "Save Settings",
                "show_settings": "⚙️ Show Settings", 
                "hide_settings": "⬆️ Hide Settings",
                "help_button": "❓ Help",
                
                # Labels
                "settings_title": "Tapo Bulb Settings",
                "email_label": "Email:",
                "password_label": "Password:",
                "ip_label": "Bulb IP:",
                "language_label": "Language:",
                "glucose_status": "Glucose: {}",
                "direction_status": "Direction: {}",
                "alert_status": "Status: {}",
                
                # Status messages
                "bulb_connected": "💡 Bulb: Connected",
                "bulb_failed": "💡 Bulb: Connection Failed",
                "status_ready": "Ready",
                "status_monitoring": "Monitoring Active", 
                "status_stopped": "Monitoring Stopped",
                "status_testing": "Testing connections...",
                "status_checking": "Checking...",
                "status_check_failed": "Check Failed",
                
                # Alert levels
                "alert_critical_low": "🔴 CRITICAL LOW",
                "alert_low": "🟡 LOW",
                "alert_normal": "🟢 NORMAL", 
                "alert_high": "🟣 HIGH",
                
                # Alert dialogs
                "configure_first": "Configure Tapo settings first",
                "settings_saved": "Settings saved!",
                "monitoring_started": "Monitoring started",
                "monitoring_stopped": "Monitoring stopped",
                "connections_working": "✅ Connections working!",
                "check_complete": "Check complete: {}",
                "language_changed": "Language changed to {}",
                "start_monitoring_first": "Please start monitoring first",
                "could_not_get_glucose": "❌ Could not get glucose reading"
            },
            'es': {
                "start_monitoring": "Iniciar Monitoreo",
                "stop_monitoring": "Detener Monitoreo", 
                "check_now": "Comprobar Ahora",
                "test_connections": "Probar Conexiones",
                "save_settings": "Guardar Ajustes",
                "show_settings": "⚙️ Mostrar Ajustes", 
                "hide_settings": "⬆️ Ocultar Ajustes",
                "help_button": "❓ Ayuda",
                "settings_title": "Configuración Bombilla Tapo",
                "email_label": "Correo:",
                "password_label": "Contraseña:",
                "ip_label": "IP Bombilla:",
                "language_label": "Idioma:",
                "glucose_status": "Glucosa: {}",
                "direction_status": "Dirección: {}",
                "alert_status": "Estado: {}",
                "bulb_connected": "💡 Bombilla: Conectada",
                "bulb_failed": "💡 Bombilla: Conexión Fallida",
                "status_ready": "Listo",
                "status_monitoring": "Monitoreo Activo", 
                "status_stopped": "Monitoreo Detenido",
                "status_testing": "Probando conexiones...",
                "status_checking": "Comprobando...",
                "status_check_failed": "Comprobación Fallida",
                "alert_critical_low": "🔴 BAJA CRÍTICA",
                "alert_low": "🟡 BAJA",
                "alert_normal": "🟢 NORMAL", 
                "alert_high": "🟣 ALTA",
                "configure_first": "Configure primero los Ajustes",
                "settings_saved": "¡Ajustes guardados!",
                "monitoring_started": "Monitoreo iniciado",
                "monitoring_stopped": "Monitoreo detenido",
                "connections_working": "✅ ¡Conexiones funcionando!",
                "check_complete": "Comprobación completa: {}",
                "language_changed": "Idioma cambiado a {}",
                "start_monitoring_first": "Por favor inicie el monitoreo primero",
                "could_not_get_glucose": "❌ No se pudo obtener la lectura de glucosa"
            },
            'fr': {
                "start_monitoring": "Démarrer la Surveillance",
                "stop_monitoring": "Arrêter la Surveillance", 
                "check_now": "Vérifier Maintenant",
                "test_connections": "Tester les Connexions",
                "save_settings": "Enregistrer les Paramètres",
                "show_settings": "⚙️ Afficher les Paramètres", 
                "hide_settings": "⬆️ Masquer les Paramètres",
                "help_button": "❓ Aide",
                "settings_title": "Paramètres de l'Ampoule Tapo",
                "email_label": "Email:",
                "password_label": "Mot de passe:",
                "ip_label": "IP de l'Ampoule:",
                "language_label": "Langue:",
                "glucose_status": "Glucose: {}",
                "direction_status": "Direction: {}",
                "alert_status": "Statut: {}",
                "bulb_connected": "💡 Ampoule: Connectée",
                "bulb_failed": "💡 Ampoule: Échec de Connexion",
                "status_ready": "Prêt",
                "status_monitoring": "Surveillance Active", 
                "status_stopped": "Surveillance Arrêtée",
                "status_testing": "Test des connexions...",
                "status_checking": "Vérification...",
                "status_check_failed": "Échec de la Vérification",
                "alert_critical_low": "🔴 CRITIQUEMENT BAS",
                "alert_low": "🟡 BAS",
                "alert_normal": "🟢 NORMAL", 
                "alert_high": "🟣 ÉLEVÉ",
                "configure_first": "Configurez d'abord les paramètres Tapo",
                "settings_saved": "Paramètres enregistrés !",
                "monitoring_started": "Surveillance démarrée",
                "monitoring_stopped": "Surveillance arrêtée",
                "connections_working": "✅ Connexions fonctionnelles !",
                "check_complete": "Vérification terminée: {}",
                "language_changed": "Langue changée en {}",
                "start_monitoring_first": "Veuillez d'abord démarrer la surveillance",
                "could_not_get_glucose": "❌ Impossible d'obtenir la lecture de glucose"
            },
            'eu': {
                "start_monitoring": "Monitorizazioa hasi",
                "stop_monitoring": "Gelditu monitorizazioa",
                "check_now": "Egiaztatu orain",
                "test_connections": "Konexioak probatu",
                "save_settings": "Ezarpenak gorde",
                "show_settings": "⚙️Ezarpenak erakutsi",
                "hide_settings": "⬆️Ezarpenak ezkutatu",
                "help_button": "❓ Laguntza",
                "settings_title": "Tapo bonbillaren konfigurazioa",
                "email_label": "Posta:",
                "password_label": "Pasahitza:",
                "ip_label": "Bonbillaren IP:",
                "language_label": "Hizkuntza:",
                "glucose_status": "Glukosa: {}",
                "direction_status": "Norabidea: {}",
                "alert_status": "Egoera: {}",
                "bulb_connected": "💡 Bonbilla: konektatua",
                "bulb_failed": "💡 Bonbilla: konexio okerra",
                "status_ready": "Prest",
                "status_monitoring": "Monitorizazio aktiboa",
                "status_stopped": "Gelditutako monitorizazioa",
                "status_testing": "Konexioak probatzen...",
                "status_checking": "Egiaztatzen...",
                "status_check_failed": "Egiaztapenak huts egin du",
                "alert_critical_low": "🔴 KRITIKOKI BAXUA",
                "alert_low": "🟡 BAXUA",
                "alert_normal": "🟢 NORMALA",
                "alert_high": "🟣 ALTUA",
                "configure_first": "Konfigura itzazu lehendabizi ezarpenak",
                "settings_saved": "Gordetako ezarpenak!",
                "monitoring_started": "Monitorizazioa hasita",
                "monitoring_stopped": "Geldiarazitako monitorizazioa",
                "connections_working": "✅ Konexioak funtzionatzen!",
                "check_complete": "Egiaztapen osoa: {}",
                "language_changed": "Hizkuntza {} ra aldatu da",
                "start_monitoring_first": "Mesedez, hasi lehenengo monitorizazioa",
                "could_not_get_glucose": "❌ Ezin izan da glukosa-irakurketa lortu"

            }
        }
    
    def t(self, key, *args):
        """Simple translation helper"""
        translation = self.translations.get(self.current_language, self.translations['en'])
        text = translation.get(key, key)
        
        # Format with arguments if provided
        if args:
            try:
                return text.format(*args)
            except:
                return text
        return text
        
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
            self.t("glucose_status", "--"),
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
            self.t("direction_status", "--"),
            style=Pack(
                padding_bottom=15, 
                font_size=20, 
                text_align="center",
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        status_text = self.t("status_ready")
        if self.is_monitoring:
            status_text = self.t("status_monitoring")
            
        self.alert_status = toga.Label(
            self.t("alert_status", status_text),
            style=Pack(
                padding_bottom=10, 
                font_size=18, 
                text_align="center", 
                color=self.colors["dark_blue"],
                font_family="sans-serif"
            )
        )
        
        self.bulb_status = toga.Label(
            self.t("bulb_failed"),
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
        btn_text = self.t("stop_monitoring") if self.is_monitoring else self.t("start_monitoring")
        self.monitor_btn = toga.Button(
            btn_text,
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
            self.t("check_now"),
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
        settings_btn_text = self.t("hide_settings") if self.settings_visible else self.t("show_settings")
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
            self.t("help_button"),
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
            self.t("settings_title"),
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
            self.t("email_label"), 
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
            self.t("password_label"), 
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
            self.t("ip_label"), 
            style=Pack(width=80, color=self.colors["dark_blue"], font_family="sans-serif")
        ))
        self.ip_input = toga.TextInput(
            value=self.tapo_ip,
            placeholder="192.168.1.100",
            style=Pack(flex=1)
        )
        ip_box.add(self.ip_input)
    
        # Language selector - 2-column layout
        language_box = toga.Box(style=Pack(direction=COLUMN, padding_bottom=20))
        language_label = toga.Label(
            self.t("language_label"),
            style=Pack(padding_bottom=10, color=self.colors["dark_blue"], font_family="sans-serif")
        )
        language_box.add(language_label)
    
        # Create two columns for language buttons
        language_columns = toga.Box(style=Pack(direction=ROW))
    
        # Split languages into two columns
        languages_list = list(self.languages.items())
        mid_point = (len(languages_list) + 1) // 2  # +1 to handle odd numbers
    
        left_column = toga.Box(style=Pack(direction=COLUMN, flex=1, padding_right=5))
        right_column = toga.Box(style=Pack(direction=COLUMN, flex=1, padding_left=5))
    
        # Add buttons to left column
        for lang_code, lang_name in languages_list[:mid_point]:
            lang_btn = toga.Button(
                lang_name,
                on_press=self.select_language,
                style=Pack(
                    padding=10,
                    margin_bottom=5,
                    background_color=self.colors["teal"] if lang_code == self.current_language else self.colors["yellow"],
                    color=self.colors["dark_blue"],
                    font_family="sans-serif",
                    font_size=14
                )
            )
            lang_btn.language_code = lang_code
            left_column.add(lang_btn)
    
        # Add buttons to right column
        for lang_code, lang_name in languages_list[mid_point:]:
            lang_btn = toga.Button(
                lang_name,
                on_press=self.select_language,
                style=Pack(
                    padding=10,
                    margin_bottom=5,
                    background_color=self.colors["teal"] if lang_code == self.current_language else self.colors["yellow"],
                    color=self.colors["dark_blue"],
                    font_family="sans-serif",
                    font_size=14
                )
            )
            lang_btn.language_code = lang_code
            right_column.add(lang_btn)
    
        language_columns.add(left_column)
        language_columns.add(right_column)
        language_box.add(language_columns)
    
        # Test and Save buttons
        test_save_row = toga.Box(style=Pack(direction=ROW, padding_bottom=5))
        test_btn = toga.Button(
            self.t("test_connections"),
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
            self.t("save_settings"),
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
        settings_section.add(language_box)
        settings_section.add(test_save_row)
    
        # Add to main box
        self.main_box.add(settings_section)
        self.current_children.append(settings_section)

    def select_language(self, widget):
        """Select language from button group"""
        self.current_language = widget.language_code
        
        # Save settings
        self.save_settings_to_file()
        
        # Rebuild UI with new language
        self.build_ui()
        
        # Show confirmation
        lang_name = self.languages.get(self.current_language, self.current_language)
        self.show_alert(self.t("language_changed", lang_name))

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
                        self.current_language = settings.get('language', 'en')
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
                    'tapo_ip': self.tapo_ip,
                    'language': self.current_language
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
        about_text = self.get_about_text()
        self.main_window.info_dialog("📖 " + self.t("help_button").replace("❓ ", ""), about_text)
    
    def get_about_text(self):
        """Get about text in current language"""
        if self.current_language == 'es':
            return """
🌈 QUÉ HACE ESTA APP:
• Se conecta a xDrip+ para obtener lecturas de glucosa
• Cambia el color de tu bombilla Tapo según los niveles de glucosa
• Proporciona alertas visuales para niveles bajos y altos
• Se actualiza automáticamente cada 100 segundos

🚀 INSTRUCCIONES:

1. CONFIGURACIÓN BOMBILLA TAPO:
• Instala la bombilla Tapo L530E usando la app oficial de Tapo
• Encuentra la dirección IP de la bombilla en la app de Tapo (Info del Dispositivo)
• Introduce tu correo y contraseña de Tapo en esta app
• Guarda los ajustes

2. XDRIP+ SETUP:
• Abre la app xDrip+
• Ve a Configuración → Ajustes Inter-App
• Activa "Transmitir Datos Localmente"
• Asegúrate de que "Transmisión Local" esté activa

3. PRUEBA Y COMIENZA:
• Presiona "Probar Conexiones" para verificar que todo funciona
• Luego presiona "Iniciar Monitoreo" para comenzar la verificación automática
• Usa "Comprobar Ahora" para actualizaciones inmediatas durante el monitoreo

🎨 SIGNIFICADO DE COLORES:
🔴 ROJO: Críticamente Baja (<50) - ¡Emergencia!
🟡 AMARILLO: Baja (50-70) - ¡Necesita atención!
🟢 VERDE: Normal (70-180) - ¡Todo bien!
🟣 MORADO: Alta (>180) - ¡Necesita atención!

🔧 RESOLUCIÓN DE PROBLEMAS:

❌ ¿No se conecta a xDrip+?
• Asegúrate de que xDrip+ esté ejecutándose
• Verifica que "Transmitir Datos Localmente" esté activado en xDrip+
• Asegúrate de que el teléfono esté en la misma red WiFi

❌ ¿La bombilla no cambia de color?
• Verifica que el correo y contraseña de Tapo sean correctos
• Comprueba que la dirección IP de la bombilla sea correcta (desde la app de Tapo)
• Asegúrate de que la bombilla esté en línea en la app de Tapo
• Prueba el botón "Probar Conexiones"

❌ ¿La app deja de monitorear?
• Mantén la app abierta para un monitoreo continuo
• Android puede poner las apps en suspensión para ahorrar batería
• Enchufa el teléfono para el monitoreo nocturno

❌ ¿Las lecturas de glucosa no se actualizan?
• Verifica que xDrip+ tenga datos recientes del CGM
• Asegúrate de que el sensor esté activo y conectado
• Reinicia tanto xDrip+ como Diabuddy Bulb

Versión 0.0.1 - Hecho con ❤️ para familias con diabetes
"""
        elif self.current_language == 'fr':
            return """
🌈 CE QUE FAIT CETTE APPLICATION:
• Se connecte à xDrip+ pour obtenir les lectures de glucose
• Change la couleur de votre ampoule Tapo en fonction des niveaux de glucose
• Fournit des alertes visuelles pour les niveaux bas et élevés
• Se met à jour automatiquement toutes les 100 secondes

🚀 INSTRUCTIONS:

1. CONFIGURATION DE L'AMPOULE TAPO:
• Installez l'ampoule Tapo L530E en utilisant l'application officielle Tapo
• Trouvez l'adresse IP de l'ampoule dans l'application Tapo (Informations sur l'appareil)
• Entrez votre email et mot de passe Tapo dans cette application
• Enregistrez les paramètres

2. CONFIGURATION XDRIP+:
• Ouvrez l'application xDrip+
• Allez dans Paramètres → Paramètres Inter-App
• Activez "Diffuser les données localement"
• Assurez-vous que "Diffusion locale" est active

3. TESTEZ ET COMMENCEZ:
• Appuyez sur "Tester les connexions" pour vérifier que tout fonctionne
• Ensuite appuyez sur "Démarrer la surveillance" pour commencer la vérification automatique
• Utilisez "Vérifier maintenant" pour des mises à jour immédiates pendant la surveillance

🎨 SIGNIFICATION DES COULEURS:
🔴 ROUGE: Critique Bas (<50) - Urgence!
🟡 JAUNE: Bas (50-70) - Attention nécessaire!
🟢 VERT: Normal (70-180) - Tout va bien!
🟣 VIOLET: Élevé (>180) - Attention nécessaire!

🔧 DÉPANNAGE:

❌ Impossible de se connecter à xDrip+?
• Assurez-vous que xDrip+ fonctionne
• Vérifiez que "Diffuser les données localement" est activé dans xDrip+
• Assurez-vous que le téléphone est sur le même réseau WiFi

❌ L'ampoule ne change pas de couleur?
• Vérifiez que l'email et le mot de passe Tapo sont corrects
• Vérifiez que l'adresse IP de l'ampoule est correcte (depuis l'application Tapo)
• Assurez-vous que l'ampoule est en ligne dans l'application Tapo
• Essayez le bouton "Tester les connexions"

❌ L'application arrête la surveillance?
• Gardez l'application ouverte pour une surveillance continue
• Android peut mettre les applications en veille pour économiser la batterie
• Branchez le téléphone pour la surveillance nocturne

❌ Les lectures de glucose ne se mettent pas à jour?
• Vérifiez que xDrip+ a des données CGM récentes
• Assurez-vous que le capteur est actif et connecté
• Redémarrez à la fois xDrip+ et Diabuddy Bulb

Version 0.0.1 - Fait avec ❤️ pour les familles diabétiques
"""
        elif self.current_language == 'eu':
            return """
🌈 ZER EGITEN DU APP HONEK?
• xDrip+era konektatzen da glukosa-irakurketak lortzeko
• Zure Tapo bonbillaren kolorea aldatzen du glukosa mailen arabera
• Alerta bisualak ematen ditu maila baxu eta altuetarako
• Automatikoki eguneratzen da 100 segundotik behin

🚀 JARRAIBIDEAK:

1. BONBILLA TAPO KONFIGURAZIOA:
• Instalatu Tapo L530E bonbilla Taporen app ofiziala erabiliz
• Aurkitu bonbillaren IP helbidea Taporen app-an (Gailuaren Info)
• Sartu zure eposta eta Taporen pasahitza app honetan
• Gorde doikuntzak

2. XDRIP+ KONFIGURAZIOA:
• xDrip+ aplikazioa ireki 
• Joan Konfiguraziora → Inter-App doikuntzak
• "Datuak tokian-tokian transmititzea" aktiboa egon behar du
• Ziurtatu "Transmisio lokala" aktibo dagoela

3. PROBATU ETA HASI:
• Sakatu "Konexioak probatu" dena ondo dabilela egiaztatzeko
• Gero, sakatu "Monitorizazioa hasi" egiaztapen automatikoa hasteko
• Erabili "Egiaztatu orain" berehalako eguneratzeetarako monitoretzan

🎨 KOLOREEN ESANAHIA:
🔴 GORRIA: Kritikoki Baxua (< 50) - Larrialdia!
🟡 HORIA: Baxua (50-70) - Arreta behar da!
🟢 BERDEA: Normala (70-180) - Dena ondo!
🟣 MOREA: Altua (>180) - Arreta behar da!

🔧 ARAZOEN EBAZTEA: 

❌ Ez al da xDrip+era konektatzen?
• Ziurtatu xDrip+ exekutatzen ari dela
• "Datuak lokalean transmititzea" xDrip+en aktibatuta dagoela egiaztatu
• Ziurtatu telefonoa WiFi sare berean dagoela

❌ Bonbilla ez da kolorez aldatzen?
• Egiaztatu Taporen posta eta pasahitza zuzenak direla
• Egiaztatu bonbillaren IP helbidea zuzena dela (Taporen aplikaziotik)
• Ziurtatu bonbilla linean dagoela Taporen app-an
• "Probatu konexioak" botoia probatu

❌ App-ak monitorizatzeari uzten dio?
• Mantendu app-a irekita etengabeko monitorizaziorako
• Androidek app-ak esekita jar ditzake bateria aurrezteko
• Entxufatu telefonoa gaueko monitorizaziorako

❌ Glukosaren irakurketak ez dira eguneratzen?
• xDrip+ek CGMren datu berriak dituela egiaztatzen du
• Ziurtatu sentsorea aktibo eta konektatuta dagoela
• Berrabiarazi xDrip+ eta Diabuddy Bulb

0.0.1 Bertsioa ❤️rekin diabetesa duten familientzat egina
"""
        else:  # English default
            return """
🌈 WHAT THIS APP DOES:
• Connects to xDrip+ to get glucose readings
• Changes your Tapo bulb color based on glucose levels
• Provides visual alerts for lows and highs
• Updates automatically every 100 seconds

🚀 INSTRUCTIONS:

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
• Ensure phone is on same WiFi network

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

Version 0.0.1 - Made with ❤️ for diabetes families
"""
    
    def show_alert(self, message, is_error=False):
        """Show alert dialog"""
        title = "⚠️ Alert" if is_error else "💡 Info"
        self.main_window.info_dialog(title, message)
    
    def update_status(self, glucose_value, direction, alert_level=""):
        """Update the status display with arrows and icon"""
        self.glucose_status.text = self.t("glucose_status", glucose_value)
        
        # Convert direction to arrow
        arrow = self.get_direction_arrow(direction)
        self.direction_status.text = self.t("direction_status", arrow)
        
        if alert_level:
            alert_text = self.t(f"alert_{alert_level}")
            self.alert_status.text = self.t("alert_status", alert_text)
            
            # Update the icon based on status
            self.current_status = alert_level
            self.status_icon.image = self.get_icon_for_status(alert_level)
            
            if alert_level in ["critical", "low", "high"]:
                self.show_alert(f"Glucose Alert: {glucose_value} ({alert_text})", is_error=True)
    
    async def initialize_tapo(self, email=None, password=None, ip=None):
        """Initialize Tapo connection"""
        email = email or self.tapo_email
        password = password or self.tapo_password
        ip = ip or self.tapo_ip
        
        if not all([email, password, ip]):
            self.show_alert(self.t("configure_first"), is_error=True)
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
            self.bulb_status.text = self.t("bulb_connected")
            self.bulb_status.style.color = self.colors["green"]
            return True
            
        except Exception as e:
            self.bulb_status.text = self.t("bulb_failed")
            self.bulb_status.style.color = self.colors["red"]
            return False

    def test_connections(self, widget):
        """Test both connections with minimal dialogs and icon changes"""
        async def _test_connections():
            was_monitoring = False
            if self.is_monitoring:
                was_monitoring = True
                self.stop_monitoring()
                await asyncio.sleep(1)
            
            self.alert_status.text = self.t("alert_status", self.t("status_testing"))
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
                self.show_alert(self.t("connections_working"))
                self.alert_status.text = self.t("alert_status", self.t("status_ready"))
                self.alert_status.style.color = self.colors["green"]
            elif xdrip_ok and not tapo_ok:
                self.show_alert("❌ Partial connection\n\nxDrip+ is working but Tapo bulb failed to connect.", is_error=True)
                self.alert_status.text = self.t("alert_status", "xDrip+ Only")
                self.alert_status.style.color = self.colors["orange"]
            elif not xdrip_ok and tapo_ok:
                self.show_alert("❌ Partial connection\n\nTapo bulb is connected but xDrip+ failed.", is_error=True)
                self.alert_status.text = self.t("alert_status", "Tapo Only") 
                self.alert_status.style.color = self.colors["orange"]
            else:
                self.show_alert("❌ Connection failed\n\nBoth xDrip+ and Tapo bulb failed to connect.", is_error=True)
                self.alert_status.text = self.t("alert_status", "Connection Failed")
                self.alert_status.style.color = self.colors["red"]
                self.status_icon.image = self.get_icon_for_status("ready")
                self.current_status = "ready"
            
            if was_monitoring:
                self.alert_status.text += " - Restart"
        
        asyncio.create_task(_test_connections())
    
    def check_now(self, widget):
        """Manual check"""
        async def _check_now():
            if not self.is_monitoring:
                self.show_alert(self.t("start_monitoring_first"), is_error=True)
                return
                
            self.alert_status.text = self.t("alert_status", self.t("status_checking"))
            self.alert_status.style.color = self.colors["dark_blue"]
            
            glucose = await self.xdrip_client.get_latest_glucose()
            if glucose:
                alert_level = self.get_alert_level(glucose['value'])
                self.update_status(glucose['value'], glucose['direction'], alert_level)
                
                if all([self.tapo_email, self.tapo_password, self.tapo_ip]):
                    if await self.initialize_tapo():
                        await self.update_bulb_color(glucose['value'])
                        self.show_alert("✅ " + self.t("check_complete", glucose['value']))
                    else:
                        self.show_alert(f"Glucose: {glucose['value']} (Bulb not connected)")
                else:
                    self.show_alert(f"Glucose: {glucose['value']} (Configure bulb in Settings)")
            else:
                self.alert_status.text = self.t("alert_status", self.t("status_check_failed"))
                self.alert_status.style.color = self.colors["red"]
                self.show_alert(self.t("could_not_get_glucose"), is_error=True)
        
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
            
            self.alert_status.text = self.t("alert_status", "Settings Saved!")
            self.alert_status.style.color = self.colors["green"]
            self.show_alert("✅ " + self.t("settings_saved"))
            
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
            self.show_alert(self.t("configure_first"), is_error=True)
            return
            
        self.is_monitoring = True
        self.monitor_btn.text = self.t("stop_monitoring")
        self.alert_status.text = self.t("alert_status", self.t("status_monitoring"))
        self.alert_status.style.color = self.colors["green"]
        self.show_alert("🟢 " + self.t("monitoring_started"))
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.monitor_btn.text = self.t("start_monitoring")
        self.alert_status.text = self.t("alert_status", self.t("status_stopped")) 
        self.alert_status.style.color = self.colors["orange"]
        
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
