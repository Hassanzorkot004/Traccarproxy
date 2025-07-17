from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Config
TRACCAR_URL = 'https://map.gpstraccar.xyz'
TRACCAR_USER = 'hassanzorkot204@gmail.com'
TRACCAR_PASS = 'hassan@2004'

# 🟢 Route de test simple
@app.route('/')
def home():
    return "🚚 API Traccar GPS - Fonctionne ✅"

@app.route('/health')
def health():
    return jsonify({"status": "OK", "timestamp": "2025-07-17"})

@app.route('/test-traccar')
def test_traccar():
    try:
        response = requests.get(f'{TRACCAR_URL}/api/session', 
                              auth=(TRACCAR_USER, TRACCAR_PASS), 
                              timeout=10)
        return jsonify({
            "traccar_status": response.status_code,
            "traccar_url": TRACCAR_URL,
            "message": "Test connexion Traccar"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "traccar_url": TRACCAR_URL,
            "message": "Erreur connexion Traccar"
        })

# 🟢 Route 1 : Carte pour UN seul IMEI (avec gestion d'erreur améliorée)
@app.route('/map/<imei>')
def show_map(imei):
    try:
        print(f"Requête reçue pour IMEI: {imei}")
        
        # Récupération des devices
        devices_resp = requests.get(f'{TRACCAR_URL}/api/devices', 
                                   auth=(TRACCAR_USER, TRACCAR_PASS),
                                   timeout=30)
        devices_resp.raise_for_status()
        devices = devices_resp.json()
        
        device = next((d for d in devices if d['uniqueId'] == imei), None)
        if not device:
            return f"<h3>❌ Aucun appareil trouvé pour l'IMEI {imei}</h3>", 404

        device_id = device['id']
        device_name = device.get('name', 'Camion')
        
        # Récupération des positions
        positions_resp = requests.get(f'{TRACCAR_URL}/api/positions', 
                                     auth=(TRACCAR_USER, TRACCAR_PASS),
                                     timeout=30)
        positions_resp.raise_for_status()
        positions = positions_resp.json()
        
        position = next((p for p in positions if p['deviceId'] == device_id), None)
        if not position:
            return f"<h3>❌ Aucune position trouvée pour l'appareil {device_name}</h3>", 404

        lat = position['latitude']
        lon = position['longitude']
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Carte - {device_name}</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <style> html, body, #map {{ height: 100%; margin: 0; padding: 0; }} </style>
        </head>
        <body>
            <div id="map"></div>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script>
                const map = L.map('map').setView([{lat}, {lon}], 15);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19, attribution: '© OpenStreetMap'
                }}).addTo(map);
                const truckIcon = L.icon({{
                    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3097/3097144.png',
                    iconSize: [40, 40], iconAnchor: [20, 20]
                }});
                L.marker([{lat}, {lon}], {{ icon: truckIcon }}).addTo(map).bindPopup("🚚 {device_name}").openPopup();
            </script>
        </body>
        </html>
        '''
        return html
        
    except requests.exceptions.RequestException as e:
        return f"<h3>❌ Erreur de connexion Traccar: {str(e)}</h3>", 500
    except Exception as e:
        return f"<h3>❌ Erreur générale: {str(e)}</h3>", 500

# 🟢 Route 2 : Carte pour PLUSIEURS IMEI (avec gestion d'erreur améliorée)
@app.route('/map_multi')
def show_multiple():
    imeis = request.args.get('imeis')
    if not imeis:
        return "<h3>❌ Aucun IMEI fourni</h3>", 400

    imei_list = [imei.strip() for imei in imeis.split(',')]
    
    try:
        print(f"Requête reçue pour IMEIs: {imei_list}")
        
        # Récupération des données
        devices_resp = requests.get(f'{TRACCAR_URL}/api/devices', 
                                   auth=(TRACCAR_USER, TRACCAR_PASS),
                                   timeout=30)
        positions_resp = requests.get(f'{TRACCAR_URL}/api/positions', 
                                     auth=(TRACCAR_USER, TRACCAR_PASS),
                                     timeout=30)
        
        devices_resp.raise_for_status()
        positions_resp.raise_for_status()
        
        devices = devices_resp.json()
        positions = positions_resp.json()

        markers = []
        for imei in imei_list:
            device = next((d for d in devices if d['uniqueId'] == imei), None)
            if not device:
                continue
                
            device_id = device['id']
            device_name = device.get('name', f'Device {imei}')
            position = next((p for p in positions if p['deviceId'] == device_id), None)
            
            if position:
                markers.append({
                    'name': device_name,
                    'lat': position['latitude'],
                    'lon': position['longitude']
                })

        if not markers:
            return "<h3>❌ Aucun marqueur trouvé</h3>", 404

        center_lat, center_lon = markers[0]['lat'], markers[0]['lon']
        marker_js = "\n".join([
            f"""L.marker([{m['lat']}, {m['lon']}], {{ icon: truckIcon }}).addTo(map).bindPopup("🚚 {m['name']}");"""
            for m in markers
        ])

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Carte Multi-Commandes</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <style> html, body, #map {{ height: 100%; margin: 0; padding: 0; }} </style>
        </head>
        <body>
            <div id="map"></div>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script>
                const map = L.map('map').setView([{center_lat}, {center_lon}], 7);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19, attribution: '© OpenStreetMap'
                }}).addTo(map);
                const truckIcon = L.icon({{
                    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3097/3097144.png',
                    iconSize: [40, 40], iconAnchor: [20, 20]
                }});
                {marker_js}
            </script>
        </body>
        </html>
        '''
        return html
        
    except requests.exceptions.RequestException as e:
        return f"<h3>❌ Erreur de connexion Traccar: {str(e)}</h3>", 500
    except Exception as e:
        return f"<h3>❌ Erreur générale: {str(e)}</h3>", 500

# PAS de if __name__ == '__main__' pour éviter les conflits avec Gunicorn
