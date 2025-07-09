from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

TRACCAR_URL =  'https://map.gpstraccar.xyz' 

TRACCAR_USER = 'hassanzorkot204@gmail.com'
TRACCAR_PASS = 'hassan@2004'

@app.route('/map/<imei>')
def show_map(imei):
    try:
        # 1. Récupérer tous les devices
        devices_resp = requests.get(f'{TRACCAR_URL}/api/devices', auth=(TRACCAR_USER, TRACCAR_PASS))
        devices_resp.raise_for_status()
        devices = devices_resp.json()

        # 2. Trouver le device correspondant à l’IMEI
        device = next((d for d in devices if d['uniqueId'] == imei), None)
        if not device:
            return f"<h3>❌ Aucun appareil trouvé pour l'IMEI {imei}</h3>", 404

        device_id = device['id']
        device_name = device.get('name', 'Camion')

        # 3. Récupérer la dernière position
        positions_resp = requests.get(f'{TRACCAR_URL}/api/positions', auth=(TRACCAR_USER, TRACCAR_PASS))
        positions_resp.raise_for_status()
        positions = positions_resp.json()

        position = next((p for p in positions if p['deviceId'] == device_id), None)
        if not position:
            return f"<h3>❌ Aucune position trouvée pour le device ID {device_id}</h3>", 404

        lat = position['latitude']
        lon = position['longitude']

        # 4. Générer la page HTML avec Leaflet
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Carte - {device_name}</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <style>
                html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script>
                const map = L.map('map').setView([{lat}, {lon}], 15);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }}).addTo(map);

                const truckIcon = L.icon({{
                    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3097/3097144.png',
                    iconSize: [40, 40],
                    iconAnchor: [20, 20]
                }});

                const marker = L.marker([{lat}, {lon}], {{ icon: truckIcon }}).addTo(map)
                    .bindPopup("🚚 {device_name}").openPopup();
            </script>
        </body>
        </html>
        '''
        return html

    except Exception as e:
        return f"<h3>❌ Erreur : {str(e)}</h3>", 500

if __name__ == '__main__':
    app.run(debug=True)
