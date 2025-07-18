let satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '&copy; Esri, DigitalGlobe, GeoEye'
});

let map = L.map('map', {
    center: [53.3811, -1.4702
    ],
    zoom: 16,
    layers: [satellite]
})