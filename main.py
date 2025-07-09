@app.route('/map_multi')
def show_multiple():
    imeis = request.args.get('imeis')
    if not imeis:
        return "<h3>❌ Aucun IMEI fourni</h3>", 400

    imei_list = imeis.split(',')

    try:
        # 1. Récupérer tous les devices et toutes les positions
        devices_resp = requests.get(f'{TRACCAR_URL}/api/devices', auth=(TRACCAR_USER, TRACCAR_PASS))
        positions_resp = requests.get(f'{TRACCAR_URL}/api/positions', auth=(TRACCAR_USER, TRACCAR_PASS))
        devices_resp.raise_for_status()
        positions_resp.raise_for_status()

        devices = devices_resp.json()
        positions = positions_resp.json()

        # 2. Trouver les devices correspondants
        markers = []
        for imei in imei_list:
            device = next((d for d in devices if d['uniqueId'] == imei.strip()), None)
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

        # 3. Générer HTML avec tous les marqueurs
        marker_js = "\n".join([
            f"""
            L.marker([{m['lat']}, {m['lon']}], {{ icon: truckIcon }}).addTo(map)
             .bindPopup("🚚 {m['name']}");
            """
            for m in markers
        ])

        center_lat, center_lon = markers[0]['lat'], markers[0]['lon']  # Point central

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Carte Multi Devices</title>
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
                const map = L.map('map').setView([{center_lat}, {center_lon}], 7);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }}).addTo(map);

                const truckIcon = L.icon({{
                    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3097/3097144.png',
                    iconSize: [40, 40],
                    iconAnchor: [20, 20]
                }});

                {marker_js}
            </script>
        </body>
        </html>
        '''
        return html

    except Exception as e:
        return f"<h3>❌ Erreur : {str(e)}</h3>", 500
