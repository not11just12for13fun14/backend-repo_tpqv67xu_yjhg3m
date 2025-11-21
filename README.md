TrenchSight - Field Photo Capture and 3D Prep

What’s included in this first stage
- Mobile-first capture screen for Android/iOS (PWA-friendly web app)
- Enter site name, select date, auto-capture GPS coordinates
- Session-based upload to backend with metadata
- Angle consistency assist with ±5° tolerance using device orientation
- Zoom mode toggle (0.5x / 1x where supported)
- Centering dashed guide for easier framing
- Photo counter and distance from starting point
- Battery and storage checks
- Filenames: {siteName}_{date}_{seq}_{lat}_{lng}.jpg
- Metadata saved in DB (GPS, tilt, heading, zoom, timestamp)
- Optional Google Drive upload (set GOOGLE_SERVICE_ACCOUNT_JSON + GOOGLE_DRIVE_FOLDER_ID)

Next steps
- Desktop processing tool to stitch series and export to AutoCAD-compatible 3D formats (e.g., DXF with EXIF parsing)
- Panorama assisted capture mode refinements
- Offline queue + background sync when signal is poor
