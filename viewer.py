import webview

# Change this to your app's URL
APP_URL = "https://enroll.professionaltraining.co.za"

window = webview.create_window(
    "Enrol Admin Portal",
    APP_URL,
    width=1280,
    height=900,
    resizable=True,
    confirm_close=True,
    text_select=True,
    zoomable=True
)

webview.start(debug=False)